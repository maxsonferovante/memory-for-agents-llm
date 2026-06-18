from __future__ import annotations

import json
import logging
import os
import time
import uuid
from hashlib import sha256
from contextlib import closing
from pathlib import Path

from local_stack.config import load_settings
from local_stack.markdown import (
    chunk_text,
    derive_sections,
    derive_structured_sections,
    derive_title,
    estimate_tokens,
    first_sentence,
    hash_embedding,
    parse_frontmatter,
    render_excerpt,
)
from local_stack.storage import (
    claim_next_job,
    clear_reconciliation_conflicts,
    connect,
    fetch_latest_document_revision,
    fetchall,
    initialize,
    mark_job_complete,
    mark_job_failed,
    replace_chunks,
    replace_document_sections,
    upsert_memory_item,
    upsert_consolidation_snapshot,
    upsert_document_revision,
    upsert_reconciliation_conflict,
    upsert_writeback_suggestion,
    utc_now,
)


settings = load_settings()
db = None
logging.basicConfig(
    level=getattr(logging, os.environ.get("MEMORY_LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("local_stack.worker")


def _stable_id(prefix: str, *parts: object) -> str:
    payload = "|".join("" if part is None else str(part) for part in parts)
    return f"{prefix}_{sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def _bootstrap_database() -> None:
    last_error: Exception | None = None
    logger.info("bootstrapping worker database connection")
    for attempt in range(1, 61):
        try:
            with closing(connect(settings.db_path)) as bootstrap_db:
                initialize(bootstrap_db)
            logger.info("worker database bootstrap complete")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            logger.warning("worker database not ready yet: attempt=%s error=%s", attempt, exc)
            time.sleep(1)
    raise SystemExit(f"database not ready: {last_error}")


def _event_text(event: dict[str, object]) -> str:
    content = event.get("content")
    if isinstance(content, str) and content.strip():
        return content
    raw_markdown_path = event.get("raw_markdown_path")
    if isinstance(raw_markdown_path, str) and raw_markdown_path:
        path = Path(raw_markdown_path)
        if path.exists():
            return path.read_text(encoding="utf-8")
    raw_payload_path = event.get("raw_payload_path")
    if isinstance(raw_payload_path, str) and raw_payload_path:
        try:
            payload = json.loads(Path(raw_payload_path).read_text(encoding="utf-8"))
        except Exception:
            return ""
        candidate = payload.get("content")
        if isinstance(candidate, str):
            return candidate
    return ""


def _kind_for(event: dict[str, object]) -> str:
    event_type = str(event.get("event_type") or "session_stop")
    source_file = str(event.get("file_path") or "")
    if source_file.startswith("knowledge/specs/"):
        return "spec"
    if source_file.startswith("knowledge/adr/"):
        return "adr"
    if source_file.startswith("knowledge/runbooks/"):
        return "runbook"
    if source_file.startswith("knowledge/glossary/"):
        return "glossary"
    mapping = {
        "session_stop": "context_pack",
        "proposal_ready": "spec",
        "memory_promoted": "lesson",
        "canonical_sync": "lesson",
        "repo_handoff": "context_pack",
    }
    return mapping.get(event_type, "lesson")


def _status_for(event: dict[str, object]) -> str:
    event_type = str(event.get("event_type") or "")
    return "canonical" if event_type in {"memory_promoted", "canonical_sync"} else "proposal"


def _provenance(event: dict[str, object]) -> dict[str, object]:
    return {
        "source": event.get("source") or "claude-code-hook",
        "session_id": event.get("session_id"),
        "event_type": event.get("event_type"),
        "branch": event.get("branch"),
        "created_at": event.get("created_at"),
        "file_path": event.get("file_path"),
        "document_id": event.get("document_id"),
        "revision_id": event.get("revision_id"),
        "parent_revision_id": event.get("parent_revision_id"),
        "operation": event.get("operation"),
        "canonical_path": event.get("canonical_path"),
    }


def _event_operation(event: dict[str, object]) -> str:
    operation = event.get("operation")
    if isinstance(operation, str) and operation.strip():
        return operation.strip()
    if str(event.get("event_type") or "") == "memory_deleted":
        return "delete"
    return "update"


def _event_document_id(
    event: dict[str, object], frontmatter: dict[str, object]
) -> str:
    explicit = event.get("document_id")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    for key in ("document_id", "id"):
        value = frontmatter.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return _stable_id("doc", event.get("repo"), event.get("file_path"))


def _event_canonical_path(event: dict[str, object]) -> str:
    explicit = event.get("canonical_path")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    file_path = event.get("file_path")
    if isinstance(file_path, str) and file_path.strip():
        return file_path.strip()
    return "memory/unknown.md"


def _event_revision_id(
    event: dict[str, object], document_id: str
) -> str:
    explicit = event.get("revision_id")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    return _stable_id(
        "rev",
        document_id,
        event.get("content_hash"),
        event.get("created_at"),
        event.get("event_type"),
    )


def _derive_consolidation_slug(scope: str, canonical_path: str, repo: str) -> tuple[str, str]:
    parts = Path(canonical_path).parts
    if "knowledge" in parts:
        index = parts.index("knowledge")
        if index + 2 < len(parts):
            bucket = parts[index + 1]
            remainder = parts[index + 2 :]
            if bucket in {"products", "domains", "specs", "integrations"} and remainder:
                return remainder[0], bucket.rstrip("s")
            if bucket == "repos":
                if len(remainder) > 1:
                    return remainder[0], "repo"
                return repo, "repo"
            if bucket in {"org", "adr", "incidents", "runbooks", "glossary"}:
                return "all", bucket.rstrip("s")
    return repo, scope


def _document_json(
    revision: dict[str, object],
    sections: list[dict[str, object]],
    *,
    conflict_state: str = "clear",
    writeback_available: bool = True,
) -> dict[str, object]:
    frontmatter = json.loads(str(revision.get("frontmatter_json") or "{}"))
    section_payload = []
    blocks: list[dict[str, object]] = []
    links: list[object] = []
    references: list[object] = []
    for section in sections:
        section_blocks = json.loads(str(section.get("blocks_json") or "[]"))
        section_links = json.loads(str(section.get("links_json") or "[]"))
        section_refs = json.loads(str(section.get("references_json") or "[]"))
        section_payload.append(
            {
                "section_index": section["section_index"],
                "level": section["level"],
                "heading": section.get("heading"),
                "heading_path": section["heading_path"],
                "raw_text": section["raw_text"],
                "blocks": section_blocks,
                "links": section_links,
                "references": section_refs,
            }
        )
        for block_index, block in enumerate(section_blocks):
            blocks.append(
                {
                    "section_index": section["section_index"],
                    "block_index": block_index,
                    **block,
                }
            )
        links.extend(section_links)
        references.extend(section_refs)
    return {
        "document_id": revision["document_id"],
        "revision_id": revision["id"],
        "parent_revision_id": revision.get("parent_revision_id"),
        "status": revision["status"],
        "canonical_path": revision["canonical_path"],
        "source_file": revision["source_file"],
        "operation": revision["operation"],
        "title": revision["title"],
        "frontmatter": frontmatter,
        "raw_text": revision["raw_text"],
        "body_text": revision["body_text"],
        "sections": section_payload,
        "blocks": blocks,
        "links": links,
        "references": references,
        "provenance": json.loads(str(revision["provenance_json"])),
        "conflict_state": conflict_state,
        "writeback_available": writeback_available,
    }


def _refresh_consolidation_snapshot(
    repo: str, scope: str, canonical_path: str, created_at: str
) -> None:
    slug, title_scope = _derive_consolidation_slug(scope, canonical_path, repo)
    repo_key = repo if scope == "repo" else ""
    revisions = fetchall(
        db,
        """
        SELECT *
        FROM document_revisions
        WHERE scope = %s AND repo = %s AND status = 'active' AND is_deleted = FALSE
        ORDER BY canonical_path ASC, created_at ASC
        """,
        (scope, repo),
    )
    filtered = [
        revision
        for revision in revisions
        if _derive_consolidation_slug(scope, str(revision["canonical_path"]), repo)[0] == slug
    ]
    documents = []
    for revision in filtered:
        section_rows = fetchall(
            db,
            """
            SELECT *
            FROM document_sections
            WHERE revision_id = %s
            ORDER BY section_index ASC
            """,
            (revision["id"],),
        )
        documents.append(_document_json(revision, section_rows))

    snapshot = {
        "scope": scope,
        "repo": repo,
        "slug": slug,
        "title": f"{title_scope}:{slug}",
        "generated_at": created_at,
        "document_count": len(documents),
        "documents": documents,
    }
    upsert_consolidation_snapshot(
        db,
        {
            "id": _stable_id("cons", scope, repo_key, slug, created_at, len(documents)),
            "scope": scope,
            "repo": repo_key,
            "slug": slug,
            "title": f"{title_scope}:{slug}",
            "document_ids": [document["document_id"] for document in documents],
            "snapshot": snapshot,
            "content_hash": sha256(
                json.dumps(snapshot, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest(),
            "created_at": created_at,
            "updated_at": created_at,
        },
    )


def _index_event(event: dict[str, object]) -> bool:
    event_id = str(event.get("id") or "unknown")
    logger.info(
        "indexing event id=%s type=%s repo=%s scope=%s",
        event_id,
        str(event.get("event_type") or "unknown"),
        str(event.get("repo") or "unknown"),
        str(event.get("scope") or "repo"),
    )
    raw_event_text = _event_text(event)
    text = raw_event_text.strip()
    operation = _event_operation(event)
    if not text and operation != "delete":
        logger.info("skipping event id=%s because it has no markdown content", event_id)
        return False

    frontmatter, body = parse_frontmatter(text)
    document_id = _event_document_id(event, frontmatter)
    revision_id = _event_revision_id(event, document_id)
    previous_revision = fetch_latest_document_revision(db, document_id)
    parent_revision_id = event.get("parent_revision_id") or (
        previous_revision.get("id") if previous_revision else None
    )
    canonical_path = _event_canonical_path(event)
    title = str(
        frontmatter.get("title")
        or event.get("title")
        or derive_title(body, Path(str(event.get("file_path") or "memory")).stem)
    )
    summary_source = body.strip() or text.strip() or canonical_path
    summary = render_excerpt(first_sentence(summary_source) or summary_source)
    repo = str(event.get("repo") or "unknown")
    scope = str(event.get("scope") or "repo")
    kind = _kind_for(event)
    source_file = str(event.get("file_path") or "")
    created_at = str(event.get("created_at") or utc_now())
    item_id = str(uuid.uuid4())
    structured_sections = derive_structured_sections(body if body.strip() else text)
    document_links = []
    document_references = []
    for section in structured_sections:
        document_links.extend(section.links)
        document_references.extend(section.references)

    conflict_required = (
        previous_revision is not None
        and event.get("parent_revision_id") is not None
        and str(event.get("parent_revision_id")) != str(previous_revision.get("id"))
        and str(previous_revision.get("content_hash")) != str(event.get("content_hash"))
    )
    if conflict_required:
        upsert_reconciliation_conflict(
            db,
            {
                "id": _stable_id("conflict", document_id, revision_id),
                "document_id": document_id,
                "repo": repo,
                "canonical_path": canonical_path,
                "database_revision_id": previous_revision.get("id"),
                "repo_content_hash": event.get("content_hash"),
                "status": "open",
                "details": {
                    "reason": "parent_revision_mismatch",
                    "expected_parent_revision_id": previous_revision.get("id"),
                    "received_parent_revision_id": event.get("parent_revision_id"),
                },
                "created_at": created_at,
                "updated_at": created_at,
            },
        )
        conflict_state = "conflict"
    else:
        clear_reconciliation_conflicts(db, document_id)
        conflict_state = "clear"

    revision_record = {
        "id": revision_id,
        "document_id": document_id,
        "event_id": event["id"],
        "repo": repo,
        "scope": scope,
        "canonical_path": canonical_path,
        "source_file": source_file or canonical_path,
        "operation": operation,
        "parent_revision_id": parent_revision_id,
        "title": title,
        "content_hash": event["content_hash"],
        "frontmatter": frontmatter,
        "raw_text": text,
        "body_text": body.strip() if body.strip() else text,
        "links": document_links,
        "references": document_references,
        "provenance": _provenance(event),
        "status": "deleted" if operation == "delete" else "active",
        "is_deleted": operation == "delete",
        "created_at": created_at,
        "updated_at": created_at,
    }
    upsert_document_revision(db, revision_record)

    section_records = []
    for section in structured_sections:
        section_records.append(
            {
                "id": _stable_id("sec", revision_id, section.section_index),
                "document_id": document_id,
                "section_index": section.section_index,
                "level": section.level,
                "heading": section.heading,
                "heading_path": section.heading_path,
                "raw_text": section.raw_text,
                "blocks": [
                    {
                        "block_type": block.block_type,
                        "raw_text": block.raw_text,
                    }
                    for block in section.blocks
                ],
                "links": section.links,
                "references": section.references,
                "created_at": created_at,
            }
        )
    replace_document_sections(db, revision_id, section_records)

    memory_item = {
        "id": item_id,
        "event_id": event["id"],
        "repo": repo,
        "scope": scope,
        "kind": kind,
        "title": title,
        "summary": summary,
        "source_file": source_file,
        "commit_sha": event.get("commit_sha"),
        "content_hash": event["content_hash"],
        "status": "deleted" if operation == "delete" else _status_for(event),
        "supersedes_id": None,
        "provenance": {
            **_provenance(event),
            "document_id": document_id,
            "revision_id": revision_id,
            "parent_revision_id": parent_revision_id,
            "canonical_path": canonical_path,
            "conflict_state": conflict_state,
        },
        "created_at": created_at,
        "updated_at": created_at,
    }
    upsert_memory_item(db, memory_item)

    sections = derive_sections(body if body.strip() else text)
    chunks_data: list[dict[str, object]] = []
    if operation != "delete" and sections:
        chunk_source = [
            (section.heading_path, section.content)
            for section in sections
            if section.content.strip()
        ]
    elif operation != "delete":
        chunk_source = [("document", text)]
    else:
        chunk_source = []

    for index, (heading_path, chunk_source_text) in enumerate(chunk_source):
        chunk_candidates = chunk_text(chunk_source_text, settings.max_chunk_chars)
        for sub_index, chunk in enumerate(chunk_candidates):
            combined_index = index * 100 + sub_index
            chunks_data.append(
                {
                    "id": str(uuid.uuid4()),
                    "repo": repo,
                    "scope": scope,
                    "kind": kind,
                    "heading_path": heading_path,
                    "chunk_index": combined_index,
                    "chunk_text": chunk,
                    "embedding": hash_embedding(chunk),
                    "token_count": estimate_tokens(chunk),
                    "source_file": source_file,
                    "provenance": _provenance(event),
                    "created_at": created_at,
                }
            )

    if operation != "delete" and not chunks_data:
        chunks_data.append(
            {
                "id": str(uuid.uuid4()),
                "repo": repo,
                "scope": scope,
                "kind": kind,
                "heading_path": "document",
                "chunk_index": 0,
                "chunk_text": text,
                "embedding": hash_embedding(text),
                "token_count": estimate_tokens(text),
                "source_file": source_file,
                "provenance": _provenance(event),
                "created_at": created_at,
            }
        )

    replace_chunks(db, item_id, chunks_data)
    document_json = _document_json(
        {
            **revision_record,
            "provenance_json": json.dumps(revision_record["provenance"], ensure_ascii=False),
        },
        [
            {
                "section_index": section["section_index"],
                "level": section["level"],
                "heading": section.get("heading"),
                "heading_path": section["heading_path"],
                "raw_text": section["raw_text"],
                "blocks_json": json.dumps(section["blocks"], ensure_ascii=False),
                "links_json": json.dumps(section["links"], ensure_ascii=False),
                "references_json": json.dumps(section["references"], ensure_ascii=False),
            }
            for section in section_records
        ],
        conflict_state=conflict_state,
        writeback_available=operation != "delete",
    )
    if operation != "delete":
        upsert_writeback_suggestion(
            db,
            {
                "id": _stable_id("writeback", document_id, revision_id, canonical_path),
                "document_id": document_id,
                "target_path": canonical_path,
                "based_on_revision_id": revision_id,
                "suggestion": {
                    "document": document_json,
                    "verification": {
                        "method": "rule-based",
                        "passed": conflict_state == "clear",
                        "checks": [
                            "document revision indexed",
                            "no active reconciliation conflict",
                        ],
                    },
                    "action": "suggest_apply_to_repo",
                },
                "status": "ready" if conflict_state == "clear" else "blocked",
                "created_at": created_at,
                "updated_at": created_at,
            },
        )
    _refresh_consolidation_snapshot(repo, scope, canonical_path, created_at)
    logger.info(
        "indexed event id=%s into memory_item=%s chunks=%s title=%r",
        event_id,
        item_id,
        len(chunks_data),
        title,
    )
    return True


def main() -> int:
    global db
    _bootstrap_database()
    db = connect(settings.db_path)
    logger.info(
        "local memory worker started db_path=%s poll_seconds=%s max_chunk_chars=%s",
        settings.db_path,
        settings.worker_poll_seconds,
        settings.max_chunk_chars,
    )
    while True:
        job = claim_next_job(db)
        if job is None:
            logger.debug("no pending job available")
            time.sleep(settings.worker_poll_seconds)
            continue
        try:
            indexed = _index_event(job)
            mark_job_complete(db, str(job["id"]))
            if not indexed:
                logger.info("processed event id=%s without derived memory output", job["id"])
            else:
                logger.info("processed event id=%s", job["id"])
        except Exception as exc:  # noqa: BLE001
            mark_job_failed(db, str(job["id"]), str(exc))
            logger.exception("failed event id=%s", job["id"])


if __name__ == "__main__":
    raise SystemExit(main())
