---
id: prop-bidirectional-structured-memory-adr-v1
type: proposal
scope: product
status: promoted
owner: cross-repo-coordinator
target_path: knowledge/adr/bidirectional-structured-memory-mcp.md
supersedes: prop-structured-memory-mcp-adr-v1
confidence: high
promoted_to: knowledge/adr/bidirectional-structured-memory-mcp.md
promoted_at: 2026-06-18
---


# Bidirectional structured memory and MCP ADR candidate

## Problem

The local memory stack now needs a dual-source-of-truth model where repository documents and the database both hold durable truth, while MCP returns structural JSON that can be losslessly re-emitted as Markdown. The previous read model treated Markdown as the only authoritative source and did not model writeback suggestions, revision identity, or explicit divergence.

## Proposal

Adopt a bidirectional, lossless memory architecture:

1. Persist ingest events with stable document identity, revision identity, parent revision identity, operation, and canonical path.
2. Materialize `document_revisions`, `document_sections`, and `consolidation_snapshots` as canonical database projections.
3. Expose MCP reads as structural JSON, not literal Markdown, while preserving exact text and order.
4. Represent repo-vs-database divergence explicitly through conflicts and writeback suggestions instead of silent overwrite.

The source of truth becomes shared between the repository and the database. Markdown remains the canonical authoring form, but the read contract is structural JSON that can be reconstructed into Markdown without relevant loss.

## Target architecture

```txt
knowledge/ and curated proposals
   ↕
Ingestion API
   ↕
Raw events + document identity
   ↕
Revisions / sections / consolidations / conflicts
   ↕
MCP structural JSON
   ↕
Agents and curation workflows
```

## Rationale

- Document identity and revision identity are required to preserve continuity across create, update, rename, delete, split, and merge operations.
- Structural sections preserve order, provenance, links, and references without forcing the read contract to be Markdown literal.
- Consolidations should be materialized in the database so shared views can be queried independently of the repository.
- Explicit conflict and writeback suggestions keep the write path auditable and avoid silent divergence.
- The MCP boundary should be able to emit JSON that round-trips back into Markdown with the same text and order.

## Alternatives considered

- Keep Markdown as the only read contract.
  - Rejected because it does not model the structural JSON read surface required by the current stack.
- Treat the database as the only source of truth.
  - Rejected because it would weaken repository reviewability and promotion governance.
- Auto-apply database writeback into Git.
  - Rejected because writeback must remain suggested and auditable.

## Consequences

- The stack gains a bidirectional memory workflow with explicit divergence handling.
- Canonical knowledge can be reconstructed from either repository content or database projections.
- MCP clients can consume JSON structurally while still reproducing Markdown faithfully when needed.
- The roadmap must preserve append-only history and tombstones for destructive operations.

## Sources

- [README.md](../../../README.md)
- [DOCUMENTACAO.md](../../../DOCUMENTACAO.md)
- [hooks/memory_event_poster.py](../../../hooks/memory_event_poster.py)
- [local_stack/storage.py](../../../local_stack/storage.py)
- [local_stack/worker.py](../../../local_stack/worker.py)
- [local_stack/mcp-server/src/main.rs](../../../local_stack/mcp-server/src/main.rs)
- [scripts/smoke_test_local_memory_stack.py](../../../scripts/smoke_test_local_memory_stack.py)

## Acceptance criteria

- The ADR explicitly describes bidirectional, lossless memory flow.
- Document and revision identity are first-class concepts.
- The MCP contract is structural JSON and preserves order/text losslessly.
- Conflicts and writeback suggestions are explicit and auditable.
- The target remains compatible with the existing ADR roadmap path.
