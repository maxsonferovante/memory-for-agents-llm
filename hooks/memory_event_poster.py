#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib import error as urllib_error
from urllib import request as urllib_request

DEFAULT_INGEST_URL = "http://127.0.0.1:8080/api/v1/events"
PATH_KEYS = ("file_path", "filePath", "path", "target_path")
CONTENT_KEYS = ("content", "text", "body", "value")
SESSION_ID_KEYS = ("session_id", "sessionId")
DOCUMENT_ID_KEYS = ("document_id", "documentId")
REVISION_ID_KEYS = ("revision_id", "revisionId")
PARENT_REVISION_ID_KEYS = ("parent_revision_id", "parentRevisionId")
OPERATION_KEYS = ("operation", "op")
CANONICAL_PATH_KEYS = ("canonical_path", "canonicalPath")
OFFICIAL_SPEC_KIT_FLOW = [
    "context_pack",
    "task_work",
    "memory_delta",
    "proposal",
    "promotion",
    "canonical_memory",
]
PROJECT_CONTEXT_FILES = (
    "AGENTS.md",
    "README.md",
    "QUICKSTART.md",
    "CODEX.md",
    "CLAUDE.md",
    "knowledge/README.md",
    "hooks/README.md",
    "local_stack/README.md",
    ".codex/README.md",
    ".claude/CLAUDE.md",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_payload() -> dict[str, object]:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def first_string(value: object, keys: tuple[str, ...]) -> str | None:
    if isinstance(value, dict):
        for key in keys:
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        for nested in value.values():
            found = first_string(nested, keys)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = first_string(item, keys)
            if found:
                return found
    return None


def repo_root() -> Path:
    top_level = git_output("rev-parse", "--show-toplevel")
    return Path(top_level) if top_level else Path.cwd()


def git_output(*args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except Exception:
        return None
    return completed.stdout.strip() or None


def detect_repo_name() -> str:
    return repo_root().name or "repo"


def detect_branch() -> str | None:
    return git_output("rev-parse", "--abbrev-ref", "HEAD")


def detect_commit() -> str | None:
    return git_output("rev-parse", "HEAD")


def extract_path(payload: dict[str, object]) -> str | None:
    return first_string(payload, PATH_KEYS)


def extract_content(payload: dict[str, object]) -> str | None:
    content = first_string(payload, CONTENT_KEYS)
    if content:
        return content
    path_text = extract_path(payload)
    if not path_text:
        return None
    file_path = Path(path_text)
    if file_path.exists() and file_path.is_file():
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception:
            return None
    return None


def extract_session_id(payload: dict[str, object]) -> str | None:
    return first_string(payload, SESSION_ID_KEYS)


def extract_document_id(payload: dict[str, object]) -> str | None:
    return first_string(payload, DOCUMENT_ID_KEYS)


def extract_revision_id(payload: dict[str, object]) -> str | None:
    return first_string(payload, REVISION_ID_KEYS)


def extract_parent_revision_id(payload: dict[str, object]) -> str | None:
    return first_string(payload, PARENT_REVISION_ID_KEYS)


def extract_operation(payload: dict[str, object]) -> str | None:
    return first_string(payload, OPERATION_KEYS)


def extract_canonical_path(payload: dict[str, object]) -> str | None:
    return first_string(payload, CANONICAL_PATH_KEYS)


def frontmatter_scalar(content: str | None, key: str) -> str | None:
    if not content:
        return None
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", content, re.S)
    if not match:
        return None
    raw_frontmatter = match.group(1)
    key_match = re.search(rf"^{re.escape(key)}:\s*(.+)$", raw_frontmatter, re.M)
    if not key_match:
        return None
    return key_match.group(1).strip().strip("\"'")


def infer_document_id(payload: dict[str, object], path_text: str | None, content: str | None) -> str:
    explicit = extract_document_id(payload)
    if explicit:
        return explicit
    for key in ("document_id", "id"):
        candidate = frontmatter_scalar(content, key)
        if candidate:
            return candidate
    seed = "|".join([detect_repo_name(), path_text or "unknown"])
    return f"doc_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]}"


def infer_canonical_path(payload: dict[str, object], path_text: str | None) -> str | None:
    explicit = extract_canonical_path(payload)
    if explicit:
        return explicit
    return path_text


def infer_operation(
    payload: dict[str, object], path_text: str | None, event_type: str, content: str | None
) -> str:
    explicit = extract_operation(payload)
    if explicit:
        return explicit
    if event_type == "memory_deleted":
        return "delete"
    if event_type == "canonical_sync":
        return "sync"
    if content:
        return "update"
    if path_text:
        return "touch"
    return "session_stop"


def infer_revision_id(
    payload: dict[str, object],
    document_id: str,
    content_hash: str,
    created_at: str,
    event_type: str,
) -> str:
    explicit = extract_revision_id(payload)
    if explicit:
        return explicit
    seed = "|".join([document_id, content_hash, created_at, event_type])
    return f"rev_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]}"


def infer_scope(path_text: str | None) -> str:
    if not path_text:
        return "repo"
    parts = Path(path_text).parts
    if "knowledge" in parts:
        try:
            idx = parts.index("knowledge")
            bucket = parts[idx + 1]
            if bucket == "_proposals":
                return "feature"
            if bucket == "products":
                return "product"
            if bucket == "org":
                return "org"
            if bucket == "repos":
                return "repo"
            if bucket == "specs":
                return "feature"
            return bucket
        except Exception:
            return "repo"
    return "repo"


def infer_artifact_kind(path_text: str | None) -> str:
    if not path_text:
        return "implementation"
    path = Path(path_text)
    name = path.name.lower()
    parts = tuple(part.lower() for part in path.parts)
    if "adr" in parts or name.startswith("adr"):
        return "adr"
    if "specs" in parts or "spec" in name:
        return "spec"
    if "tasks" in name:
        return "tasks"
    if "plan" in name:
        return "plan"
    if "checklist" in name:
        return "checklist"
    if "constitution" in name:
        return "constitution"
    if "analysis" in name or "analyze" in name:
        return "analysis"
    if "review" in name:
        return "review"
    if "memory" in name or "knowledge" in parts:
        return "memory"
    return "implementation" if path.suffix != ".md" else "spec"


def infer_spec_event_type(path_text: str | None, content: str | None) -> str:
    kind = infer_artifact_kind(path_text)
    text = (content or "").lower()
    path_exists = bool(path_text and Path(path_text).exists())
    if kind == "constitution":
        return "constitution.updated" if path_exists else "constitution.created"
    if kind == "spec":
        return "spec.updated" if path_exists else "spec.created"
    if kind == "plan":
        return "plan.created"
    if kind == "tasks":
        return "tasks.generated"
    if kind == "analysis":
        return (
            "inconsistency.detected" if "inconsisten" in text else "analysis.completed"
        )
    if kind == "adr":
        return "architecture.decision.created"
    if kind == "review":
        return "review.completed"
    if kind == "memory":
        if path_text and "_proposals" in Path(path_text).parts:
            return "memory.created" if "status: ready" not in text else "memory.updated"
        return "memory.consolidated"
    return "implementation.completed" if path_text else "implementation.started"


def infer_event_type(path_text: str | None, content: str | None) -> str:
    if path_text:
        parts = Path(path_text).parts
        if "knowledge" in parts:
            if "_proposals" in parts:
                if content and "status: ready" in content.lower():
                    return "proposal_ready"
                return "session_stop"
            return "memory_promoted"
        if path_text.endswith(".md"):
            return "repo_handoff"
    return "session_stop"


def scope_for_knowledge_path(path: Path) -> str:
    parts = path.parts
    if "knowledge" not in parts:
        return "repo"
    try:
        idx = parts.index("knowledge")
        bucket = parts[idx + 1]
    except Exception:
        return "repo"
    if bucket == "_proposals":
        return "spec"
    return bucket.rstrip("s") if bucket.endswith("s") else bucket


def git_lines(*args: str) -> list[str]:
    output = git_output(*args)
    if not output:
        return []
    return [line for line in output.splitlines() if line.strip()]


def session_key(payload: dict[str, object]) -> str:
    explicit = (
        extract_session_id(payload)
        or os.environ.get("CLAUDE_SESSION_ID")
        or os.environ.get("CODEX_SESSION_ID")
        or os.environ.get("SESSION_ID")
    )
    if explicit:
        return explicit
    return f"{detect_repo_name()}-{os.getppid()}"


def session_marker_path(payload: dict[str, object]) -> Path:
    key = hashlib.sha256(session_key(payload).encode("utf-8")).hexdigest()
    return Path(tempfile.gettempdir()) / "memory_hook_sessions" / f"{key}.json"


def read_project_context() -> str:
    root = repo_root()
    sections: list[str] = [
        "---",
        f"title: Session bootstrap context for {detect_repo_name()}",
        "---",
        "",
        f"# Session bootstrap context for {detect_repo_name()}",
        "",
        "## Purpose",
        "",
        "Snapshot the repo-level operating context that the agent should internalize at session start.",
        "",
    ]

    for relative_path in PROJECT_CONTEXT_FILES:
        path = root / relative_path
        if not path.exists() or not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8").strip()
        except Exception:
            continue
        sections.extend(
            [
                f"## {relative_path}",
                "",
                "```markdown",
                content,
                "```",
                "",
            ]
        )

    return "\n".join(sections).rstrip() + "\n"


def build_session_summary() -> str:
    changed = git_lines("status", "--short")
    staged_stat = git_output("diff", "--cached", "--stat") or "No staged changes."
    unstaged_stat = git_output("diff", "--stat") or "No unstaged changes."
    recent_commits = git_lines("log", "--oneline", "-5")

    lines = [
        "---",
        f"title: Session work summary for {detect_repo_name()}",
        "---",
        "",
        f"# Session work summary for {detect_repo_name()}",
        "",
        "## Working tree",
        "",
    ]

    if changed:
        lines.extend(f"- {line}" for line in changed)
    else:
        lines.append("- No working tree changes detected.")

    lines.extend(
        [
            "",
            "## Staged diff stat",
            "",
            "```text",
            staged_stat.strip(),
            "```",
            "",
            "## Unstaged diff stat",
            "",
            "```text",
            unstaged_stat.strip(),
            "```",
            "",
            "## Recent commits",
            "",
        ]
    )

    if recent_commits:
        lines.extend(f"- {line}" for line in recent_commits)
    else:
        lines.append("- No recent commits available.")

    return "\n".join(lines).rstrip() + "\n"


def canonical_knowledge_files() -> list[Path]:
    root = repo_root() / "knowledge"
    if not root.exists():
        return []
    files: list[Path] = []
    for path in sorted(root.rglob("*.md")):
        parts = path.parts
        if "_proposals" in parts:
            continue
        if "knowledge" not in parts:
            continue
        try:
            idx = parts.index("knowledge")
        except ValueError:
            continue
        if idx + 1 >= len(parts):
            continue
        if parts[idx + 1] == "README.md":
            continue
        files.append(path)
    return files


def build_event_from_values(
    *,
    source: str,
    event_type: str,
    file_path: str | None,
    content: str,
    scope: str | None = None,
    title: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "event_type": event_type,
        "file_path": file_path,
        "content": content,
        "scope": scope,
    }
    if title:
        payload["title"] = title
    event = build_event(payload, source=source, event_type=event_type)
    if event is None:
        raise ValueError("unable to build event")
    return event


def post_project_bootstrap(url: str, source: str, ignore_errors: bool) -> None:
    context_event = build_event_from_values(
        source=source,
        event_type="repo_handoff",
        file_path="README.md",
        content=read_project_context(),
        scope="repo",
        title=f"Session bootstrap context for {detect_repo_name()}",
    )
    post_event(url, context_event, ignore_errors=ignore_errors)


def post_canonical_sync(url: str, source: str, ignore_errors: bool) -> int:
    synced = 0
    root = repo_root()
    for path in canonical_knowledge_files():
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue
        event = build_event_from_values(
            source=source,
            event_type="canonical_sync",
            file_path=str(path.relative_to(root)),
            content=content,
            scope=scope_for_knowledge_path(path),
        )
        post_event(url, event, ignore_errors=ignore_errors)
        synced += 1
    return synced


def maybe_post_bootstrap(
    payload: dict[str, object],
    url: str,
    source: str,
    ignore_errors: bool,
    sync_canonical: bool,
) -> None:
    marker = session_marker_path(payload)
    if marker.exists():
        return
    marker.parent.mkdir(parents=True, exist_ok=True)
    post_project_bootstrap(url, source, ignore_errors)
    canonical_count = (
        post_canonical_sync(url, source, ignore_errors) if sync_canonical else 0
    )
    marker.write_text(
        json.dumps(
            {
                "session_key": session_key(payload),
                "created_at": utc_now(),
                "canonical_count": canonical_count,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def build_event(
    payload: dict[str, object], source: str, event_type: str | None = None
) -> dict[str, object] | None:
    content = extract_content(payload)
    path_text = extract_path(payload)
    resolved_event_type = str(
        event_type or payload.get("event_type") or infer_event_type(path_text, content)
    )
    if resolved_event_type == "session_stop" and not content and not path_text:
        content = build_session_summary()
    if not content and not path_text:
        return None

    repo = str(payload.get("repo") or detect_repo_name())
    branch = str(payload.get("branch") or detect_branch() or "")
    commit = str(payload.get("commit_sha") or detect_commit() or "")
    session_id = str(
        payload.get("session_id")
        or os.environ.get("CLAUDE_SESSION_ID")
        or os.environ.get("CODEX_SESSION_ID")
        or os.environ.get("SESSION_ID")
        or ""
    )
    created_at = str(payload.get("created_at") or utc_now())
    content_hash = (
        hashlib.sha256((content or "").encode("utf-8")).hexdigest()
        if content
        else hashlib.sha256((path_text or "").encode("utf-8")).hexdigest()
    )
    document_id = infer_document_id(payload, path_text, content)
    canonical_path = infer_canonical_path(payload, path_text)
    operation = infer_operation(payload, path_text, resolved_event_type, content)
    parent_revision_id = extract_parent_revision_id(payload)
    revision_id = infer_revision_id(
        payload, document_id, content_hash, created_at, resolved_event_type
    )
    event_id_seed = "|".join(
        [
            resolved_event_type,
            repo,
            branch,
            commit,
            path_text or "",
            document_id,
            revision_id,
            session_id,
            created_at,
            content_hash,
        ]
    )
    event_id = str(
        payload.get("id")
        or f"evt_{hashlib.sha256(event_id_seed.encode('utf-8')).hexdigest()[:16]}"
    )

    artifact_kind = infer_artifact_kind(path_text)
    event = {
        # Legacy fields consumed by the current local_stack API.
        "id": event_id,
        "event_id": event_id,
        "event_type": resolved_event_type,
        "schema_version": "1.0",
        "occurred_at": created_at,
        "repo": repo,
        "branch": branch or None,
        "commit_sha": commit or None,
        "file_path": path_text,
        "scope": str(payload.get("scope") or infer_scope(path_text)),
        "document_id": document_id,
        "revision_id": revision_id,
        "parent_revision_id": parent_revision_id,
        "operation": operation,
        "canonical_path": canonical_path,
        "source": source,
        "session_id": session_id or None,
        "created_at": created_at,
        "content_hash": content_hash,
        "content": content,
        "tool_name": payload.get("tool_name"),
        # Spec Memory Platform envelope fields.
        "producer": {
            "runtime": source.replace("-hook", ""),
            "adapter": "memory_event_poster",
            "version": "1.0",
        },
        "actor": {
            "type": "agent" if "hook" in source else "system",
            "id": source,
        },
        "artifact": {
            "kind": artifact_kind,
            "path": path_text,
            "uri": f"file://{path_text}" if path_text else None,
            "version": commit or content_hash,
            "document_id": document_id,
            "revision_id": revision_id,
            "parent_revision_id": parent_revision_id,
            "operation": operation,
            "canonical_path": canonical_path,
        },
        "correlation": {
            "session_id": session_id or None,
            "trace_id": payload.get("trace_id") or event_id,
            "parent_event_id": payload.get("parent_event_id"),
            "pull_request": payload.get("pull_request"),
            "commit": commit or None,
        },
        "payload": {
            "tool_name": payload.get("tool_name"),
            "official_flow": OFFICIAL_SPEC_KIT_FLOW,
            "raw_hook_payload": payload,
        },
        "provenance": {
            "source_url": payload.get("source_url"),
            "evidence": [
                value
                for value in (path_text, commit, payload.get("tool_name"))
                if value
            ],
            "document_id": document_id,
            "revision_id": revision_id,
            "parent_revision_id": parent_revision_id,
            "operation": operation,
            "canonical_path": canonical_path,
        },
    }
    return event


def post_event(url: str, event: dict[str, object], ignore_errors: bool = False) -> None:
    body = json.dumps(event, ensure_ascii=False).encode("utf-8")
    request = urllib_request.Request(
        url,
        data=body,
        method="POST",
        headers={"content-type": "application/json"},
    )
    try:
        with urllib_request.urlopen(request, timeout=10) as response:
            response.read()
    except urllib_error.URLError as exc:
        if ignore_errors:
            print(
                f"memory event poster: failed to post to {url}: {exc}", file=sys.stderr
            )
            return
        raise SystemExit(f"failed to post memory event to {url}: {exc}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Post agent hook events to the local memory ingestion API."
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("MEMORY_INGEST_API_URL", DEFAULT_INGEST_URL),
        help="Memory ingest API URL.",
    )
    parser.add_argument(
        "--source",
        default=os.environ.get("MEMORY_HOOK_SOURCE", "claude-code-hook"),
        help="Provenance source to write into the memory event.",
    )
    parser.add_argument(
        "--event-type",
        help="Override event_type for lifecycle hooks that do not include a file path.",
    )
    parser.add_argument(
        "--ignore-errors",
        action="store_true",
        help="Log ingestion failures without failing the hook command.",
    )
    parser.add_argument(
        "--bootstrap-once",
        action="store_true",
        help="Post a repo bootstrap context snapshot once per session.",
    )
    parser.add_argument(
        "--sync-canonical",
        action="store_true",
        help="When bootstrapping, also re-send canonical knowledge files to the ingest API.",
    )
    parser.add_argument(
        "--bootstrap-only",
        action="store_true",
        help="Run bootstrap logic without posting the current hook payload as a separate event.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = read_payload()
    if args.bootstrap_once:
        maybe_post_bootstrap(
            payload,
            url=args.url,
            source=args.source,
            ignore_errors=args.ignore_errors,
            sync_canonical=args.sync_canonical,
        )
        if args.bootstrap_only:
            return 0
    event = build_event(payload, source=args.source, event_type=args.event_type)
    if event is None:
        print("memory event poster: nothing to post", file=sys.stderr)
        return 0
    post_event(args.url, event, ignore_errors=args.ignore_errors)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
