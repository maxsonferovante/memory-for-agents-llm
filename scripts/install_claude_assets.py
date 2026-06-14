#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import sys
import time
from pathlib import Path
from typing import Iterable

from stack_urls import StackUrls, build_stack_urls


PACKAGE_NAME = "memory-for-agents-llm"
HOOK_MATCHER = ".*"
CLAUDE_MCP_SERVER_NAME = "localMemory"


def discover_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def discover_claude_home(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.expanduser()

    env_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    if env_dir:
        return Path(env_dir).expanduser()

    return Path.home() / ".claude"


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return data


def write_json(path: Path, data: dict, dry_run: bool) -> None:
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload + "\n", encoding="utf-8")


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


def quote_command(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def hook_runner_source() -> str:
    return """#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PATH_KEYS = ("file_path", "filePath", "path", "target_path")


def read_payload() -> dict:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def first_string(value, keys: tuple[str, ...]) -> str | None:
    if isinstance(value, dict):
        for key in keys:
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate
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


def extract_path(payload: dict) -> str | None:
    return first_string(payload, PATH_KEYS)


def is_memory_path(path_text: str) -> bool:
    parts = Path(path_text).parts
    return "knowledge" in parts and "_proposals" in parts


def run_memory_hooks(argv: list[str]) -> int:
    if not argv:
        print("memory hook runner: missing subcommand", file=sys.stderr)
        return 1

    package_root = Path(__file__).resolve().parent
    hooks_script = package_root / "memory_hooks.py"
    if not hooks_script.exists():
        print(f"memory hook runner: missing {hooks_script}", file=sys.stderr)
        return 1

    subcommand = argv[0]
    payload = read_payload()
    tool_name = str(payload.get("tool_name") or "").strip() or "Write"
    path_text = extract_path(payload)

    if subcommand == "guard-write":
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
        if not path_text or not is_memory_path(path_text):
            return 0
        command = [sys.executable, str(hooks_script), "validate-promotion", path_text]
    elif subcommand == "promote-ready":
        queue_root = Path.cwd() / "knowledge" / "_proposals"
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
        print(f"memory hook runner: unknown subcommand {subcommand}", file=sys.stderr)
        return 1

    completed = subprocess.run(command, cwd=Path.cwd())
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(run_memory_hooks(sys.argv[1:]))
"""


def ensure_hook_runner(package_hooks_dir: Path, dry_run: bool) -> str:
    runner_path = package_hooks_dir / "claude_hook_runner.py"
    runner_text = hook_runner_source().rstrip() + "\n"
    existed = runner_path.exists()
    if existed:
        if runner_path.read_text(encoding="utf-8") == runner_text:
            return f"unchanged {runner_path}"
        if dry_run:
            return f"would update {runner_path}"
    else:
        if dry_run:
            return f"would write {runner_path}"

    runner_path.parent.mkdir(parents=True, exist_ok=True)
    runner_path.write_text(runner_text, encoding="utf-8")
    return f"{'updated' if existed else 'created'} {runner_path}"


def merge_hook(settings: dict, event: str, entry: dict) -> bool:
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise SystemExit("settings.json hooks must be an object")

    current = hooks.setdefault(event, [])
    if not isinstance(current, list):
        raise SystemExit(f"settings.json hooks.{event} must be an array")

    def normalize(hook: dict) -> dict:
        normalized = dict(hook)
        if normalized.get("timeout") == 60:
            normalized.pop("timeout", None)
        if normalized.get("matcher") in {"", None}:
            normalized.pop("matcher", None)
        return normalized

    signature = json.dumps(normalize(entry), sort_keys=True, ensure_ascii=False)
    for existing in current:
        if not isinstance(existing, dict):
            raise SystemExit(f"settings.json hooks.{event} entries must be objects")
        if json.dumps(normalize(existing), sort_keys=True, ensure_ascii=False) == signature:
            return False

    current.append(entry)
    return True


def claude_project_state_path(claude_home: Path) -> Path:
    return claude_home.with_name(f"{claude_home.name}.json")


def build_claude_local_memory_server(stack_urls: StackUrls) -> dict:
    return {"url": stack_urls.mcp_url}


def merge_project_mcp_server(
    state: dict, project_root: Path, server_name: str, server_config: dict
) -> bool:
    projects = state.setdefault("projects", {})
    if not isinstance(projects, dict):
        raise SystemExit(".claude.json projects must be an object")

    project_key = str(project_root)
    project_state = projects.setdefault(project_key, {})
    if not isinstance(project_state, dict):
        raise SystemExit(f".claude.json projects.{project_key} must be an object")

    if "mcpContextUris" not in project_state:
        project_state["mcpContextUris"] = []
    if not isinstance(project_state["mcpContextUris"], list):
        raise SystemExit(f".claude.json projects.{project_key}.mcpContextUris must be an array")

    if "enabledMcpjsonServers" not in project_state:
        project_state["enabledMcpjsonServers"] = []
    if not isinstance(project_state["enabledMcpjsonServers"], list):
        raise SystemExit(
            f".claude.json projects.{project_key}.enabledMcpjsonServers must be an array"
        )

    if "disabledMcpjsonServers" not in project_state:
        project_state["disabledMcpjsonServers"] = []
    if not isinstance(project_state["disabledMcpjsonServers"], list):
        raise SystemExit(
            f".claude.json projects.{project_key}.disabledMcpjsonServers must be an array"
        )

    mcp_servers = project_state.setdefault("mcpServers", {})
    if not isinstance(mcp_servers, dict):
        raise SystemExit(f".claude.json projects.{project_key}.mcpServers must be an object")

    current = mcp_servers.get(server_name)
    if current == server_config:
        return False

    mcp_servers[server_name] = server_config
    return True


def build_hook_entry(command: str, matcher: str | None = None) -> dict:
    hook_entry = {"type": "command", "command": command, "timeout": 60}
    entry: dict = {"hooks": [hook_entry]}
    if matcher is not None:
        entry["matcher"] = matcher
    return entry


def update_settings(
    settings_path: Path,
    runner_path: Path,
    package_hooks_dir: Path,
    stack_urls: StackUrls,
    dry_run: bool,
) -> str:
    settings = read_json(settings_path)

    hook_command_base = quote_command(
        [Path(sys.executable).as_posix(), runner_path.as_posix()]
    )
    event_command = quote_command(
        [
            Path(sys.executable).as_posix(),
            (package_hooks_dir / "memory_event_poster.py").as_posix(),
            "--url",
            stack_urls.ingest_url,
        ]
    )

    changed = False
    changed |= merge_hook(
        settings,
        "PreToolUse",
        build_hook_entry(f"{hook_command_base} guard-write", HOOK_MATCHER),
    )
    changed |= merge_hook(
        settings,
        "PostToolUse",
        build_hook_entry(f"{event_command}", HOOK_MATCHER),
    )
    changed |= merge_hook(
        settings,
        "Stop",
        build_hook_entry(f"{event_command}", ""),
    )
    changed |= merge_hook(
        settings,
        "PostToolUse",
        build_hook_entry(f"{hook_command_base} validate-promotion", HOOK_MATCHER),
    )
    changed |= merge_hook(
        settings,
        "Stop",
        build_hook_entry(f"{hook_command_base} promote-ready", ""),
    )

    if not changed:
        return f"unchanged {settings_path}"

    if settings_path.exists():
        if dry_run:
            message = f"would update {settings_path}"
        else:
            backup = backup_path(settings_path)
            shutil.copy2(settings_path, backup)
            message = f"updated {settings_path} (backup {backup})"
    else:
        message = f"{'would ' if dry_run else ''}create {settings_path}"

    write_json(settings_path, settings, dry_run=dry_run)
    return message


def update_project_state(
    state_path: Path, repo_root: Path, stack_urls: StackUrls, dry_run: bool
) -> str:
    state = read_json(state_path)
    changed = merge_project_mcp_server(
        state,
        repo_root,
        CLAUDE_MCP_SERVER_NAME,
        build_claude_local_memory_server(stack_urls),
    )

    if not changed:
        return f"unchanged {state_path}"

    if state_path.exists():
        if dry_run:
            message = f"would update {state_path}"
        else:
            backup = backup_path(state_path)
            shutil.copy2(state_path, backup)
            message = f"updated {state_path} (backup {backup})"
    else:
        message = f"{'would ' if dry_run else ''}create {state_path}"

    write_json(state_path, state, dry_run=dry_run)
    return message


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install Claude Code agents, skills, and memory hooks."
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        help="Override the Claude Code config directory (defaults to CLAUDE_CONFIG_DIR or ~/.claude).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files when they differ.",
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
    source_claude_dir = repo_root / ".claude"
    source_agents = source_claude_dir / "agents"
    source_skills = source_claude_dir / "skills"
    source_hooks = repo_root / "hooks"

    claude_home = discover_claude_home(args.config_dir)
    package_root = claude_home / PACKAGE_NAME
    package_hooks_dir = package_root / "hooks"

    actions: list[str] = []
    actions.extend(copy_tree(source_agents, claude_home / "agents", args.force, args.dry_run))
    actions.extend(copy_tree(source_skills, claude_home / "skills", args.force, args.dry_run))
    actions.extend(copy_tree(source_hooks, package_hooks_dir, args.force, args.dry_run))
    actions.append(ensure_hook_runner(package_hooks_dir, args.dry_run))
    actions.append(
        update_settings(
            claude_home / "settings.json",
            package_hooks_dir / "claude_hook_runner.py",
            package_hooks_dir,
            stack_urls,
            args.dry_run,
        )
    )
    actions.append(
        update_project_state(
            claude_project_state_path(claude_home),
            repo_root,
            stack_urls,
            args.dry_run,
        )
    )

    print(f"Claude config directory: {claude_home}")
    print(f"Package root: {package_root}")
    print(f"Stack base URL: {stack_urls.base_url}")
    for action in actions:
        print(action)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
