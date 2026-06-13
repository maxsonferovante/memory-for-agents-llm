#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


DEFAULT_NAMESPACE = "maxsonferovante"
DEFAULT_PLATFORM = "linux/amd64"
TAG_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class ImageSpec:
    repository: str
    context: Path
    dockerfile: Path


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


def validate_tag(tag: str) -> str:
    value = tag.strip()
    if not value:
        raise SystemExit("version is required")
    if not TAG_RE.fullmatch(value):
        raise SystemExit(f"invalid Docker tag: {tag!r}")
    return value


def image_ref(namespace: str, repository: str, tag: str) -> str:
    return f"{namespace}/{repository}:{tag}"


def quote_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def build_command(
    namespace: str,
    image: ImageSpec,
    version: str,
    platform: str,
    push_latest: bool,
) -> list[str]:
    command = [
        "docker",
        "buildx",
        "build",
        "--platform",
        platform,
        "--pull",
        "--file",
        str(image.dockerfile),
        "--tag",
        image_ref(namespace, image.repository, version),
    ]
    if push_latest:
        command.extend(["--tag", image_ref(namespace, image.repository, "latest")])
    command.extend(["--push", str(image.context)])
    return command


def publish_image(
    repo_root: Path,
    namespace: str,
    image: ImageSpec,
    version: str,
    platform: str,
    push_latest: bool,
    dry_run: bool,
) -> None:
    command = build_command(namespace, image, version, platform, push_latest)
    print(quote_command(command))
    if dry_run:
        return
    subprocess.run(command, cwd=repo_root, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and push the local stack images to Docker Hub.")
    parser.add_argument(
        "--namespace",
        default=DEFAULT_NAMESPACE,
        help="Docker Hub namespace/user. Defaults to maxsonferovante.",
    )
    parser.add_argument(
        "--version",
        help="Image tag to publish. Defaults to git describe.",
    )
    parser.add_argument(
        "--platform",
        default=DEFAULT_PLATFORM,
        help="Target platform for buildx. Defaults to linux/amd64.",
    )
    parser.add_argument(
        "--no-latest",
        action="store_true",
        help="Skip publishing the `latest` tag alongside the version tag.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the build and push commands without executing them.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = discover_repo_root()
    version = validate_tag(args.version or git_version(repo_root))
    namespace = validate_tag(args.namespace)
    platform = args.platform.strip()
    if not platform:
        raise SystemExit("platform is required")

    images = [
        ImageSpec(
            repository="memory-for-agents-llm-api",
            context=repo_root / "local_stack" / "api",
            dockerfile=repo_root / "local_stack" / "api" / "Dockerfile",
        ),
        ImageSpec(
            repository="memory-for-agents-llm-worker",
            context=repo_root,
            dockerfile=repo_root / "local_stack" / "worker" / "Dockerfile",
        ),
        ImageSpec(
            repository="memory-for-agents-llm-mcp-server",
            context=repo_root / "local_stack" / "mcp-server",
            dockerfile=repo_root / "local_stack" / "mcp-server" / "Dockerfile",
        ),
    ]

    print(f"version: {version}")
    print(f"namespace: {namespace}")
    print(f"platform: {platform}")
    print(f"push_latest: {not args.no_latest}")
    for image in images:
        publish_image(
            repo_root=repo_root,
            namespace=namespace,
            image=image,
            version=version,
            platform=platform,
            push_latest=not args.no_latest,
            dry_run=args.dry_run,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
