---
id: prop-adr-spec-memory-mcp-consumption-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---


# ADR: Make MCP the official context consumption layer

## Problem

The platform needs implementable Spec Kit-first documentation that replaces runtime-centric memory design with artifact, event, memory, and MCP contracts.

## Proposal

## Status

Proposed

## Context

Claude Code, Codex, Copilot, and future agents need the same memory without sharing database credentials or runtime-specific retrieval logic.

## Decision

Expose memory and context retrieval through MCP. Agent runtimes consume MCP resources and tools; they do not query the database directly.

## Alternatives considered

- Embed retrieval logic in every runtime adapter.
- Use only Markdown files as runtime context.

## Consequences

- MCP server behavior becomes part of the platform contract.
- The Memory API remains the write path, while MCP is read-oriented by default.
- Future runtimes can integrate by implementing MCP consumption and event production.

## Consequences

- Implementers get a concrete target contract.
- Runtime-specific code can be simplified into adapters.
- Memory remains derived from structured evidence rather than raw conversations.

## Sources

- [AGENTS.md](../../../AGENTS.md)
- [README.md](../../../README.md)
- [hooks/memory_hooks.py](../../../hooks/memory_hooks.py)
- [knowledge/org/knowledge-scope-model.md](../../../knowledge/org/knowledge-scope-model.md)

## Acceptance criteria

- The document is runtime-agnostic.
- The document keeps Spec Kit artifacts as the process source of truth.
- The document defines a clear migration or implementation contract.
