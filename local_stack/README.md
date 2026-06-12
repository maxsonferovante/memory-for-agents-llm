# Local memory stack

This directory contains the minimal fully-local implementation for the memory architecture:

- `api/`: Rust ingestion API ported from the central-memory backend prototype.
- `postgres` service: local PostgreSQL metadata store.
- `worker/`: asynchronous indexer that derives structured memory, chunks, and embeddings.
- `mcp-server/`: Rust MCP server that reads the derived index and exposes search/resources.

## Services

- `POST /v1/events` on the API accepts hook events.
- Raw payloads land under `/data/raw`.
- PostgreSQL metadata lives in the `memory` database.
- Derived index data is exported to `/data/derived/index.json`.
- The MCP server reads that derived index with the official Rust MCP SDK.

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
    "source": "claude-code-hook",
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

## Notes

- Markdown stays canonical.
- Raw storage is append-only.
- PostgreSQL is the metadata store.
- The worker can switch to an open-source embedding backend later by replacing the `hash` embedder.
