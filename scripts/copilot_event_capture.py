#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib import error as urllib_error
from urllib import request as urllib_request

DEFAULT_URL = "http://127.0.0.1:8080/api/v1/events"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_github_event(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    return data if isinstance(data, dict) else {}


def first_string(*values: object) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def repository_name(event: dict[str, object]) -> str:
    repo = event.get("repository")
    if isinstance(repo, dict):
        return first_string(repo.get("full_name"), repo.get("name")) or "unknown"
    return os.environ.get("GITHUB_REPOSITORY", "unknown")


def pull_request_number(event: dict[str, object]) -> str | None:
    pr = event.get("pull_request")
    if isinstance(pr, dict):
        number = pr.get("number")
        return str(number) if number is not None else None
    return None


def event_type_for(github_event_name: str, action: str | None) -> str:
    if github_event_name == "pull_request":
        if action in {"opened", "reopened", "synchronize", "ready_for_review"}:
            return "implementation.started"
        if action == "closed":
            return "implementation.completed"
        return "implementation.started"
    if github_event_name == "pull_request_review":
        return "review.completed"
    if github_event_name in {"check_suite", "check_run", "workflow_run"}:
        return "analysis.completed"
    if github_event_name == "push":
        return "implementation.completed"
    return "lesson.learned"


def extract_artifact(event: dict[str, object]) -> dict[str, object]:
    pr = event.get("pull_request")
    if isinstance(pr, dict):
        return {
            "kind": "review" if event.get("review") else "implementation",
            "path": first_string(pr.get("html_url"), pr.get("url")),
            "uri": first_string(pr.get("html_url"), pr.get("url")),
            "version": first_string(os.environ.get("GITHUB_SHA"), pr.get("head", {}).get("sha") if isinstance(pr.get("head"), dict) else None),
        }
    return {
        "kind": "implementation",
        "path": os.environ.get("GITHUB_REF"),
        "uri": os.environ.get("GITHUB_SERVER_URL", "https://github.com") + "/" + os.environ.get("GITHUB_REPOSITORY", "unknown"),
        "version": os.environ.get("GITHUB_SHA"),
    }


def deterministic_id(seed: str) -> str:
    return f"evt_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]}"


def build_event(github_event_name: str, event: dict[str, object], source: str) -> dict[str, object]:
    action = first_string(event.get("action"))
    repo = repository_name(event)
    occurred_at = utc_now()
    event_type = event_type_for(github_event_name, action)
    pr_number = pull_request_number(event)
    commit = os.environ.get("GITHUB_SHA")
    run_id = os.environ.get("GITHUB_RUN_ID")
    artifact = extract_artifact(event)
    seed = "|".join([github_event_name, action or "", repo, pr_number or "", commit or "", run_id or ""])
    event_id = deterministic_id(seed)
    content = json.dumps(event, sort_keys=True, ensure_ascii=False)
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    return {
        "id": event_id,
        "event_id": event_id,
        "event_type": event_type,
        "schema_version": "1.0",
        "occurred_at": occurred_at,
        "repo": repo,
        "branch": os.environ.get("GITHUB_REF_NAME"),
        "commit_sha": commit,
        "file_path": artifact.get("path"),
        "scope": "repo",
        "source": source,
        "session_id": run_id,
        "created_at": occurred_at,
        "content_hash": content_hash,
        "content": content,
        "tool_name": "github-actions",
        "producer": {
            "runtime": "github-copilot",
            "adapter": "copilot_event_capture",
            "version": "1.0",
        },
        "actor": {
            "type": "system",
            "id": os.environ.get("GITHUB_ACTOR", "github-actions"),
        },
        "artifact": artifact,
        "correlation": {
            "session_id": run_id,
            "trace_id": os.environ.get("GITHUB_RUN_ATTEMPT", event_id),
            "parent_event_id": None,
            "pull_request": pr_number,
            "commit": commit,
        },
        "payload": {
            "github_event_name": github_event_name,
            "github_action": action,
            "workflow": os.environ.get("GITHUB_WORKFLOW"),
            "run_id": run_id,
        },
        "provenance": {
            "source_url": f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{repo}/actions/runs/{run_id}" if run_id else None,
            "evidence": [value for value in (github_event_name, action, pr_number, commit, run_id) if value],
        },
    }


def post_event(url: str, event: dict[str, object], ignore_errors: bool) -> None:
    body = json.dumps(event, ensure_ascii=False).encode("utf-8")
    req = urllib_request.Request(url, data=body, method="POST", headers={"content-type": "application/json"})
    try:
        with urllib_request.urlopen(req, timeout=10) as response:
            response.read()
    except urllib_error.URLError as exc:
        if ignore_errors:
            print(f"copilot event capture: failed to post to {url}: {exc}", file=sys.stderr)
            return
        raise SystemExit(f"failed to post Copilot event to {url}: {exc}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture GitHub/Copilot workflow events as Spec Memory events.")
    parser.add_argument("--event-path", default=os.environ.get("GITHUB_EVENT_PATH", ""))
    parser.add_argument("--event-name", default=os.environ.get("GITHUB_EVENT_NAME", "manual"))
    parser.add_argument("--url", default=os.environ.get("MEMORY_INGEST_API_URL", DEFAULT_URL))
    parser.add_argument("--source", default="github-copilot-agent-hook")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--ignore-errors", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    event_path = Path(args.event_path) if args.event_path else Path("/nonexistent")
    event_payload = load_github_event(event_path)
    event = build_event(args.event_name, event_payload, args.source)
    if args.dry_run:
        print(json.dumps(event, indent=2, sort_keys=True))
        return 0
    post_event(args.url, event, args.ignore_errors)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
