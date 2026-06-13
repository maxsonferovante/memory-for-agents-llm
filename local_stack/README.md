# Local memory stack

This directory contains the minimal fully-local implementation for the memory architecture. It is shared by Claude Code, Codex, and future agent clients:

- `api/`: Rust ingestion API ported from the central-memory backend prototype.
- `postgres` service: local PostgreSQL metadata store.
- `worker/`: asynchronous indexer that derives structured memory, chunks, and embeddings.
- `mcp-server/`: Rust MCP server that reads PostgreSQL directly and exposes search/resources.

## Services

- `POST /v1/events` on the API accepts hook events from Claude Code, Codex, or any client that sends the same event envelope.
- Raw payloads land under `/data/raw`.
- PostgreSQL metadata, chunks, and embeddings live in the `memory` database.
- The worker stores embeddings in `pgvector` columns on `memory_chunks`.
- The MCP server reads PostgreSQL directly with the official Rust MCP SDK and can be consumed by Codex through `.codex/config.toml`.

## Example event

```bash
curl -sS http://localhost:8081/v1/events \
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
curl http://localhost:8081/healthz
curl http://localhost:8081/v1/items
python3 scripts/smoke_test_local_memory_stack.py
```

## Codex MCP consumption

The repo-scoped Codex config registers `localMemory` as a STDIO MCP server. The global installer writes an equivalent user-level `~/.codex/config.toml` entry with absolute paths:

```toml
[mcp_servers.localMemory]
command = "cargo"
args = ["run", "--quiet", "--manifest-path", "/absolute/path/to/repo/local_stack/mcp-server/Cargo.toml"]
cwd = "/absolute/path/to/repo"
env = { MEMORY_DATABASE_URL = "postgresql://memory:memory@127.0.0.1:5432/memory", MEMORY_INGEST_API_URL = "http://127.0.0.1:8081/v1/events" }
```

After `docker compose up --build`, the MCP server connects to the local Postgres instance exposed on `127.0.0.1:5432`. The MCP server exposes memory search, item reads, and repo context packs to Codex custom agents.

## Notes

- Markdown stays canonical.
- Raw storage is append-only.
- PostgreSQL is the metadata store.
- The worker can switch to an open-source embedding backend later by replacing the `hash` embedder.
