---
id: prop-local-stack-postgres-mcp-runtime-adr-v1
type: proposal
scope: repo
status: promoted
owner: memory-curator
source:
  - ../../../local_stack/mcp-server/src/main.rs
  - ../../../local_stack/storage.py
  - ../../../local_stack/worker.py
  - ../../../scripts/install_codex_assets.py
  - ../../../scripts/install_claude_assets.py
  - ../../../scripts/smoke_test_local_memory_stack.py
  - ../../../docker-compose.yml
target_path: knowledge/adr/local-stack-postgres-mcp-runtime.md
supersedes: null
confidence: high
promoted_to: knowledge/adr/local-stack-postgres-mcp-runtime.md
promoted_at: 2026-06-12
---


# Local stack Postgres MCP runtime ADR candidate

## Problem

The repo-local memory stack previously depended on a derived `index.json` snapshot for MCP reads. That duplicated the structured memory data already stored in Postgres, created drift risk between the worker and the MCP server, and forced local installers and client configs to carry `MEMORY_INDEX_PATH` even after the runtime moved to database-backed storage.

## Proposal

Standardize the repo-local `localMemory` runtime on direct Postgres access with `pgvector` as the canonical chunk embedding store.

- The Rust MCP server must require `MEMORY_DATABASE_URL` and query Postgres directly for `search_memory`, `get_memory_item`, `get_repo_context_pack`, `list_resources`, and `read_resource`.
- The worker must persist chunks and embeddings only in the database and must not export or recover through `local_stack/data/derived/index.json`.
- `memory_chunks.embedding` must use native `pgvector` storage so the database remains the only source of truth for vector retrieval.
- Local client installers and example configs must register `localMemory` with `MEMORY_DATABASE_URL` instead of `MEMORY_INDEX_PATH`.
- The first implementation may keep deterministic hash embeddings and MCP-side lexical plus vector scoring, as long as the storage and retrieval boundary stays database-backed.

## Consequences

- The local stack removes a stale file-sync boundary and keeps structured memory plus chunk embeddings in one place.
- MCP runtime health now depends on a live Postgres connection instead of a file snapshot, so connection failures become operationally visible.
- Search behavior stays compatible enough for the current stack because the query embedding and ranking heuristic remain stable while the storage layer changes.
- Future upgrades to real embeddings or SQL-native similarity can happen without reintroducing a file-backed retrieval surface.

## Sources

- [local_stack/mcp-server/src/main.rs](../../../local_stack/mcp-server/src/main.rs)
- [local_stack/storage.py](../../../local_stack/storage.py)
- [local_stack/worker.py](../../../local_stack/worker.py)
- [scripts/install_codex_assets.py](../../../scripts/install_codex_assets.py)
- [scripts/install_claude_assets.py](../../../scripts/install_claude_assets.py)
- [scripts/smoke_test_local_memory_stack.py](../../../scripts/smoke_test_local_memory_stack.py)
- [docker-compose.yml](../../../docker-compose.yml)

## Acceptance criteria

- The decision states that `MEMORY_DATABASE_URL` replaces `MEMORY_INDEX_PATH` for the MCP runtime contract.
- The decision states that the worker persists embeddings only in Postgres and no longer exports `index.json`.
- The decision states that `pgvector` is the canonical chunk embedding storage for the local stack.
- The decision keeps the MCP server as a retrieval surface, not the authoritative persistence layer.
