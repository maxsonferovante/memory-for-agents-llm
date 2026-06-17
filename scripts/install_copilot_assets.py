#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import platform
import shutil
import time
from pathlib import Path

from stack_urls import build_stack_urls

COPILOT_ASSET_PATHS = (
    Path("copilot-instructions.md"),
    Path("instructions"),
    Path("prompts"),
    Path("agents"),
    Path("skills"),
    Path("workflows/spec-memory-copilot-events.yml"),
)

COPILOT_REPO_ASSET_PATHS = (
    Path("scripts/copilot_event_capture.py"),
)


def discover_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def render_workflow(source: Path, ingest_url: str | None) -> str:
    text = source.read_text(encoding="utf-8")
    if ingest_url:
        old = "${{ secrets.MEMORY_INGEST_API_URL || 'http://127.0.0.1:8080/api/v1/events' }}"
        new = f"${{{{ secrets.MEMORY_INGEST_API_URL || '{ingest_url}' }}}}"
        text = text.replace(old, new)
    return text


def copy_rendered_file(source: Path, target: Path, text: str, force: bool, dry_run: bool) -> str:
    if target.exists() and target.is_dir():
        raise SystemExit(f"refusing to overwrite directory with file: {target}")

    payload = text.encode("utf-8")
    if target.exists():
        if target.read_bytes() == payload:
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
        target.write_text(text, encoding="utf-8")
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


def install_assets(
    source_github: Path,
    target_github: Path,
    source_repo: Path,
    target_repo: Path,
    force: bool,
    dry_run: bool,
    ingest_url: str | None,
) -> list[str]:
    actions: list[str] = []
    for relative in COPILOT_ASSET_PATHS:
        source = source_github / relative
        target = target_github / relative
        if not source.exists():
            actions.append(f"missing source {source}")
            continue
        if source.is_dir():
            actions.extend(copy_tree(source, target, force=force, dry_run=dry_run))
            continue
        if relative == Path("workflows/spec-memory-copilot-events.yml"):
            actions.append(
                copy_rendered_file(
                    source,
                    target,
                    render_workflow(source, ingest_url),
                    force=force,
                    dry_run=dry_run,
                )
            )
        else:
            actions.append(copy_file(source, target, force=force, dry_run=dry_run))
    for relative in COPILOT_REPO_ASSET_PATHS:
        source = source_repo / relative
        target = target_repo / relative
        if not source.exists():
            actions.append(f"missing source {source}")
            continue
        actions.append(copy_file(source, target, force=force, dry_run=dry_run))
    return actions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install GitHub Copilot Spec Memory Platform assets into a target repository."
    )
    parser.add_argument(
        "--target-repo",
        type=Path,
        default=Path.cwd(),
        help="Repository to receive .github Copilot assets (defaults to current directory).",
    )
    parser.add_argument(
        "--source-repo",
        type=Path,
        help="Repository containing source .github Copilot assets (defaults to this repo).",
    )
    parser.add_argument(
        "--stack-host",
        help="Optional memory stack host/IP; when set, the workflow fallback ingest URL is rendered for that stack.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing Copilot asset files when they differ, keeping timestamped backups.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing anything.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_repo = args.source_repo.expanduser().resolve() if args.source_repo else discover_repo_root()
    target_repo = args.target_repo.expanduser().resolve()
    source_github = source_repo / ".github"
    target_github = target_repo / ".github"
    ingest_url = build_stack_urls(args.stack_host).ingest_url if args.stack_host else None

    if not source_github.exists():
        raise SystemExit(f"source .github directory does not exist: {source_github}")

    actions = install_assets(
        source_github=source_github,
        target_github=target_github,
        source_repo=source_repo,
        target_repo=target_repo,
        force=args.force,
        dry_run=args.dry_run,
        ingest_url=ingest_url,
    )

    print(f"Detected OS: {platform.system() or os.name}")
    print(f"Source repository: {source_repo}")
    print(f"Target repository: {target_repo}")
    print(f"Target .github directory: {target_github}")
    if ingest_url:
        print(f"Rendered workflow fallback ingest URL: {ingest_url}")
    for action in actions:
        print(action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
