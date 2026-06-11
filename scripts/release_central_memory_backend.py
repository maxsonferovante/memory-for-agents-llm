#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def capture(cmd: list[str], cwd: Path) -> str:
    completed = subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.PIPE, text=True)
    return completed.stdout


def terraform_var_args(args: argparse.Namespace, lambda_zip_path: Path) -> list[str]:
    terraform_args = [
        f"-var=aws_region={args.aws_region}",
        f"-var=lambda_zip_path={lambda_zip_path}",
        f"-var=api_key_value={args.api_key_value}",
        f"-var=usage_plan_rate_limit={args.usage_plan_rate_limit}",
        f"-var=usage_plan_burst_limit={args.usage_plan_burst_limit}",
    ]
    if args.backend_auth_token is not None:
        terraform_args.append(f"-var=backend_auth_token={args.backend_auth_token}")
    return terraform_args


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and release the self-hosted central memory backend into AWS."
    )
    parser.add_argument(
        "--aws-region",
        default=os.environ.get("AWS_REGION"),
        help="AWS region for the release. Defaults to AWS_REGION.",
    )
    parser.add_argument(
        "--api-key-value",
        default=os.environ.get("API_KEY_VALUE"),
        help="API key value used by API Gateway. Defaults to API_KEY_VALUE.",
    )
    parser.add_argument(
        "--usage-plan-rate-limit",
        type=float,
        default=10,
        help="Steady-state requests per second allowed by the usage plan.",
    )
    parser.add_argument(
        "--usage-plan-burst-limit",
        type=int,
        default=20,
        help="Burst requests allowed by the usage plan.",
    )
    parser.add_argument(
        "--backend-auth-token",
        default=os.environ.get("BACKEND_AUTH_TOKEN"),
        help="Optional bearer token passed to the Lambda. Defaults to BACKEND_AUTH_TOKEN.",
    )
    parser.add_argument(
        "--terraform-dir",
        default="infra/terraform/central-memory-backend",
        help="Path to the Terraform stack.",
    )
    parser.add_argument(
        "--build-output-dir",
        default="dist/backend/central-memory-backend",
        help="Where to place the Lambda zip artifact.",
    )
    parser.add_argument(
        "--env-file",
        default="dist/backend/central-memory-backend/backend.env",
        help="Where to write sourceable backend config after apply.",
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Apply the Terraform plan without an interactive confirmation prompt.",
    )
    return parser.parse_args()


def require(value: str | None, name: str) -> str:
    if not value:
        raise SystemExit(f"{name} is required")
    return value


def write_env_file(
    env_file: Path,
    api_base_url: str,
    api_key_value: str,
    aws_region: str,
    usage_plan_rate_limit: float,
    usage_plan_burst_limit: int,
    backend_auth_token: str | None,
) -> None:
    env_file.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f'API_BASE_URL="{api_base_url}"',
        f'API_KEY_VALUE="{api_key_value}"',
        'API_KEY_HEADER="x-api-key"',
        f'AWS_REGION="{aws_region}"',
        f'API_USAGE_PLAN_RATE_LIMIT="{usage_plan_rate_limit}"',
        f'API_USAGE_PLAN_BURST_LIMIT="{usage_plan_burst_limit}"',
    ]
    if backend_auth_token is not None:
        lines.append(f'BACKEND_AUTH_TOKEN="{backend_auth_token}"')
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_release_summary(
    api_base_url: str,
    bucket_name: str,
    api_key_name: str,
    env_file: Path,
    aws_region: str,
    usage_plan_rate_limit: float,
    usage_plan_burst_limit: int,
) -> None:
    print("\n=== Backend release complete ===")
    print(f"API base URL        : {api_base_url}")
    print(f"Bucket name         : {bucket_name}")
    print(f"API key name        : {api_key_name}")
    print(f"AWS region          : {aws_region}")
    print(f"Rate limit (rps)    : {usage_plan_rate_limit}")
    print(f"Burst limit         : {usage_plan_burst_limit}")
    print(f"Env file            : {env_file}")
    print("\nCopy/paste:")
    print(f'source "{env_file}"')
    print('printf \'%s\\n\' "$API_BASE_URL" "$API_KEY_HEADER"')


def main() -> int:
    args = parse_args()
    aws_region = require(args.aws_region, "AWS region")
    api_key_value = require(args.api_key_value, "API key value")

    root = repo_root()
    build_script = root / "scripts" / "build_central_memory_backend.py"
    terraform_dir = (root / args.terraform_dir).resolve()
    env_file = (root / args.env_file).resolve()

    run([sys.executable, str(build_script), "--target-dir", args.build_output_dir], root)

    lambda_zip_path = (root / args.build_output_dir / "bootstrap.zip").resolve()
    if not lambda_zip_path.exists():
        raise SystemExit(f"expected build artifact not found: {lambda_zip_path}")

    run(["terraform", "init"], terraform_dir)
    terraform_args = terraform_var_args(args, lambda_zip_path)
    run(["terraform", "plan", *terraform_args], terraform_dir)

    if not args.auto_approve:
        print("plan completed; rerun with --auto-approve to apply the release", file=sys.stderr)
        return 0

    run(["terraform", "apply", "-auto-approve", *terraform_args], terraform_dir)

    outputs_raw = capture(["terraform", "output", "-json"], terraform_dir)
    outputs = json.loads(outputs_raw)

    api_base_url = outputs["api_base_url"]["value"]
    write_env_file(
        env_file=env_file,
        api_base_url=api_base_url,
        api_key_value=api_key_value,
        aws_region=aws_region,
        usage_plan_rate_limit=args.usage_plan_rate_limit,
        usage_plan_burst_limit=args.usage_plan_burst_limit,
        backend_auth_token=args.backend_auth_token,
    )

    print_release_summary(
        api_base_url=api_base_url,
        bucket_name=outputs["bucket_name"]["value"],
        api_key_name=outputs["api_key_name"]["value"],
        env_file=env_file,
        aws_region=aws_region,
        usage_plan_rate_limit=args.usage_plan_rate_limit,
        usage_plan_burst_limit=args.usage_plan_burst_limit,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
