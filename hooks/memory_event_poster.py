#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib import error as urllib_error
from urllib import request as urllib_request


DEFAULT_INGEST_URL = "http://127.0.0.1:8080/api/v1/events"
PATH_KEYS = ("file_path", "filePath", "path", "target_path")
CONTENT_KEYS = ("content", "text", "body", "value")
OFFICIAL_SPEC_KIT_FLOW = (
    "speckit.constitution",
    "speckit.specify",
    "speckit.clarify",
    "speckit.checklist",
    "speckit.plan",
    "speckit.tasks",
    "speckit.analyze",
    "speckit.implement",
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
    top_level = git_output("rev-parse", "--show-toplevel")
    if not top_level:
        return Path.cwd().name or "repo"
    return Path(top_level).name


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
        return "inconsistency.detected" if "inconsisten" in text else "analysis.completed"
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
    return infer_spec_event_type(path_text, content)


def build_event(
    payload: dict[str, object], source: str, event_type: str | None = None
) -> dict[str, object] | None:
    content = extract_content(payload)
    path_text = extract_path(payload)
    resolved_event_type = str(
        event_type or payload.get("event_type") or infer_event_type(path_text, content)
    )
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
    event_id_seed = "|".join(
        [
            resolved_event_type,
            repo,
            branch,
            commit,
            path_text or "",
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
            "evidence": [value for value in (path_text, commit, payload.get("tool_name")) if value],
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
            print(f"memory event poster: failed to post to {url}: {exc}", file=sys.stderr)
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = read_payload()
    event = build_event(payload, source=args.source, event_type=args.event_type)
    if event is None:
        print("memory event poster: nothing to post", file=sys.stderr)
        return 0
    post_event(args.url, event, ignore_errors=args.ignore_errors)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
