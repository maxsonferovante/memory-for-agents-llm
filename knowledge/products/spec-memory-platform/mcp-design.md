---
id: prop-spec-memory-platform-mcp-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---


# MCP design

## Problem

The platform needs implementable Spec Kit-first documentation that replaces runtime-centric memory design with artifact, event, memory, and MCP contracts.

## Proposal

## Role

MCP is the official read layer for agent runtimes. Runtimes do not query the database directly and do not own persistent memory.

## Resources

- `memory://org/{org_id}`
- `memory://product/{product_id}`
- `memory://repo/{repo_id}`
- `memory://spec/{spec_id}`
- `memory://adr/{adr_id}`

## Tools

- `search_memory(query, scope, limit)`
- `build_context_pack(task, scope, budget)`
- `get_spec_context(spec_id)`
- `list_recent_events(scope, event_types)`
- `explain_memory(memory_id)`

## Access policy

MCP tools are read-only by default. Writes go through Event Capture and Memory API endpoints. Runtime identity is used for audit and authorization, not schema branching.

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
