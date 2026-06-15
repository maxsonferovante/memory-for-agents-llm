---
id: prop-adr-spec-memory-event-contract-v1
type: proposal
scope: product
status: promoted
owner: spec-memory-platform
target_path: knowledge/adr/spec-memory-event-contract.md
supersedes: null
confidence: high
promoted_to: knowledge/adr/spec-memory-event-contract.md
promoted_at: 2026-06-15
---


# ADR: Use events as the memory write contract

## Problem

The platform needs implementable Spec Kit-first documentation that replaces runtime-centric memory design with artifact, event, memory, and MCP contracts.

## Proposal

## Status

Proposed

## Context

Hooks, skills, commands, pull requests, commits, and CI can all produce useful knowledge. Without a shared contract, each runtime creates incompatible memory semantics.

## Decision

Make structured events the only write contract for durable memory. The Memory API persists append-only events, and memory is derived from those events through replayable processing.

## Alternatives considered

- Let each runtime write directly to Markdown memory.
- Let runtimes write directly to the database.

## Consequences

- Event schema validation becomes mandatory.
- Idempotency and provenance are handled centrally.
- Memory projections can be rebuilt after schema or processing changes.

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
