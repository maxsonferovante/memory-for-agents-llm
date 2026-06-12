#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path


PACKAGE_NAME = "memory-for-agents-llm"
DEFAULT_OUTPUT_DIR = "dist/releases"

BASE_PATHS = [
    "AGENTS.md",
    "CLAUDE.md",
    "CODEX.md",
    "QUICKSTART.md",
    "README.md",
    ".claude",
    ".codex",
    ".agents",
    "hooks",
    "local_stack",
    "scripts",
]

OPTIONAL_PATHS = [
    "knowledge",
]


def discover_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def git_version(repo_root: Path) -> str:
    try:
        return run_git(repo_root, "describe", "--tags", "--always", "--dirty")
    except subprocess.CalledProcessError:
        return run_git(repo_root, "rev-parse", "--short", "HEAD")


def git_commit(repo_root: Path) -> str:
    return run_git(repo_root, "rev-parse", "HEAD")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_paths(repo_root: Path, include_knowledge: bool) -> list[Path]:
    paths = [repo_root / rel for rel in BASE_PATHS]
    if include_knowledge:
        paths.extend(repo_root / rel for rel in OPTIONAL_PATHS)
    return [path for path in paths if path.exists()]


def iter_release_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    files.append(child)
        elif path.is_file():
            files.append(path)
    excluded_parts = {"__pycache__", "target", ".terraform", ".git"}
    excluded_suffixes = {".pyc", ".pyo"}
    return [
        path
        for path in files
        if not any(part in excluded_parts for part in path.parts)
        and path.suffix not in excluded_suffixes
    ]


def safe_tarinfo(path: Path, arcname: str) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name=arcname)
    stat = path.stat()
    info.size = stat.st_size
    info.mode = 0o644
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    return info


def write_release_manifest(
    release_root: Path,
    version: str,
    commit: str,
    include_knowledge: bool,
    files: list[Path],
    repo_root: Path,
) -> Path:
    manifest_path = release_root / "release-manifest.json"
    manifest = {
        "package_name": PACKAGE_NAME,
        "version": version,
        "commit": commit,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "include_knowledge": include_knowledge,
        "files": [
            {
                "path": str(path.relative_to(repo_root).as_posix()),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in files
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest_path


def build_artifact(
    repo_root: Path,
    output_dir: Path,
    version: str,
    include_knowledge: bool,
) -> Path:
    commit = git_commit(repo_root)
    release_root = output_dir / f"{PACKAGE_NAME}-{version}"
    if release_root.exists():
        shutil.rmtree(release_root)
    release_root.mkdir(parents=True, exist_ok=True)

    source_paths = collect_paths(repo_root, include_knowledge)
    files = iter_release_files(source_paths)
    write_release_manifest(release_root, version, commit, include_knowledge, files, repo_root)

    for source in files:
        relative = source.relative_to(repo_root)
        target = release_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    artifact_path = output_dir / f"{PACKAGE_NAME}-{version}.tar.gz"
    with artifact_path.open("wb") as raw_file:
        with gzip.GzipFile(fileobj=raw_file, mode="wb", mtime=0) as gz_file:
            with tarfile.open(fileobj=gz_file, mode="w") as tar:
                for path in sorted(release_root.rglob("*")):
                    if not path.is_file():
                        continue
                    arcname = str(path.relative_to(output_dir).as_posix())
                    info = safe_tarinfo(path, arcname)
                    with path.open("rb") as handle:
                        tar.addfile(info, handle)

    checksum_path = artifact_path.parent / f"{artifact_path.name}.sha256"
    checksum_path.write_text(f"{sha256_file(artifact_path)}  {artifact_path.name}\n", encoding="utf-8")
    return artifact_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a deterministic release artifact.")
    parser.add_argument(
        "--version",
        help="Version string for the artifact. Defaults to git describe.",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Where to write the release artifact.",
    )
    parser.add_argument(
        "--include-knowledge",
        action="store_true",
        help="Include the knowledge/ tree in the artifact.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = discover_repo_root()
    version = args.version or git_version(repo_root)
    output_dir = (repo_root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    artifact_path = build_artifact(
        repo_root=repo_root,
        output_dir=output_dir,
        version=version,
        include_knowledge=args.include_knowledge,
    )

    print(f"version: {version}")
    print(f"commit: {git_commit(repo_root)}")
    print(f"artifact: {artifact_path}")
    print(f"checksum: {artifact_path.parent / (artifact_path.name + '.sha256')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
