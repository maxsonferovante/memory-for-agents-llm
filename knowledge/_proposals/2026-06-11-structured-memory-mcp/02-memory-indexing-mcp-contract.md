---
id: prop-memory-indexing-mcp-contract-v1
type: proposal
scope: integration
status: promoted
owner: cross-repo-coordinator
target_path: knowledge/integrations/memory-indexing-and-mcp.md
supersedes: null
confidence: high
---

# Memory indexing and MCP contract candidate

## Problem

Agents need richer retrieval than latest-snapshot reads, but the system must avoid turning embeddings or MCP resources into unreviewed canonical memory.

## Proposal

Define a three-phase contract for reliable capture, derived indexing, and MCP reads.

### Phase 1: reliable capture

Hooks or agents send memory events to the backend after memory-producing actions.

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

AWS deployment may use API Gateway, Lambda, S3 raw files, and DynamoDB metadata. Local deployment may use FastAPI, a filesystem `raw/` directory, and SQLite or Postgres metadata.

### Phase 2: processing and indexing

The processor derives two retrieval models from raw events and canonical Markdown.

#### Structured memory records

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

#### Vector memory chunks

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

The structured record is the retrieval control plane. The vector chunk is a recall aid and must point back to a structured item and source file.

### Phase 3: MCP consumption

The MCP server exposes memory to Claude Code and other agents through a bounded read surface.

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

Prompts should guide agents to consult MCP memory before broad repo exploration when a task depends on prior decisions, cross-repo invariants, or repeated lessons.

## Consequences

- Agents get richer retrieval without bypassing canonical Markdown review.
- Indexers gain enough metadata to rebuild structured and vector stores from raw and canonical sources.
- MCP servers can expose memory through stable tools and resources while persistence remains outside MCP.

## Rules

- Markdown remains the official authored memory.
- Raw storage is append-only from the ingestion perspective.
- Metadata must preserve repo, branch, commit, source file, content hash, session, and source actor.
- Indexers may summarize, chunk, and embed, but must retain source pointers.
- Search results must return provenance with enough detail for an agent to cite or open the source file.
- MCP writes, if added later, must create proposals instead of mutating canonical files directly.

## Sources

- [knowledge/integrations/central-memory-backend.md](../../../knowledge/integrations/central-memory-backend.md)
- [knowledge/adr/central-memory-backend.md](../../../knowledge/adr/central-memory-backend.md)
- [hooks/README.md](../../../hooks/README.md)
- [knowledge/org/memory-curation-flow.md](../../../knowledge/org/memory-curation-flow.md)
- [knowledge/org/cross-repo-sharing-policy.md](../../../knowledge/org/cross-repo-sharing-policy.md)
- [AWS OpenSearch Serverless vector search documentation](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless-vector-search.html)
- [Model Context Protocol specification](https://modelcontextprotocol.io/specification/2025-03-26)

## Acceptance criteria

- Event capture is defined before embeddings.
- Structured memory and vector memory have separate schemas.
- Every chunk links back to a structured memory item and source file.
- MCP tools and resources are named and scoped.
- The contract forbids replacing canonical Markdown with vector storage.
