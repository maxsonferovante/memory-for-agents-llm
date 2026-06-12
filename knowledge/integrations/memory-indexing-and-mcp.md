---
id: memory-indexing-and-mcp-v1
type: canonical
scope: integration
status: active
owner: cross-repo-coordinator
source:
  - ../../../knowledge/_proposals/2026-06-11-structured-memory-mcp/02-memory-indexing-mcp-contract.md
  - ../../../knowledge/adr/structured-memory-mcp-roadmap.md
  - ../../../hooks/README.md
supersedes: null
---

# Memory indexing and MCP contract

## Purpose

Define how memory events, structured indexes, vector indexes, and MCP consumption fit around the canonical Markdown memory base.

## Phase 1: capture reliable events

Hooks and memory-producing agents may send local stack events after session stops, ready proposals, promoted memory, and repo handoffs.

```json
{
  "event_type": "session_stop | proposal_ready | memory_promoted | repo_handoff",
  "repo": "memory-for-agents-llm",
  "branch": "feature/x",
  "commit_sha": "abc123",
  "file_path": "knowledge/repos/example.md",
  "content_hash": "sha256:...",
  "content": "...",
  "scope": "org | product | domain | repo | spec | adr",
  "provenance": {
    "source": "claude-code-hook",
    "session_id": "019...",
    "created_at": "2026-06-11T00:00:00Z"
  }
}
```

Minimum capture requirements:

- Store the raw payload or source document before processing.
- Persist metadata for repo, branch, commit, file path, content hash, scope, source, session, and creation time.
- Keep the write path separate from canonical promotion; event capture must not silently edit Markdown.

## Phase 2: derive structured and vector memory

The processor/indexer parses Markdown and raw events, extracts metadata, creates summaries, chunks content, and optionally embeds chunks.

### Structured memory record

```txt
memory_items
- id
- repo
- product
- domain
- scope
- type: invariant | adr | spec | runbook | lesson | glossary | context_pack
- title
- summary
- source_file
- commit_sha
- content_hash
- status: proposal | canonical | superseded
- supersedes_id
- created_at
- updated_at
```

### Vector memory chunk

```txt
memory_chunks
- chunk_id
- memory_item_id
- repo
- scope
- type
- heading_path
- chunk_text
- embedding
- token_count
- source_file
- provenance
```

Structured records are the retrieval control plane. Vector chunks are recall aids and must always link back to `memory_item_id` and `source_file`.

## Phase 3: expose MCP reads

MCP should expose memory through bounded tools and resources.

Tools:

```txt
search_project_memory(query, repo?, scope?, type?)
get_memory_item(id)
get_repo_context_pack(repo)
get_architecture_decisions(repo/product)
get_recent_session_learnings(repo)
compare_cross_repo_knowledge(concept)
```

Resources:

```txt
memory://org/invariants
memory://repos/{repo}/canonical
memory://products/{product}/context-pack
memory://adr/{id}
memory://specs/{id}
```

Prompts should instruct agents to consult MCP memory before broad repository exploration when the task depends on prior decisions, cross-repo invariants, or repeated lessons.

## Governance rules

- Markdown in `knowledge/` remains the official authored memory.
- Raw storage is append-only from the ingestion perspective.
- Search results must include source file and provenance.
- Summaries and chunks are derived artifacts, not canonical notes.
- MCP write tools, if introduced later, must create proposals under `knowledge/_proposals/` instead of modifying canonical paths directly.

## Implementation notes

- The local path can use FastAPI, filesystem raw storage, and SQLite or Postgres.
- The stack can use any derived retrieval provider, as long as raw storage and canonical Markdown remain the rebuildable source of truth.
- The indexer should be asynchronous so hook latency is not coupled to summarization or embedding latency.
