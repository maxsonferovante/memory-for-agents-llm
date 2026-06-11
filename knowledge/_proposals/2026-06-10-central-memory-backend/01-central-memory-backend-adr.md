---
id: prop-central-memory-backend-adr-v1
type: proposal
scope: product
status: promoted
owner: cross-repo-coordinator
target_path: knowledge/adr/central-memory-backend.md
supersedes: null
confidence: high
---

# Central memory backend ADR candidate

## Problem

The orchestrator needs a central place to publish and retrieve memory snapshots across local sessions and repos, but direct mutable writes would conflict with source-backed Git docs and make promotion opaque.

## Proposal

Use API Gateway plus Lambda plus S3 as an immutable snapshot backend.

- The API receives manifest-first full snapshots from hooks or tools.
- Lambda validates the request, issues a pre-signed upload, and finalizes the snapshot after the bundle is uploaded.
- S3 stores the bundle, the manifest, and the latest pointer as immutable artifacts.
- Git remains the authoring source of truth for the memory files themselves.
- The AWS backend is a distribution and retrieval layer, not a mutable editor of canonical knowledge.

## Alternatives considered

- Write directly to S3 without an API.
  - Rejected because it removes validation and state transitions.
- Use a mutable database as the source of truth.
  - Rejected because it duplicates the knowledge-governance problem and weakens review.
- Keep only Git sync without a central backend.
  - Rejected because cross-repo retrieval and automation would stay manual.

## Consequences

- Cross-repo retrieval becomes simpler because every published snapshot has one stable home.
- The store becomes auditable because each published state is immutable and content-hashed.
- The system adds one more layer of infrastructure, so Terraform must own the lifecycle and bucket policy explicitly.
- Any semantic index, search index, or derived graph can be rebuilt from the published snapshot history.

## Sources

- [knowledge/org/memory-governance.md](../../../knowledge/org/memory-governance.md)
- [knowledge/org/agent-memory-cycle.md](../../../knowledge/org/agent-memory-cycle.md)
- [knowledge/org/memory-curation-flow.md](../../../knowledge/org/memory-curation-flow.md)
- [knowledge/org/cross-repo-sharing-policy.md](../../../knowledge/org/cross-repo-sharing-policy.md)
- [primeira-pesquisa-ideia.md](../../../primeira-pesquisa-ideia.md)
- [knowledge/products/claude-code-memory-platform/shared-memory-contract.md](../../../knowledge/products/claude-code-memory-platform/shared-memory-contract.md)

## Acceptance criteria

- The backend is append-only from the point of view of published memory snapshots.
- The backend never edits canonical note content in place.
- Every published snapshot is traceable to a repo, a session, and a bundle hash.
- A later search or index layer can be derived from the stored snapshots.
- Git remains the canonical authoring source for memory files.
