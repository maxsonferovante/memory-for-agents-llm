#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOKS_DIR = REPO_ROOT / "hooks"
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from central_memory_backend_client import BackendClient, BackendConfig, resolve_env_file  # noqa: E402


@dataclass(frozen=True)
class SmokeBundle:
    bundle_path: Path
    bundle_sha256: str
    bundle_size_bytes: int
    file_sha256: str
    file_size_bytes: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test the central memory backend write/read flow.")
    parser.add_argument(
        "--env-file",
        default=os.environ.get("MEMORY_BACKEND_ENV_FILE", "dist/backend/central-memory-backend/backend.env"),
        help="Path to the sourced backend.env file.",
    )
    parser.add_argument(
        "--repo-name",
        default=None,
        help="Repo name to record in the smoke-test manifest. Defaults to the current git repo name.",
    )
    parser.add_argument(
        "--branch",
        default=None,
        help="Branch name to record in the manifest. Defaults to the current git branch.",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Session identifier to record in the manifest. Defaults to a generated UUID.",
    )
    return parser.parse_args()


def git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def detect_repo_name(explicit: str | None) -> str:
    if explicit:
        return slugify_repo_name(explicit)
    return slugify_repo_name(Path(git_output("rev-parse", "--show-toplevel")).name)


def detect_branch(explicit: str | None) -> str:
    if explicit:
        return explicit
    return git_output("rev-parse", "--abbrev-ref", "HEAD")


def detect_commit() -> str:
    return git_output("rev-parse", "HEAD")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def slugify_repo_name(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "repo"


def build_smoke_bundle(temp_dir: Path, repo_name: str, branch: str, commit: str, session_id: str) -> SmokeBundle:
    bundle_root = temp_dir / "bundle"
    bundle_root.mkdir(parents=True, exist_ok=True)

    file_path = bundle_root / "knowledge" / "org" / "smoke-test.md"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_body = """---
id: smoke-test-memory
type: canonical
scope: org
status: active
owner: cross-repo-coordinator
source:
  - scripts/smoke_test_central_memory_backend.py
supersedes: null
---

# Smoke test memory

This note exists only to verify the backend write/read flow.
"""
    file_path.write_text(file_body, encoding="utf-8")
    file_bytes = file_path.read_bytes()
    file_sha256 = sha256_bytes(file_bytes)
    file_size_bytes = len(file_bytes)

    manifest = {
        "schema_version": "1",
        "repo": {
            "name": repo_name,
            "scope": "repo",
            "branch": branch,
            "commit": commit,
        },
        "source": {
            "agent": "memory-curator",
            "trigger": "Stop",
            "session_id": session_id,
        },
        "bundle": {
            "kind": "full",
            "sha256": "pending",
            "size_bytes": 0,
            "file_count": 1,
        },
        "files": [
            {
                "path": "knowledge/org/smoke-test.md",
                "kind": "canonical",
                "status": "active",
                "sha256": file_sha256,
                "size_bytes": file_size_bytes,
            }
        ],
    }

    manifest_path = bundle_root / "memory-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    bundle_path = temp_dir / "bundle.tar.gz"
    with tarfile.open(bundle_path, mode="w:gz") as archive:
        archive.add(manifest_path, arcname="memory-manifest.json")
        archive.add(file_path, arcname="knowledge/org/smoke-test.md")

    bundle_bytes = bundle_path.read_bytes()
    return SmokeBundle(
        bundle_path=bundle_path,
        bundle_sha256=sha256_bytes(bundle_bytes),
        bundle_size_bytes=len(bundle_bytes),
        file_sha256=file_sha256,
        file_size_bytes=file_size_bytes,
    )


def main() -> int:
    args = parse_args()
    config = BackendConfig.from_environment(args.env_file)
    client = BackendClient(config)

    repo_name = detect_repo_name(args.repo_name)
    branch = detect_branch(args.branch)
    commit = detect_commit()
    session_id = args.session_id or str(uuid.uuid4())

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        bundle = build_smoke_bundle(temp_root, repo_name, branch, commit, session_id)

        create_response = client.create_batch(
            {
                "schema_version": "1",
                "repo": {
                    "name": repo_name,
                    "scope": "repo",
                    "branch": branch,
                    "commit": commit,
                },
                "source": {
                    "agent": "memory-curator",
                    "trigger": "Stop",
                    "session_id": session_id,
                },
                "bundle": {
                    "kind": "full",
                    "sha256": bundle.bundle_sha256,
                    "size_bytes": bundle.bundle_size_bytes,
                    "file_count": 1,
                },
                "files": [
                    {
                        "path": "knowledge/org/smoke-test.md",
                        "kind": "canonical",
                        "status": "active",
                        "sha256": bundle.file_sha256,
                        "size_bytes": bundle.file_size_bytes,
                    }
                ],
            }
        )

        batch_id = str(create_response["batch_id"])
        client.upload_presigned(create_response["upload"], bundle.bundle_path)
        client.update_batch(batch_id, "ready", "smoke test validation passed")
        publish_response = client.publish_batch(batch_id)
        latest_snapshot = client.get_latest_snapshot(repo_name)

        print(
            json.dumps(
                {
                    "batch_id": batch_id,
                    "snapshot_id": publish_response.get("snapshot_id"),
                    "latest_snapshot_id": latest_snapshot.get("snapshot_id"),
                    "repo": repo_name,
                    "branch": branch,
                    "commit": commit,
                    "env_file": str(resolve_env_file(args.env_file)),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
