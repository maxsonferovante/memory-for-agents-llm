---
id: prop-bidirectional-structured-memory-integration-v1
type: proposal
scope: integration
status: promoted
owner: cross-repo-coordinator
target_path: knowledge/integrations/bidirectional-structured-memory-mcp.md
supersedes: prop-structured-memory-mcp-contract-v1
confidence: high
promoted_to: knowledge/integrations/bidirectional-structured-memory-mcp.md
promoted_at: 2026-06-18
---


# Bidirectional structured memory and MCP integration contract

## Problem

The integration contract needs to reflect that memory ingest is no longer write-only. The API, worker, and MCP server now exchange document identity, revisions, structural sections, consolidations, conflicts, and writeback suggestions.

## Proposal

Update the integration contract so that:

1. `POST /events` and `POST /events/batch` carry stable document identity, revision identity, operation, and canonical path.
2. The worker materializes `document_revisions`, `document_sections`, and `consolidation_snapshots` as durable projections.
3. MCP returns structural JSON for documents and consolidations, with exact text and order preserved.
4. Repository and database divergence is surfaced as explicit conflict state plus `writeback_suggestions`.

## Operational contract

- Event capture remains append-only.
- Revisions keep `parent_revision_id` and `operation` so destructive changes can be traced.
- Sections retain ordered blocks, links, references, and provenance.
- Consolidations remain persisted database views rather than ephemeral search results.
- Writeback remains suggested, not auto-applied.

## Readback expectations

The MCP response contract should include:

- `document_id`
- `revision_id`
- `status`
- `canonical_path`
- `frontmatter`
- hierarchical `sections`
- ordered `blocks`
- `links`, `references`, and `provenance`
- `conflict_state`
- `writeback_available`

The returned JSON must be sufficient to reconstruct the canonical Markdown without material loss in text or order.

## Sources

- [README.md](../../../README.md)
- [DOCUMENTACAO.md](../../../DOCUMENTACAO.md)
- [local_stack/api/src/main.rs](../../../local_stack/api/src/main.rs)
- [local_stack/worker.py](../../../local_stack/worker.py)
- [local_stack/storage.py](../../../local_stack/storage.py)
- [local_stack/mcp-server/src/main.rs](../../../local_stack/mcp-server/src/main.rs)

## Consequences

- The integration contract now explicitly covers readback and writeback suggestion surfaces.
- MCP clients can rely on structural JSON rather than Markdown literal reads.
- The document and revision model becomes a required part of event capture and projection.
- Divergence handling is explicit, which keeps repository promotion and database materialization auditable.

## Acceptance criteria

- The ingestion API contract includes document and revision identity.
- The MCP contract states structural JSON as the supported read surface.
- Explicit conflict state and writeback suggestions are documented.
- The contract remains compatible with the existing local stack smoke test flow.
