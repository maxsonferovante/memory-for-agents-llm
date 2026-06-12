---
id: structured-memory-mcp-roadmap-v1
type: canonical
scope: product
status: active
owner: cross-repo-coordinator
source:
  - ../../../knowledge/_proposals/2026-06-11-structured-memory-mcp/01-structured-memory-mcp-adr.md
  - ../../../knowledge/org/memory-governance.md
  - ../../../knowledge/org/context-pack-contract.md
supersedes: null
---

# Structured memory and MCP roadmap ADR

## Decision

Evolve the central memory system in three layers instead of replacing the Markdown knowledge base with RAG:

1. Capture reliable events from Claude Code hooks into raw storage and metadata.
2. Derive structured memory records and vector chunks through an asynchronous processor/indexer.
3. Expose retrieval through an MCP server for Claude Code and other agents.

Canonical Markdown remains the versioned source of truth. Raw stores, metadata stores, structured databases, vector databases, and MCP resources are derived layers for distribution and retrieval.

## Architecture

```txt
Claude Code hooks
   ↓
Memory Backend API
   ↓
Raw Storage + Metadata DB
   ↓
Processor/Indexer
   ↓
Structured Memory DB + Vector DB
   ↓
MCP Server
   ↓
Claude Code / Agents
```

## Context

The repository already separates memory by organization, product, domain, repo, spec, ADR, runbook, glossary, and proposal scope. The local stack publishes immutable snapshots, which is a good first retrieval layer, but agents eventually need richer queries such as decisions by product, lessons by repo, and cross-repo concept comparison.

## Rationale

- Markdown remains reviewable, source-backed, and versioned in Git.
- Raw capture preserves provenance before summarization, chunking, or embedding can lose context.
- Structured memory makes status, supersession, scope, ownership, and source files queryable.
- Vector memory improves recall but stays tied to structured items and source files.
- MCP is the agent consumption boundary, not the authoritative persistence layer.

## Deployment options

- Local: filesystem raw storage and SQLite or Postgres metadata.
- Vector retrieval may use any local or remote provider, as long as embeddings remain rebuildable from canonical and raw sources.

## Alternatives rejected

- Directly treating a vector database as canonical memory.
- Adding semantic search before reliable event capture and metadata.
- Exposing raw snapshots over MCP without structured filtering.

## Consequences

- The roadmap stays incremental: capture first, index second, MCP consumption third.
- Search indexes can be rebuilt after schema, embedding model, or provider changes.
- Agents get a stable retrieval surface without bypassing memory governance.
- The local stack remains compatible with the existing append-only snapshot contract.
