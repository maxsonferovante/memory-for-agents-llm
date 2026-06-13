#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
import time
import tomllib
import re
from pathlib import Path
from typing import Any, Iterable

from stack_urls import StackUrls, build_stack_urls


PACKAGE_NAME = "memory-for-agents-llm"


LOCAL_MEMORY_MCP_SERVER = {
    "startup_timeout_sec": 30,
    "tool_timeout_sec": 60,
    "enabled": True,
    "required": False,
    "default_tools_approval_mode": "auto",
}


CODEX_MCP_SERVERS = {
    "openaiDeveloperDocs": {
        "url": "https://developers.openai.com/mcp",
        "startup_timeout_sec": 15,
        "tool_timeout_sec": 60,
        "enabled": True,
        "required": False,
        "default_tools_approval_mode": "auto",
    },
}


CODEX_AGENT_SETTINGS = {
    "max_threads": 6,
    "max_depth": 1,
    "job_max_runtime_seconds": 1800,
}


CODEX_FEATURES = {
    "hooks": True,
}


def build_local_memory_server(stack_urls: StackUrls) -> dict[str, Any]:
    return {
        "url": stack_urls.mcp_url,
        **LOCAL_MEMORY_MCP_SERVER,
    }


def discover_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def discover_codex_home(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.expanduser()

    env_dir = os.environ.get("CODEX_HOME") or os.environ.get("OPENAI_CODEX_HOME")
    if env_dir:
        return Path(env_dir).expanduser()

    return Path.home() / ".codex"


def discover_skills_dir(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.expanduser()

    env_dir = os.environ.get("CODEX_SKILLS_DIR")
    if env_dir:
        return Path(env_dir).expanduser()

    return Path.home() / ".agents" / "skills"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return data


def write_json(path: Path, data: dict[str, Any], dry_run: bool) -> None:
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload + "\n", encoding="utf-8")


def read_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise SystemExit(f"invalid TOML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must contain a TOML table")
    return data


def toml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


_TOML_BARE_KEY_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def toml_key(key: str) -> str:
    if _TOML_BARE_KEY_RE.fullmatch(key):
        return key
    return toml_quote(key)


def toml_dotted_path(parts: Iterable[str]) -> str:
    return ".".join(toml_key(part) for part in parts)


def toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, str):
        return toml_quote(value)
    if isinstance(value, list):
        if all(not isinstance(item, dict) for item in value):
            return "[" + ", ".join(toml_value(item) for item in value) + "]"
    raise TypeError(f"unsupported TOML value: {value!r}")


def emit_toml_table(
    lines: list[str], table: dict[str, Any], prefix: list[str] | None = None
) -> None:
    prefix = prefix or []
    scalars: dict[str, Any] = {}
    arrays: dict[str, list[dict[str, Any]]] = {}
    children: dict[str, dict[str, Any]] = {}

    for key, value in table.items():
        if isinstance(value, dict):
            children[key] = value
        elif (
            isinstance(value, list)
            and value
            and all(isinstance(item, dict) for item in value)
        ):
            arrays[key] = value
        else:
            scalars[key] = value

    for key in sorted(scalars):
        lines.append(f"{toml_key(key)} = {toml_value(scalars[key])}")

    for key in sorted(children):
        if lines and lines[-1] != "":
            lines.append("")
        section = toml_dotted_path([*prefix, key])
        lines.append(f"[{section}]")
        emit_toml_table(lines, children[key], [*prefix, key])

    for key in sorted(arrays):
        section = toml_dotted_path([*prefix, key])
        for item in arrays[key]:
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(f"[[{section}]]")
            emit_toml_table(lines, item, [*prefix, key])


def write_toml(path: Path, data: dict[str, Any], dry_run: bool) -> None:
    lines: list[str] = []
    emit_toml_table(lines, data)
    payload = "\n".join(lines).rstrip() + "\n"
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def file_digest(path: Path) -> bytes:
    return path.read_bytes()


def backup_path(path: Path) -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return path.with_name(f"{path.name}.bak.{stamp}")


def copy_file(source: Path, target: Path, force: bool, dry_run: bool) -> str:
    if target.exists() and target.is_dir():
        raise SystemExit(f"refusing to overwrite directory with file: {target}")

    if target.exists():
        if file_digest(source) == file_digest(target):
            return f"unchanged {target}"
        if not force:
            return f"{'would ' if dry_run else ''}skip existing {target}"
        backup = backup_path(target)
        if not dry_run:
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup)
        action = f"{'would ' if dry_run else ''}update {target} (backup {backup})"
    else:
        action = f"{'would ' if dry_run else ''}create {target}"

    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return action


def copy_tree(source_root: Path, target_root: Path, force: bool, dry_run: bool) -> list[str]:
    if not source_root.exists():
        return [f"missing source tree {source_root}"]

    actions: list[str] = []
    for source in sorted(source_root.rglob("*")):
        if source.is_dir():
            continue
        if source.name == "__pycache__" or source.suffix in {".pyc", ".pyo"}:
            continue
        relative = source.relative_to(source_root)
        target = target_root / relative
        actions.append(copy_file(source, target, force=force, dry_run=dry_run))
    return actions


def quote_posix(parts: Iterable[str | Path]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def quote_windows(parts: Iterable[str | Path]) -> str:
    return subprocess.list2cmdline([str(part) for part in parts])


def python_command(script: Path, *args: str) -> str:
    return quote_posix([Path(sys.executable).as_posix(), script.as_posix(), *args])


def python_command_windows(script: Path, *args: str) -> str:
    return quote_windows([sys.executable, script, *args])


def build_hook_entry(
    command: str,
    command_windows: str | None = None,
    matcher: str | None = None,
    timeout: int = 30,
    status: str | None = None,
) -> dict[str, Any]:
    hook_entry: dict[str, Any] = {"type": "command", "command": command, "timeout": timeout}
    if command_windows:
        hook_entry["commandWindows"] = command_windows
    if status:
        hook_entry["statusMessage"] = status
    entry: dict[str, Any] = {"hooks": [hook_entry]}
    if matcher is not None:
        entry["matcher"] = matcher
    return entry


def normalize_hook_entry(entry: dict[str, Any]) -> str:
    return json.dumps(entry, sort_keys=True, ensure_ascii=False)


def merge_hook(settings: dict[str, Any], event: str, entry: dict[str, Any]) -> bool:
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise SystemExit("hooks.json `hooks` must be an object")

    current = hooks.setdefault(event, [])
    if not isinstance(current, list):
        raise SystemExit(f"hooks.json hooks.{event} must be an array")

    signature = normalize_hook_entry(entry)
    for existing in current:
        if not isinstance(existing, dict):
            raise SystemExit(f"hooks.json hooks.{event} entries must be objects")
        if normalize_hook_entry(existing) == signature:
            return False

    current.append(entry)
    return True


def update_hooks_json(
    hooks_path: Path, package_hooks_dir: Path, stack_urls: StackUrls, dry_run: bool
) -> str:
    settings = read_json(hooks_path)
    runner = package_hooks_dir / "codex_hook_runner.py"
    poster = package_hooks_dir / "memory_event_poster.py"

    runner_command = python_command(runner)
    runner_command_windows = python_command_windows(runner)
    poster_command = python_command(poster, "--url", stack_urls.ingest_url)
    poster_command_windows = python_command_windows(poster, "--url", stack_urls.ingest_url)

    changed = False
    changed |= merge_hook(
        settings,
        "PreToolUse",
        build_hook_entry(
            f"{runner_command} guard-write",
            f"{runner_command_windows} guard-write",
            ".*",
            30,
            "Checking memory write policy",
        ),
    )
    changed |= merge_hook(
        settings,
        "PostToolUse",
        build_hook_entry(
            f"{poster_command} --source codex-code-hook --ignore-errors",
            f"{poster_command_windows} --source codex-code-hook --ignore-errors",
            ".*",
            30,
            "Posting memory event",
        ),
    )
    changed |= merge_hook(
        settings,
        "PostToolUse",
        build_hook_entry(
            f"{runner_command} validate-promotion",
            f"{runner_command_windows} validate-promotion",
            ".*",
            30,
            "Validating memory proposal",
        ),
    )
    changed |= merge_hook(
        settings,
        "SubagentStop",
        build_hook_entry(
            (
                f"{poster_command} --source codex-subagent-hook "
                "--event-type subagent_stop --ignore-errors"
            ),
            (
                f"{poster_command_windows} --source codex-subagent-hook "
                "--event-type subagent_stop --ignore-errors"
            ),
            None,
            30,
            "Capturing subagent memory handoff",
        ),
    )
    changed |= merge_hook(
        settings,
        "Stop",
        build_hook_entry(
            (
                f"{poster_command} --source codex-code-hook "
                "--ignore-errors --event-type session_stop"
            ),
            (
                f"{poster_command_windows} --source codex-code-hook "
                "--ignore-errors --event-type session_stop"
            ),
            None,
            30,
            "Capturing session memory handoff",
        ),
    )
    changed |= merge_hook(
        settings,
        "Stop",
        build_hook_entry(
            f"{runner_command} promote-ready",
            f"{runner_command_windows} promote-ready",
            None,
            60,
            "Promoting ready memory proposals",
        ),
    )

    if not changed:
        return f"unchanged {hooks_path}"

    if hooks_path.exists():
        if dry_run:
            message = f"would update {hooks_path}"
        else:
            backup = backup_path(hooks_path)
            shutil.copy2(hooks_path, backup)
            message = f"updated {hooks_path} (backup {backup})"
    else:
        message = f"{'would ' if dry_run else ''}create {hooks_path}"

    write_json(hooks_path, settings, dry_run)
    return message


def merge_table(target: dict[str, Any], values: dict[str, Any]) -> bool:
    changed = False
    for key, value in values.items():
        if isinstance(value, dict):
            child = target.setdefault(key, {})
            if not isinstance(child, dict):
                target[key] = {}
                child = target[key]
                changed = True
            changed |= merge_table(child, value)
        elif target.get(key) != value:
            target[key] = value
            changed = True
    return changed


def update_config_toml(config_path: Path, stack_urls: StackUrls, dry_run: bool) -> str:
    config = read_toml(config_path)
    local_memory = build_local_memory_server(stack_urls)

    desired = {
        "features": CODEX_FEATURES,
        "agents": CODEX_AGENT_SETTINGS,
        "mcp_servers": {
            "localMemory": local_memory,
            "openaiDeveloperDocs": CODEX_MCP_SERVERS["openaiDeveloperDocs"],
        },
    }

    changed = merge_table(config, desired)
    if not changed:
        return f"unchanged {config_path}"

    if config_path.exists():
        if dry_run:
            message = f"would update {config_path}"
        else:
            backup = backup_path(config_path)
            shutil.copy2(config_path, backup)
            message = f"updated {config_path} (backup {backup})"
    else:
        message = f"{'would ' if dry_run else ''}create {config_path}"

    write_toml(config_path, config, dry_run)
    return message


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install Codex agents, skills, MCP servers, and memory hooks globally."
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        help=(
            "Override the Codex config directory "
            "(defaults to CODEX_HOME, OPENAI_CODEX_HOME, or ~/.codex)."
        ),
    )
    parser.add_argument(
        "--skills-dir",
        type=Path,
        help=(
            "Override the Codex user skills directory "
            "(defaults to CODEX_SKILLS_DIR or ~/.agents/skills)."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing installed agent, skill, and hook files when they differ.",
    )
    parser.add_argument(
        "--stack-host",
        required=True,
        help="Host or IP for the memory stack proxy; the installer derives the MCP and ingest URLs from it.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing anything.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = discover_repo_root()
    stack_urls = build_stack_urls(args.stack_host)
    source_codex_dir = repo_root / ".codex"
    source_agents = source_codex_dir / "agents"
    source_skills = repo_root / ".agents" / "skills"
    source_hooks = repo_root / "hooks"

    codex_home = discover_codex_home(args.config_dir)
    skills_dir = discover_skills_dir(args.skills_dir)
    package_root = codex_home / PACKAGE_NAME
    package_hooks_dir = package_root / "hooks"

    actions: list[str] = []
    actions.extend(copy_tree(source_agents, codex_home / "agents", args.force, args.dry_run))
    actions.extend(copy_tree(source_skills, skills_dir, args.force, args.dry_run))
    actions.extend(copy_tree(source_hooks, package_hooks_dir, args.force, args.dry_run))
    actions.append(update_config_toml(codex_home / "config.toml", stack_urls, args.dry_run))
    actions.append(
        update_hooks_json(codex_home / "hooks.json", package_hooks_dir, stack_urls, args.dry_run)
    )

    print(f"Detected OS: {platform.system() or os.name}")
    print(f"Codex config directory: {codex_home}")
    print(f"Codex agents directory: {codex_home / 'agents'}")
    print(f"Codex user skills directory: {skills_dir}")
    print(f"Package root: {package_root}")
    print(f"Repository root: {repo_root}")
    print(f"Stack base URL: {stack_urls.base_url}")
    for action in actions:
        print(action)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
