---
id: spec-memory-platform-migration-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---

# Migration plan

## Phase 0: Freeze the principle

- Declare Spec Kit artifacts as the platform boundary.
- Preserve the official Spec Kit command sequence unchanged.
- Stop adding runtime-specific memory behavior unless it maps to the event contract.

## Phase 1: Define contracts

- Publish event envelope and event taxonomy.
- Publish memory scope taxonomy and promotion rules.
- Publish API and MCP contracts.
- Record ADRs for artifact boundary, event write contract, and MCP consumption.

## Phase 2: Convert hooks to event producers

- Map Claude hooks to the shared event envelope.
- Map Codex hooks and commands to the shared event envelope.
- Add GitHub Actions events for PRs, commits, checks, releases, and dependency changes.
- Make hook output deterministic and idempotent.

## Phase 3: Evolve the local stack

- Wrap or rename the ingestion service as the Memory API.
- Add append-only Event Store tables.
- Add Memory Store projections for scoped memory.
- Add replayable processing jobs.
- Extend MCP with spec, ADR, event, and context-pack resources.

## Phase 4: Simplify runtime assets

- Reduce custom agents to optional conveniences with explicit ROI.
- Move durable instructions from runtime files into Spec Kit artifacts, ADRs, and memory docs.
- Keep runtime files focused on adapter setup, hook wiring, and MCP discovery.

## Phase 5: Cross-product rollout

- Promote stable repository memory into product memory.
- Promote cross-product invariants into organizational memory.
- Add deprecation workflows for obsolete memories.
- Add Knowledge Graph edges for specs, decisions, dependencies, tasks, reviews, and lessons.

## Phase 6: Operational hardening

- Add schema versioning and migration tooling.
- Add event replay tests.
- Add authorization and tenancy controls.
- Add observability for event lag, projection freshness, retrieval quality, and MCP errors.
