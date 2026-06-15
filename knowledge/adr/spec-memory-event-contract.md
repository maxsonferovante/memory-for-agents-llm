---
id: adr-spec-memory-event-contract-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---

# ADR: Use events as the memory write contract

## Status

Accepted

## Context

Hooks, skills, commands, pull requests, commits, and CI can all produce useful knowledge. Without one shared write contract, each runtime creates incompatible memory semantics and bypasses governance.

## Decision

Make structured events the only write contract for durable memory. The Memory API persists append-only events, validates schema and scope, enforces idempotency, and records provenance. Memory is derived from events through replayable processing.

## Consequences

- Event schema validation becomes mandatory.
- Runtime adapters remain thin translation layers.
- Idempotency and provenance are handled centrally.
- Memory projections can be rebuilt after schema or processing changes.
- Direct writes from runtimes to durable memory stores are not allowed.

## Alternatives considered

- Let each runtime write directly to Markdown memory. This is simple but creates drift and weak auditability.
- Let runtimes write directly to the database. This bypasses validation and couples runtimes to storage.
