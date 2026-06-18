# Local memory stack

This directory contains the minimal fully-local implementation for the memory architecture. It is shared by Claude Code, Codex, and future agent clients:

- `api/`: Rust ingestion API ported from the central-memory backend prototype.
- `postgres` service: local PostgreSQL metadata store.
- `worker/`: asynchronous indexer that derives structured memory, chunks, and embeddings.
- `mcp-server/`: Rust MCP server that reads PostgreSQL directly and exposes search/resources over HTTP.

The published Docker Compose contract pulls the runtime images from Docker Hub. The repo keeps a `docker-compose.override.yml` file so `docker compose up --build` still rebuilds the same services from source during local development.

## Services

- `POST /api/v1/events` on the proxy aceita hook events e os encaminha para a API.
- Raw payloads land under `/data/raw`.
- PostgreSQL metadata, chunks, and embeddings live in the `memory` database.
- The worker stores embeddings in `pgvector` columns on `memory_chunks`.
- The MCP server reads PostgreSQL directly with the official Rust MCP SDK and is exposed by Docker Compose through the proxy at `http://127.0.0.1:8080/mcp`.

## Example event

```bash
curl -sS http://localhost:8080/api/v1/events \
  -H 'content-type: application/json' \
  -d '{
    "event_type": "session_stop",
    "repo": "memory-for-agents-llm",
    "branch": "feature/local-stack",
    "commit_sha": "abc123",
    "file_path": "knowledge/repos/example.md",
    "scope": "repo",
    "source": "codex-code-hook",
    "session_id": "019abcdef",
    "created_at": "2026-06-11T12:00:00Z",
    "content": "# Example\\n\\n## Context\\n\\nThis is a test note."
  }'
```

## Run

```bash
docker compose up --build
curl http://localhost:8080/api/healthz
curl http://localhost:8080/api/v1/items
curl -i http://localhost:8080/mcp
python3 scripts/smoke_test_local_memory_stack.py
```

## VPS Deploy

To run the published images on the x86_64 VPS, use the base compose file only so Docker Compose does not auto-load `docker-compose.override.yml`, and pin the image tag if needed:

```bash
MEMORY_IMAGE_TAG=0.4.0 docker compose -f docker-compose.yml pull
MEMORY_IMAGE_TAG=0.4.0 docker compose -f docker-compose.yml up -d
```

Use `latest` if you want the moving release alias instead of a pinned version tag.

## Codex MCP consumption

The repo-scoped Codex config registers `localMemory` as a remote MCP server. The global installer writes an equivalent user-level `~/.codex/config.toml` entry:

```toml
[mcp_servers.localMemory]
url = "http://127.0.0.1:8080/mcp"
```

After `docker compose up --build`, the proxy is reachable at `127.0.0.1:8080`, routing `/api/...` to the ingestion API and `/mcp` to the MCP server. The MCP server still connects internally to the local Postgres service and exposes memory search, item reads, and repo context packs to Codex custom agents.

## Notes

- Markdown stays canonical.
- Raw storage is append-only.
- PostgreSQL is the metadata store.
- The worker can switch to an open-source embedding backend later by replacing the `hash` embedder.
