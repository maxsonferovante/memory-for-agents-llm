---
id: prop-spec-memory-platform-flows-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---


# Spec Memory Platform flows

## Problem

The platform needs implementable Spec Kit-first documentation that replaces runtime-centric memory design with artifact, event, memory, and MCP contracts.

## Proposal

## Official Spec Kit flow

Every feature follows `/speckit.constitution`, `/speckit.specify`, `/speckit.clarify`, `/speckit.checklist`, `/speckit.plan`, `/speckit.tasks`, `/speckit.analyze`, and `/speckit.implement`.

## Event capture flow

1. Runtime, Git, CI, or PR activity changes or observes a Spec Kit artifact.
2. Adapter emits a structured event with artifact references and provenance.
3. Memory API validates the event envelope and stores it in the Event Store.
4. Processing derives memory candidates and retrieval chunks.
5. Curators or automated policies approve stable memory updates.
6. MCP exposes scoped context back to runtimes.

## Memory consolidation flow

Session and feature events are grouped by spec, repo, product, and decision. Repeated or high-impact facts become candidate repository, product, or organization memory. Accepted candidates are promoted with provenance and supersession links.

## Cross-repository sharing flow

Repository events can propose higher-scope memory. Product or organization owners accept, reject, or narrow the scope, and repo-local notes link to shared memory instead of duplicating it.

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
