---
id: central-memory-backend-adr-v1
type: canonical
scope: product
status: active
owner: cross-repo-coordinator
source:
  - ../../../knowledge/_proposals/2026-06-10-central-memory-backend/01-central-memory-backend-adr.md
  - ../../../knowledge/org/memory-governance.md
  - ../../../knowledge/org/agent-memory-cycle.md
  - ../../../knowledge/org/memory-curation-flow.md
  - ../../../knowledge/org/cross-repo-sharing-policy.md
supersedes: null
---

# Central memory backend ADR

## Decision

Use API Gateway, Lambda, and S3 as an append-only snapshot backend for published memory.

## Context

The memory system needs a central place to publish and retrieve snapshots across local sessions and repositories without turning the backend into the authoring source of truth.

## Rationale

- The API gives the orchestrator a controlled write path with validation and state transitions.
- Lambda can validate manifests and finalize batches without exposing the bucket directly.
- S3 gives cheap immutable storage for bundles, manifests, and index pointers.
- Git remains the canonical source for authored memory files.

## Alternatives rejected

- Direct bucket writes without an API.
- A mutable database as the authoritative store.
- Git-only synchronization without a central backend.

## Consequences

- Published memory becomes traceable by repo, session, and bundle hash.
- The backend can be rebuilt or mirrored from release artifacts and Terraform.
- Search, indexing, and graph layers can be derived later from immutable snapshots.

## Notes

- Terraform owns resource lifecycle.
- The backend is a distribution and retrieval layer, not an editor of canonical knowledge.
