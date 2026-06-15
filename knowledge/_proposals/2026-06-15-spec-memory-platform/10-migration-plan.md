---
id: prop-spec-memory-platform-migration-v1
type: proposal
scope: product
status: promoted
owner: spec-memory-platform
target_path: knowledge/products/spec-memory-platform/migration-plan.md
supersedes: null
confidence: high
promoted_to: knowledge/products/spec-memory-platform/migration-plan.md
promoted_at: 2026-06-15
---


# Migration plan

## Problem

The platform needs implementable Spec Kit-first documentation that replaces runtime-centric memory design with artifact, event, memory, and MCP contracts.

## Proposal

## Phase 0: Freeze the principle

Declare Spec Kit artifacts as the platform boundary and stop adding runtime-specific memory features unless they map to events.

## Phase 1: Define contracts

Publish the event envelope, event taxonomy, memory scopes, promotion rules, MCP resources, MCP tools, and ADRs.

## Phase 2: Convert hooks to event producers

Map Claude and Codex lifecycle hooks to the shared event schema. Add GitHub Actions events for pull requests, commits, CI, and releases.

## Phase 3: Evolve the local stack

Wrap or rename ingestion as the Memory API, add append-only Event Store tables, add derived Memory Store projections, add replayable processing jobs, and extend MCP.

## Phase 4: Simplify runtime assets

Reduce Claude and Codex agents to optional conveniences. Move durable instructions into Spec Kit docs, ADRs, and memory taxonomy.

## Phase 5: Cross-product rollout

Promote stable repository memory into product memory, promote cross-product invariants into organizational memory, and add Knowledge Graph edges.

## Phase 6: Operational hardening

Add schema versioning, migration tools, event replay tests, authorization, tenancy controls, and observability.

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
