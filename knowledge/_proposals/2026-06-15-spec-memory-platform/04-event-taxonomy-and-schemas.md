---
id: prop-spec-memory-platform-events-v1
type: proposal
scope: product
status: promoted
owner: spec-memory-platform
target_path: knowledge/products/spec-memory-platform/event-taxonomy-and-schemas.md
supersedes: null
confidence: high
promoted_to: knowledge/products/spec-memory-platform/event-taxonomy-and-schemas.md
promoted_at: 2026-06-15
---


# Event taxonomy and schemas

## Problem

The platform needs implementable Spec Kit-first documentation that replaces runtime-centric memory design with artifact, event, memory, and MCP contracts.

## Proposal

## Event envelope

All producers emit `event_id`, `event_type`, `schema_version`, `occurred_at`, `producer`, `scope`, `actor`, `artifact`, `correlation`, `payload`, and `provenance`.

## Required event types

### Constitution

- `constitution.created`
- `constitution.updated`

### Specification

- `spec.created`
- `spec.updated`
- `requirement.created`
- `requirement.updated`

### Clarification

- `clarification.requested`
- `clarification.resolved`

### Planning

- `plan.created`
- `architecture.decision.created`
- `dependency.selected`

### Tasks

- `tasks.generated`
- `task.created`
- `task.completed`

### Analysis

- `analysis.completed`
- `inconsistency.detected`

### Implementation

- `implementation.started`
- `implementation.completed`

### Review

- `review.completed`

### Retrospective

- `lesson.learned`
- `improvement.suggested`

### Memory

- `memory.created`
- `memory.updated`
- `memory.deprecated`
- `memory.consolidated`

## Payload conventions

Payloads describe Spec Kit artifacts, decisions, and evidence, not runtime transcripts. Runtime details stay in producer metadata. Event IDs should be deterministic for reprocessed Git, PR, or CI evidence.

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
