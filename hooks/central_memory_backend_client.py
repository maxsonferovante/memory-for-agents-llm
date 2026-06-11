#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import ssl
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib import error as urllib_error
from urllib import request as urllib_request


DEFAULT_ENV_FILE = Path("dist/backend/central-memory-backend/backend.env")


def resolve_env_file(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path).expanduser()
    env_override = os.environ.get("MEMORY_BACKEND_ENV_FILE")
    if env_override:
        return Path(env_override).expanduser()
    return DEFAULT_ENV_FILE


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip()
        value = raw_value.strip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        values[key] = value
    return values


def load_backend_env(path: str | Path | None = None, *, override_existing: bool = False) -> dict[str, str]:
    env_file = resolve_env_file(path)
    values = parse_env_file(env_file)
    if not values:
        return {}
    for key, value in values.items():
        if override_existing or key not in os.environ:
            os.environ[key] = value
    return values


def load_backend_env_if_present() -> dict[str, str]:
    return load_backend_env()


@dataclass(frozen=True)
class BackendConfig:
    api_base_url: str
    api_key_value: str
    api_key_header: str = "x-api-key"
    backend_auth_token: str | None = None
    timeout_seconds: int = 30

    @classmethod
    def from_environment(cls, env_file: str | Path | None = None) -> "BackendConfig":
        load_backend_env(env_file)
        api_base_url = os.environ.get("API_BASE_URL", "").strip()
        api_key_value = os.environ.get("API_KEY_VALUE", "").strip()
        if not api_base_url:
            raise SystemExit("API_BASE_URL is required; source backend.env or set MEMORY_BACKEND_ENV_FILE")
        if not api_key_value:
            raise SystemExit("API_KEY_VALUE is required; source backend.env or set MEMORY_BACKEND_ENV_FILE")
        return cls(
            api_base_url=api_base_url.rstrip("/"),
            api_key_value=api_key_value,
            api_key_header=os.environ.get("API_KEY_HEADER", "x-api-key").strip() or "x-api-key",
            backend_auth_token=os.environ.get("BACKEND_AUTH_TOKEN") or None,
            timeout_seconds=int(os.environ.get("MEMORY_BACKEND_TIMEOUT_SECONDS", "30")),
        )


def _join_url(base_url: str, path: str) -> str:
    base = base_url.rstrip("/")
    encoded_path = quote(path, safe="/")
    suffix = encoded_path if encoded_path.startswith("/") else f"/{encoded_path}"
    return f"{base}{suffix}"


class BackendClient:
    def __init__(self, config: BackendConfig) -> None:
        self.config = config

    def _ssl_context(self) -> ssl.SSLContext:
        context = ssl.create_default_context()
        try:
            import certifi

            context.load_verify_locations(cafile=certifi.where())
        except Exception:
            pass
        return context

    def _headers(self, content_type: str | None = "application/json", extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {
            self.config.api_key_header: self.config.api_key_value,
        }
        if content_type:
            headers["content-type"] = content_type
        if self.config.backend_auth_token:
            headers["authorization"] = f"Bearer {self.config.backend_auth_token}"
        if extra:
            headers.update(extra)
        return headers

    def _request(self, method: str, url: str, *, body: bytes | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any] | str]:
        request = urllib_request.Request(url, data=body, headers=headers or {}, method=method)
        try:
            with urllib_request.urlopen(
                request,
                timeout=self.config.timeout_seconds,
                context=self._ssl_context(),
            ) as response:
                raw = response.read()
                if not raw:
                    return response.status, ""
                text = raw.decode("utf-8")
                try:
                    return response.status, json.loads(text)
                except json.JSONDecodeError:
                    return response.status, text
        except urllib_error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise SystemExit(f"{method} {url} failed: {exc.code} {exc.reason}: {detail}") from exc

    def request_json(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any] | str:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        _, result = self._request(method, _join_url(self.config.api_base_url, path), body=body, headers=self._headers())
        return result

    def upload_presigned(self, upload: dict[str, Any], bundle_path: Path) -> None:
        method = str(upload.get("method", "PUT")).upper()
        if method != "PUT":
            raise SystemExit(f"unsupported presigned upload method: {method}")
        body = bundle_path.read_bytes()
        self._request(method, str(upload["url"]), body=body, headers={"content-type": "application/gzip"})

    def create_batch(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = self.request_json("POST", "/v1/memory-batches", payload)
        if not isinstance(result, dict):
            raise SystemExit("unexpected create batch response")
        return result

    def update_batch(self, batch_id: str, status: str, review_note: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"status": status}
        if review_note is not None:
            payload["review_note"] = review_note
        result = self.request_json("PATCH", f"/v1/memory-batches/{batch_id}", payload)
        if not isinstance(result, dict):
            raise SystemExit("unexpected update batch response")
        return result

    def publish_batch(self, batch_id: str) -> dict[str, Any]:
        result = self.request_json("POST", f"/v1/memory-batches/{batch_id}/publish")
        if not isinstance(result, dict):
            raise SystemExit("unexpected publish response")
        return result

    def get_latest_snapshot(self, repo_id: str) -> dict[str, Any]:
        result = self.request_json("GET", f"/v1/repos/{repo_id}/snapshots/latest", None)
        if not isinstance(result, dict):
            raise SystemExit("unexpected latest snapshot response")
        return result
