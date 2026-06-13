---
id: prop-local-memory-compose-proxy-routing-adr-v1
type: proposal
scope: repo
status: promoted
owner: memory-curator
source:
  - ../../../docker-compose.yml
  - ../../../local_stack/proxy/nginx.conf
  - ../../../.codex/config.toml
  - ../../../scripts/install_codex_assets.py
  - ../../../scripts/install_claude_assets.py
  - ../../../hooks/memory_event_poster.py
  - ../../../scripts/smoke_test_local_memory_stack.py
  - ../../../local_stack/README.md
target_path: knowledge/adr/local-memory-compose-proxy-routing.md
supersedes: null
confidence: high
promoted_to: knowledge/adr/local-memory-compose-proxy-routing.md
promoted_at: 2026-06-13
---


# Local memory compose proxy routing ADR candidate

## Problem

The local memory stack now has two externally consumed surfaces: ingestion over HTTP and MCP over HTTP. Without one stable public entrypoint, Codex config, Claude installation, hook posting, and smoke validation would each need to know internal service ports and the stack would expose more moving pieces than necessary.

## Proposal

Standardize Docker Compose proxy routing as the public access contract for the repo-local memory stack.

- Docker Compose must expose only the `proxy` service on `127.0.0.1:8080` for normal client access.
- The proxy must route `/api/...` to the ingestion API on `api:8081`, rewriting away the `/api/` prefix before forwarding.
- The proxy must route `/mcp` to `mcp-server:8082` and keep MCP-friendly transport settings such as disabled buffering and long read and send timeouts.
- Repo-scoped Codex config, installer defaults, hook posting, and the local smoke test must target the proxy URLs `http://127.0.0.1:8080/mcp` and `http://127.0.0.1:8080/api/...` instead of addressing backend containers directly.
- The API and MCP server may keep their internal bind ports, but those ports are implementation details rather than the client contract.

## Consequences

- Local clients get one stable base endpoint for both ingestion and MCP access.
- Internal port changes on `api` or `mcp-server` can remain isolated behind the proxy as long as the public proxy contract stays intact.
- The stack depends on Nginx proxy behavior for both hook ingestion and MCP transport, so proxy configuration becomes part of runtime correctness and smoke coverage.
- Documentation and installers can describe one local entrypoint instead of separate external host ports for each service.

## Sources

- [docker-compose.yml](../../../docker-compose.yml)
- [local_stack/proxy/nginx.conf](../../../local_stack/proxy/nginx.conf)
- [.codex/config.toml](../../../.codex/config.toml)
- [scripts/install_codex_assets.py](../../../scripts/install_codex_assets.py)
- [scripts/install_claude_assets.py](../../../scripts/install_claude_assets.py)
- [hooks/memory_event_poster.py](../../../hooks/memory_event_poster.py)
- [scripts/smoke_test_local_memory_stack.py](../../../scripts/smoke_test_local_memory_stack.py)
- [local_stack/README.md](../../../local_stack/README.md)

## Acceptance criteria

- The decision states that the public local stack contract is the proxy at `127.0.0.1:8080`, not direct client access to backend service ports.
- The decision states that `/api/...` forwards to `api:8081` with prefix rewriting and `/mcp` forwards to `mcp-server:8082`.
- The decision states that Codex, Claude installer defaults, hook posting, and smoke validation all target the proxy URLs.
- The decision states that backend bind ports remain internal implementation details.
