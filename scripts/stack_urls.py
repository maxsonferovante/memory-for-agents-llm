from __future__ import annotations

from dataclasses import dataclass


DEFAULT_STACK_PORT = 8080


@dataclass(frozen=True)
class StackUrls:
    base_url: str
    ingest_url: str
    mcp_url: str


def normalize_stack_host(stack_host: str) -> str:
    host = stack_host.strip()
    if not host:
        raise SystemExit("stack host is required")
    if any(separator in host for separator in ("//", "/", "?", "#")):
        raise SystemExit(f"invalid stack host: {stack_host!r}")
    if ":" in host:
        raise SystemExit("stack host must not include a port; pass only the host or IP")
    return host


def build_stack_urls(stack_host: str, port: int = DEFAULT_STACK_PORT) -> StackUrls:
    host = normalize_stack_host(stack_host)
    base_url = f"http://{host}:{port}"
    return StackUrls(
        base_url=base_url,
        ingest_url=f"{base_url}/api/v1/events",
        mcp_url=f"{base_url}/mcp",
    )
