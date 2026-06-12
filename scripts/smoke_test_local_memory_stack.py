#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib import error as urllib_error
from urllib import request as urllib_request


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_POSTER = REPO_ROOT / "hooks" / "memory_event_poster.py"
API_URL = "http://127.0.0.1:8081"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test the local memory stack end to end.")
    parser.add_argument("--keep-up", action="store_true", help="Leave the compose stack running after the test.")
    parser.add_argument("--timeout", type=int, default=120, help="Overall timeout in seconds.")
    return parser.parse_args()


def run(*args: str, input_text: str | None = None, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        list(args),
        cwd=REPO_ROOT,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=True,
    )
    return completed.stdout


def wait_for_health(timeout: int) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib_request.urlopen(f"{API_URL}/healthz", timeout=3) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(1)
    raise SystemExit("local memory API did not become healthy in time")


def post_hook_event(payload: dict[str, object]) -> None:
    env = dict(os.environ)
    env["MEMORY_INGEST_API_URL"] = f"{API_URL}/v1/events"
    run(sys.executable, str(HOOK_POSTER), input_text=json.dumps(payload), env=env)


def fetch_items() -> list[dict[str, object]]:
    with urllib_request.urlopen(f"{API_URL}/v1/items", timeout=5) as response:
        data = json.loads(response.read().decode("utf-8"))
    items = data.get("items", [])
    return items if isinstance(items, list) else []


def main() -> int:
    args = parse_args()
    stack_started = False
    try:
        run("docker", "compose", "up", "-d", "--build")
        stack_started = True
        wait_for_health(args.timeout)

        payload = {
            "event_type": "session_stop",
            "repo": Path(REPO_ROOT).name,
            "branch": "feature/local-memory-stack",
            "commit_sha": run("git", "rev-parse", "HEAD").strip(),
            "file_path": "knowledge/repos/smoke-test.md",
            "scope": "repo",
            "source": "claude-code-hook",
            "session_id": "smoke-test-session",
            "created_at": "2026-06-11T00:00:00Z",
            "content": """---
title: Smoke test memory
---

# Smoke test memory

This note exists only to validate the local ingestion and indexing flow.
""",
        }
        post_hook_event(payload)

        deadline = time.time() + args.timeout
        while time.time() < deadline:
            items = fetch_items()
            match = next(
                (
                    item
                    for item in items
                    if isinstance(item, dict)
                    and item.get("source_file") == "knowledge/repos/smoke-test.md"
                    and item.get("title") == "Smoke test memory"
                ),
                None,
            )
            if match:
                print(
                    json.dumps(
                        {
                            "status": "ok",
                            "indexed_item": match,
                            "item_count": len(items),
                        },
                        indent=2,
                        ensure_ascii=False,
                    )
                )
                return 0
            time.sleep(1)

        raise SystemExit("smoke test did not index the expected item in time")
    finally:
        if stack_started and not args.keep_up:
            subprocess.run(["docker", "compose", "down", "-v"], cwd=REPO_ROOT, check=False)


if __name__ == "__main__":
    raise SystemExit(main())

