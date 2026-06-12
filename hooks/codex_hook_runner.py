#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


PATH_KEYS = ("file_path", "filePath", "path", "target_path")
TOOL_KEYS = ("tool_name", "toolName", "name")


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


def extract_path(payload: dict[str, object]) -> str | None:
    return first_string(payload, PATH_KEYS)


def extract_tool(payload: dict[str, object]) -> str:
    return first_string(payload, TOOL_KEYS) or "codex-tool"


def is_proposal_path(path_text: str) -> bool:
    parts = Path(path_text).parts
    return "knowledge" in parts and "_proposals" in parts


def run_memory_hooks(argv: list[str]) -> int:
    if not argv:
        print("codex hook runner: missing subcommand", file=sys.stderr)
        return 1

    repo_root = Path.cwd()
    configured_hooks_script = os.environ.get("MEMORY_HOOKS_SCRIPT")
    candidate_hooks = [
        Path(configured_hooks_script).expanduser() if configured_hooks_script else None,
        Path(__file__).resolve().with_name("memory_hooks.py"),
        repo_root / "hooks" / "memory_hooks.py",
    ]
    hooks_script = next(
        (
            candidate
            for candidate in candidate_hooks
            if candidate is not None and candidate.exists()
        ),
        None,
    )
    if hooks_script is None:
        print("codex hook runner: missing memory_hooks.py", file=sys.stderr)
        return 1

    payload = read_payload()
    subcommand = argv[0]
    path_text = extract_path(payload)
    tool_name = extract_tool(payload)

    if subcommand == "guard-write":
        # Codex sends many tool events that do not target a file path. Only enforce
        # policy when a path can be extracted from the nested hook payload.
        if not path_text:
            return 0
        command = [
            sys.executable,
            str(hooks_script),
            "guard-write",
            "--path",
            path_text,
            "--tool",
            tool_name,
        ]
    elif subcommand == "validate-promotion":
        if not path_text or not is_proposal_path(path_text):
            return 0
        command = [sys.executable, str(hooks_script), "validate-promotion", path_text]
    elif subcommand == "promote-ready":
        queue_root = repo_root / "knowledge" / "_proposals"
        if not queue_root.exists():
            return 0
        command = [
            sys.executable,
            str(hooks_script),
            "promote-ready",
            "--queue",
            str(queue_root),
        ]
    else:
        print(f"codex hook runner: unknown subcommand {subcommand}", file=sys.stderr)
        return 1

    completed = subprocess.run(command, cwd=repo_root)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(run_memory_hooks(sys.argv[1:]))
