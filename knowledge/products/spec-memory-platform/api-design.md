---
id: prop-spec-memory-platform-api-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---


# API design

## Problem

The platform needs implementable Spec Kit-first documentation that replaces runtime-centric memory design with artifact, event, memory, and MCP contracts.

## Proposal

## Event Store API

- `POST /events` validates one event envelope, enforces idempotency, and appends the event.
- `POST /events/batch` accepts Git, CI, or migration backfills.
- `GET /events/{event_id}` returns the canonical event and processing status.
- `GET /events?scope=...` returns events by organization, product, repository, spec, feature, artifact, event type, or time range.

## Memory Store API

- `GET /memory/{memory_id}` returns a derived memory item with scope, status, provenance, and supersession links.
- `POST /memory/candidates` creates a candidate memory item.
- `POST /memory/{memory_id}/accept` promotes a candidate into active memory.
- `POST /memory/{memory_id}/deprecate` records replacement guidance.

## Context Retrieval API

- `POST /context/query` retrieves scoped context.
- `POST /context/pack` builds compact task context.
- `GET /context/spec/{spec_id}` returns feature memory, ADRs, tasks, dependency decisions, and lessons.

## Processing API

- `POST /processing/replay` rebuilds projections and indexes from events.
- `GET /processing/status` reports lag, failed events, index health, and projection versions.

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
