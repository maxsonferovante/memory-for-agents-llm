from __future__ import annotations

import json
import logging
import os
import time
import uuid
from contextlib import closing
from pathlib import Path

from local_stack.config import load_settings
from local_stack.markdown import (
    chunk_text,
    derive_sections,
    derive_title,
    estimate_tokens,
    first_sentence,
    hash_embedding,
    parse_frontmatter,
    render_excerpt,
)
from local_stack.storage import (
    claim_next_job,
    connect,
    export_index,
    initialize,
    mark_job_complete,
    mark_job_failed,
    replace_chunks,
    upsert_memory_item,
    utc_now,
)


settings = load_settings()
db = None
logging.basicConfig(
    level=getattr(logging, os.environ.get("MEMORY_LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("local_stack.worker")


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
    mapping = {
        "session_stop": "context_pack",
        "proposal_ready": "spec",
        "memory_promoted": "lesson",
        "repo_handoff": "context_pack",
    }
    return mapping.get(event_type, "lesson")


def _status_for(event: dict[str, object]) -> str:
    event_type = str(event.get("event_type") or "")
    return "canonical" if event_type == "memory_promoted" else "proposal"


def _provenance(event: dict[str, object]) -> dict[str, object]:
    return {
        "source": event.get("source") or "claude-code-hook",
        "session_id": event.get("session_id"),
        "event_type": event.get("event_type"),
        "branch": event.get("branch"),
        "created_at": event.get("created_at"),
        "file_path": event.get("file_path"),
    }


def _index_event(event: dict[str, object]) -> None:
    event_id = str(event.get("id") or "unknown")
    logger.info(
        "indexing event id=%s type=%s repo=%s scope=%s",
        event_id,
        str(event.get("event_type") or "unknown"),
        str(event.get("repo") or "unknown"),
        str(event.get("scope") or "repo"),
    )
    text = _event_text(event).strip()
    if not text:
        raise ValueError("event has no markdown content")

    frontmatter, body = parse_frontmatter(text)
    title = str(
        frontmatter.get("title")
        or event.get("title")
        or derive_title(body, Path(str(event.get("file_path") or "memory")).stem)
    )
    summary_source = body.strip() or text.strip()
    summary = render_excerpt(first_sentence(summary_source) or summary_source)
    repo = str(event.get("repo") or "unknown")
    scope = str(event.get("scope") or "repo")
    kind = _kind_for(event)
    source_file = str(event.get("file_path") or "")
    created_at = str(event.get("created_at") or utc_now())
    item_id = str(uuid.uuid4())
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
        "status": _status_for(event),
        "supersedes_id": None,
        "provenance": _provenance(event),
        "created_at": created_at,
        "updated_at": created_at,
    }
    upsert_memory_item(db, memory_item)

    sections = derive_sections(body if body.strip() else text)
    chunks_data: list[dict[str, object]] = []
    if sections:
        chunk_source = [
            (section.heading_path, section.content)
            for section in sections
            if section.content.strip()
        ]
    else:
        chunk_source = [("document", text)]

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

    if not chunks_data:
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
    logger.info(
        "indexed event id=%s into memory_item=%s chunks=%s title=%r",
        event_id,
        item_id,
        len(chunks_data),
        title,
    )
    export_index(db, settings.index_path)
    logger.info("exported derived index path=%s", settings.index_path)


def main() -> int:
    global db
    _bootstrap_database()
    db = connect(settings.db_path)
    logger.info(
        "local memory worker started db_path=%s index_path=%s poll_seconds=%s max_chunk_chars=%s",
        settings.db_path,
        settings.index_path,
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
            _index_event(job)
            mark_job_complete(db, str(job["id"]))
            export_index(db, settings.index_path)
            logger.info("processed event id=%s", job["id"])
        except Exception as exc:  # noqa: BLE001
            mark_job_failed(db, str(job["id"]), str(exc))
            export_index(db, settings.index_path)
            logger.exception("failed event id=%s", job["id"])


if __name__ == "__main__":
    raise SystemExit(main())
