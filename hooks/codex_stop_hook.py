#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def run_command(command: list[str], cwd: Path) -> int:
    completed = subprocess.run(command, cwd=cwd)
    return completed.returncode


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    python = sys.executable

    poster = [
        python,
        str(repo_root / "hooks" / "memory_event_poster.py"),
        "--url",
        "http://127.0.0.1:8080/api/v1/events",
        "--source",
        "codex-code-hook",
        "--ignore-errors",
        "--event-type",
        "session_stop",
    ]
    promote = [
        python,
        str(repo_root / "hooks" / "codex_hook_runner.py"),
        "promote-ready",
    ]

    poster_code = run_command(poster, repo_root)
    promote_code = run_command(promote, repo_root)

    response = {
        "continue": True,
        "statusMessage": "Captured session handoff and checked proposal promotion",
        "hookStatus": {
            "session_stop": poster_code,
            "promote_ready": promote_code,
        },
    }
    print(json.dumps(response, ensure_ascii=False))
    return 0 if poster_code == 0 and promote_code == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
