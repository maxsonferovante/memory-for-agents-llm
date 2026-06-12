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


DEFAULT_INGEST_URL = "http://127.0.0.1:8081/v1/events"
PATH_KEYS = ("file_path", "filePath", "path", "target_path")
CONTENT_KEYS = ("content", "text", "body", "value")


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
            return bucket if bucket != "_proposals" else "spec"
        except Exception:
            return "repo"
    return "repo"


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


def build_event(
    payload: dict[str, object], source: str, event_type: str | None = None
) -> dict[str, object] | None:
    content = extract_content(payload)
    path_text = extract_path(payload)
    if not content and not path_text and not event_type:
        return None

    event_id_seed = content or path_text or event_type or utc_now()
    event_id = str(
        payload.get("id")
        or f"evt_{hashlib.sha256(event_id_seed.encode('utf-8')).hexdigest()[:16]}"
    )
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

    event = {
        "id": event_id,
        "event_type": str(
            event_type or payload.get("event_type") or infer_event_type(path_text, content)
        ),
        "repo": repo,
        "branch": branch or None,
        "commit_sha": commit or None,
        "file_path": path_text,
        "scope": str(payload.get("scope") or infer_scope(path_text)),
        "source": source,
        "session_id": session_id or None,
        "created_at": str(payload.get("created_at") or utc_now()),
        "content_hash": hashlib.sha256((content or "").encode("utf-8")).hexdigest()
        if content
        else hashlib.sha256((path_text or event_id).encode("utf-8")).hexdigest(),
        "content": content,
        "tool_name": payload.get("tool_name"),
    }
    return event


def post_event(url: str, event: dict[str, object]) -> None:
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
        raise SystemExit(f"failed to post memory event to {url}: {exc}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Post agent hook events to the local memory ingestion API.")
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = read_payload()
    event = build_event(payload, source=args.source, event_type=args.event_type)
    if event is None:
        print("memory event poster: nothing to post", file=sys.stderr)
        return 0
    post_event(args.url, event)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

