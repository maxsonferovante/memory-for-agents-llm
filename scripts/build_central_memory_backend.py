#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import zipfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def write_bootstrap_zip(binary_path: Path, target_zip: Path) -> None:
    target_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        info = zipfile.ZipInfo("bootstrap")
        info.external_attr = 0o755 << 16
        with binary_path.open("rb") as handle:
            archive.writestr(info, handle.read())


def build_with_cargo_lambda(crate_dir: Path) -> Path:
    build_cmd = [
        "cargo",
        "lambda",
        "build",
        "--release",
        "--output-format",
        "zip",
    ]
    run(build_cmd, crate_dir)
    return crate_dir / "target" / "lambda" / "central-memory-backend" / "bootstrap.zip"


def build_with_docker(repo_root: Path, crate_dir: Path) -> Path:
    cargo_home = Path(os.environ.get("CARGO_HOME", Path.home() / ".cargo")).expanduser()
    cargo_home.mkdir(parents=True, exist_ok=True)

    uid = os.getuid()
    gid = os.getgid()
    image = os.environ.get("RUST_DOCKER_IMAGE", "rust:1.95-bookworm")
    container_cmd = "source /usr/local/cargo/env && cargo build --release --target x86_64-unknown-linux-gnu"
    docker_cmd = [
        "docker",
        "run",
        "--rm",
        "--platform",
        "linux/amd64",
        "--user",
        f"{uid}:{gid}",
        "-e",
        "CARGO_HOME=/cargo-home",
        "-v",
        f"{cargo_home}:/cargo-home",
        "-v",
        f"{repo_root}:/work",
        "-w",
        "/work/backend/central-memory-lambda",
        image,
        "bash",
        "-lc",
        container_cmd,
    ]
    run(docker_cmd, repo_root)

    binary_path = crate_dir / "target" / "x86_64-unknown-linux-gnu" / "release" / "central-memory-backend"
    if not binary_path.exists():
        raise SystemExit(f"expected Linux binary not found: {binary_path}")

    target_zip = crate_dir / "target" / "lambda" / "central-memory-backend" / "bootstrap.zip"
    write_bootstrap_zip(binary_path, target_zip)
    return target_zip


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Rust Lambda zip for the central memory backend.")
    parser.add_argument(
        "--release",
        action="store_true",
        default=True,
        help="Build in release mode (default).",
    )
    parser.add_argument(
        "--target-dir",
        default="dist/backend/central-memory-backend",
        help="Where to copy the build artifact.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    crate_dir = root / "backend" / "central-memory-lambda"
    if command_exists("cargo-lambda"):
        source_zip = build_with_cargo_lambda(crate_dir)
    elif command_exists("docker"):
        source_zip = build_with_docker(root, crate_dir)
    else:
        raise SystemExit("need either cargo-lambda or docker to build the Lambda zip")

    if not source_zip.exists():
        raise SystemExit(f"expected build artifact not found: {source_zip}")

    target_dir = (root / args.target_dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    target_zip = target_dir / "bootstrap.zip"
    shutil.copy2(source_zip, target_zip)
    print(target_zip)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
