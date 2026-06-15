---
id: adr-spec-memory-mcp-consumption-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---

# ADR: Make MCP the official context consumption layer

## Status

Accepted

## Context

Claude Code, Codex, Copilot, and future agents need the same memory without sharing database credentials, vector-index details, or runtime-specific retrieval logic.

## Decision

Expose memory and context retrieval through MCP. Agent runtimes consume MCP resources and tools. They do not query the database or projection stores directly.

## Consequences

- MCP server behavior becomes part of the platform contract.
- The Memory API remains the write path, while MCP is read-oriented by default.
- Future runtimes can integrate by implementing event production and MCP consumption.
- Retrieval responses must include provenance, confidence, and deprecation signals.

## Alternatives considered

- Embed retrieval logic in every runtime adapter. This duplicates behavior and makes replacement harder.
- Use only Markdown files as runtime context. This remains reviewable but is insufficient for scoped retrieval and graph-backed context.
