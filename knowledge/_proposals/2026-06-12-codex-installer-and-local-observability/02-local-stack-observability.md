---
id: prop-local-stack-observability-v1
type: proposal
scope: repo
status: promoted
owner: memory-curator
target_path: knowledge/repos/memory-for-agents-llm/local-stack-observability.md
supersedes: null
confidence: high
promoted_to: knowledge/repos/memory-for-agents-llm/local-stack-observability.md
promoted_at: 2026-06-12
---


# Local stack observability baseline candidate

## Problem

The local memory stack is intended to be runnable and debuggable by maintainers, but the API, worker, and MCP layers did not expose enough runtime logs to follow startup state, ingestion, indexing, or retrieval flow from the terminal alone.

## Proposal

Define a minimum observability baseline for the repo-local `local_stack/`.

### API logging baseline

- Log startup configuration at `info` level with bind address, data directories, and a sanitized database target.
- Log each ingest request with event id, event type, repo, scope, source, and content size.
- Log queueing success and list endpoints with returned item counts.

### Worker logging baseline

- Log bootstrap retries while the database is not ready.
- Log worker startup settings that affect indexing behavior.
- Log event indexing, chunk counts, index export, successful processing, and failures.

### MCP logging baseline

- Initialize `tracing` in the Rust MCP binary with a usable default filter even when `RUST_LOG` is absent.
- Log index loads and the entry or exit of major MCP surfaces: `search_memory`, `get_memory_item`, `get_repo_context_pack`, `list_resources`, and `read_resource`.

### Noise control

- Keep the default runtime level at `info`.
- Reserve repetitive idle-state messages for `debug`.
- Avoid logging raw memory content or unsanitized credentials.

## Consequences

- Maintainers can follow a local ingest-to-index-to-MCP flow from terminal output.
- Runtime issues become easier to localize without increasing the trust boundary of the stack.
- Observability becomes part of the repo-local implementation contract instead of an ad hoc debugging aid.

## Sources

- [local_stack/api/src/main.rs](../../../local_stack/api/src/main.rs)
- [local_stack/mcp-server/src/main.rs](../../../local_stack/mcp-server/src/main.rs)
- [local_stack/mcp-server/Cargo.toml](../../../local_stack/mcp-server/Cargo.toml)
- [local_stack/worker.py](../../../local_stack/worker.py)
- [local_stack/README.md](../../../local_stack/README.md)

## Acceptance criteria

- The proposal covers API, worker, and MCP runtime surfaces.
- It distinguishes `info` from `debug` logging expectations.
- It explicitly forbids logging sensitive values or raw memory content by default.
