#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path


def download_source(source: str, dest_dir: Path) -> Path:
    if source.startswith(("http://", "https://")):
        target = dest_dir / "release.tar.gz"
        with urllib.request.urlopen(source) as response, target.open("wb") as handle:
            shutil.copyfileobj(response, handle)
        return target
    path = Path(source).expanduser()
    if not path.exists():
        raise SystemExit(f"source not found: {path}")
    return path


def safe_extract(archive: tarfile.TarFile, destination: Path) -> None:
    dest_root = destination.resolve()
    for member in archive.getmembers():
        member_path = (destination / member.name).resolve()
        if dest_root not in member_path.parents and member_path != dest_root:
            raise SystemExit(f"refusing to extract path outside destination: {member.name}")
    archive.extractall(destination)


def find_packaged_repo_root(extract_root: Path) -> Path:
    candidates = [path for path in extract_root.iterdir() if path.is_dir()]
    if len(candidates) != 1:
        raise SystemExit("release artifact must contain exactly one top-level directory")
    return candidates[0]


def run_installer(package_root: Path, args: argparse.Namespace) -> int:
    installer = package_root / "scripts" / "install_claude_assets.py"
    if not installer.exists():
        raise SystemExit(f"missing packaged installer: {installer}")

    command = [sys.executable, str(installer)]
    if args.dry_run:
        command.append("--dry-run")
    if args.force:
        command.append("--force")
    if args.config_dir:
        command.extend(["--config-dir", args.config_dir])
    command.extend(["--stack-host", args.stack_host])

    completed = subprocess.run(command, cwd=package_root)
    return completed.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install a packaged public release into Claude Code.")
    parser.add_argument(
        "--source",
        required=True,
        help="Path or URL to a release tar.gz artifact.",
    )
    parser.add_argument(
        "--config-dir",
        help="Override the Claude config directory.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow overwriting differing local files.",
    )
    parser.add_argument(
        "--stack-host",
        required=True,
        help="Host or IP for the memory stack proxy; the installer derives the MCP and ingest URLs from it.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be installed without writing files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        artifact_path = download_source(args.source, temp_root)
        extract_root = temp_root / "extract"
        extract_root.mkdir(parents=True, exist_ok=True)
        with tarfile.open(artifact_path, mode="r:gz") as archive:
            safe_extract(archive, extract_root)
        package_root = find_packaged_repo_root(extract_root)
        return run_installer(package_root, args)


if __name__ == "__main__":
    raise SystemExit(main())
