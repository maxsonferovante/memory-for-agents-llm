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

DEFAULT_URL = "http://127.0.0.1:8080/api/v1/events"
PROMPT_KEYS = ("prompt", "userPrompt", "message", "text")
PATH_KEYS = ("filePath", "file_path", "path", "target_path")
SESSION_KEYS = ("sessionId", "session_id")


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
    output = completed.stdout.strip()
    return output or None


def repo_root() -> Path:
    return Path(git_output("rev-parse", "--show-toplevel") or Path.cwd())


def relative_path(path_text: str | None) -> str | None:
    if not path_text:
        return None
    path = Path(path_text)
    try:
        return str(path.resolve().relative_to(repo_root()))
    except Exception:
        try:
            return str(path.relative_to(Path.cwd()))
        except Exception:
            return path_text


def detect_repo() -> str:
    return os.environ.get("GITHUB_REPOSITORY") or repo_root().name or "unknown"


def detect_branch() -> str | None:
    return os.environ.get("GITHUB_REF_NAME") or git_output("rev-parse", "--abbrev-ref", "HEAD")


def detect_commit() -> str | None:
    return os.environ.get("GITHUB_SHA") or git_output("rev-parse", "HEAD")


def detect_session(payload: dict[str, object]) -> str:
    return (
        first_string(payload, SESSION_KEYS)
        or os.environ.get("GITHUB_RUN_ID")
        or os.environ.get("COPILOT_SESSION_ID")
        or f"{detect_repo()}-{os.getppid()}"
    )


def extract_prompt(payload: dict[str, object]) -> str | None:
    return os.environ.get("COPILOT_AGENT_PROMPT") or first_string(payload, PROMPT_KEYS)


def extract_path(payload: dict[str, object]) -> str | None:
    return first_string(payload, PATH_KEYS)


def detect_spec_path() -> str | None:
    candidates = git_lines("ls-files", "knowledge/specs")
    if not candidates:
        return None
    return candidates[0]


def git_lines(*args: str) -> list[str]:
    output = git_output(*args)
    if not output:
        return []
    return [line for line in output.splitlines() if line.strip()]


def changed_files() -> list[str]:
    return git_lines("status", "--short")


def infer_artifact_kind(path_text: str | None, phase: str) -> str:
    if phase == "sessionStart":
        return "implementation"
    if phase in {"sessionEnd", "agentStop"}:
        return "memory"
    if not path_text:
        return "implementation"
    name = Path(path_text).name.lower()
    parts = tuple(part.lower() for part in Path(path_text).parts)
    if "knowledge" in parts:
        return "memory"
    if "adr" in parts or name.startswith("adr"):
        return "adr"
    if "spec" in name:
        return "spec"
    if "plan" in name:
        return "plan"
    if "task" in name:
        return "tasks"
    if "review" in name:
        return "review"
    if "analysis" in name:
        return "analysis"
    return "implementation"


def infer_event_type(phase: str, payload: dict[str, object], path_text: str | None) -> str:
    if phase == "sessionStart":
        return "implementation.started"
    if phase in {"sessionEnd", "agentStop"}:
        return "lesson.learned"

    tool_name = str(payload.get("toolName") or payload.get("tool_name") or "").lower()
    rel_path = (path_text or "").lower()
    if "review" in tool_name or "review" in rel_path:
        return "review.completed"
    if any(token in tool_name for token in ("test", "build", "lint", "check")):
        return "analysis.completed"
    if "knowledge/_proposals" in rel_path:
        return "memory.created"
    if "knowledge/" in rel_path:
        return "memory.updated"
    if "adr" in rel_path:
        return "architecture.decision.created"
    if "spec" in rel_path:
        return "spec.updated"
    if "plan" in rel_path:
        return "plan.created"
    if "task" in rel_path:
        return "task.completed"
    return "implementation.completed"


def summarize_session(payload: dict[str, object]) -> dict[str, object]:
    status_lines = changed_files()
    proposal_candidates = [
        line.split(maxsplit=1)[-1]
        for line in status_lines
        if "knowledge/_proposals/" in line
    ]
    final_artifacts = [
        line.split(maxsplit=1)[-1]
        for line in status_lines
        if line.endswith(".md") or line.endswith(".toml") or line.endswith(".json")
    ]
    return {
        "git_status": status_lines,
        "memory_candidates": proposal_candidates,
        "final_artifacts": final_artifacts,
        "prompt": extract_prompt(payload),
    }


def deterministic_id(seed: str) -> str:
    return f"evt_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]}"


def build_event(phase: str, payload: dict[str, object], source: str) -> dict[str, object]:
    occurred_at = utc_now()
    path_text = relative_path(extract_path(payload))
    session_id = detect_session(payload)
    repo = detect_repo()
    branch = detect_branch()
    commit = detect_commit()
    event_type = infer_event_type(phase, payload, path_text)
    artifact_kind = infer_artifact_kind(path_text, phase)
    trace_id = os.environ.get("GITHUB_RUN_ATTEMPT") or session_id
    prompt = extract_prompt(payload)
    content = (
        summarize_session(payload)
        if phase in {"sessionEnd", "agentStop"}
        else {
            "phase": phase,
            "prompt": prompt,
            "spec_path": detect_spec_path(),
            "tool_name": payload.get("toolName") or payload.get("tool_name"),
            "tool_args": payload.get("toolArgs") or payload.get("tool_args"),
            "tool_result": payload.get("toolResult") or payload.get("tool_result"),
        }
    )
    seed = "|".join([repo, branch or "", commit or "", session_id, phase, path_text or ""])
    event_id = deterministic_id(seed)

    return {
        "id": event_id,
        "event_id": event_id,
        "event_type": event_type,
        "schema_version": "1.0",
        "occurred_at": occurred_at,
        "repo": repo,
        "branch": branch,
        "commit_sha": commit,
        "file_path": path_text,
        "scope": "repo",
        "source": source,
        "session_id": session_id,
        "created_at": occurred_at,
        "content_hash": hashlib.sha256(
            json.dumps(content, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest(),
        "content": json.dumps(content, ensure_ascii=False),
        "tool_name": payload.get("toolName") or payload.get("tool_name") or phase,
        "producer": {
            "runtime": "github-copilot",
            "adapter": "copilot_hook_capture",
            "version": "1.0",
        },
        "actor": {
            "type": "agent",
            "id": os.environ.get("GITHUB_ACTOR", "github-copilot"),
        },
        "artifact": {
            "kind": artifact_kind,
            "path": path_text,
            "uri": None,
            "version": commit,
        },
        "correlation": {
            "session_id": session_id,
            "trace_id": trace_id,
            "parent_event_id": None,
            "pull_request": os.environ.get("GITHUB_EVENT_PULL_REQUEST_NUMBER"),
            "commit": commit,
        },
        "payload": content,
        "provenance": {
            "source_url": f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{repo}" if repo else None,
            "evidence": [value for value in (phase, path_text, prompt, branch, commit) if value],
        },
    }


def post_event(url: str, event: dict[str, object], ignore_errors: bool) -> None:
    body = json.dumps(event, ensure_ascii=False).encode("utf-8")
    req = urllib_request.Request(
        url,
        data=body,
        method="POST",
        headers={"content-type": "application/json"},
    )
    try:
        with urllib_request.urlopen(req, timeout=10) as response:
            response.read()
    except urllib_error.URLError as exc:
        if ignore_errors:
            print(f"copilot hook capture: failed to post to {url}: {exc}", file=sys.stderr)
            return
        raise SystemExit(f"failed to post Copilot hook event to {url}: {exc}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture Copilot hook events as Spec Memory events.")
    parser.add_argument("--phase", required=True, choices=("sessionStart", "postToolUse", "agentStop", "sessionEnd"))
    parser.add_argument("--url", default=os.environ.get("MEMORY_INGEST_API_URL", DEFAULT_URL))
    parser.add_argument("--source", default="github-copilot-cloud-agent-hook")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--ignore-errors", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = read_payload()
    event = build_event(args.phase, payload, args.source)
    if args.dry_run:
        print(json.dumps(event, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    post_event(args.url, event, args.ignore_errors)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
