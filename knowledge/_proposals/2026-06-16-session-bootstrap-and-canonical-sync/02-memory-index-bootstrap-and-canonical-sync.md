---
id: prop-memory-index-bootstrap-and-canonical-sync-v1
type: proposal
scope: integration
status: promoted
owner: cross-repo-coordinator
source:
  - ../../../hooks/memory_event_poster.py
  - ../../../hooks/memory_hooks.py
  - ../../../local_stack/worker.py
  - ../../../hooks/README.md
target_path: knowledge/integrations/memory-bootstrap-and-canonical-sync.md
supersedes: knowledge/integrations/memory-indexing-and-mcp.md
confidence: high
promoted_to: knowledge/integrations/memory-bootstrap-and-canonical-sync.md
promoted_at: 2026-06-16
---


# Memory index bootstrap and canonical sync contract

## Problem

The current ingestion contract documents session-stop, proposal-ready, promotion, and repo-handoff events, but it does not require bootstrap capture of the repo operating context and does not explicitly state that canonical `knowledge/` notes should be re-sent persistently from Markdown to the local ingest API.

## Proposal

Extend the phase-1 capture contract with bootstrap and canonical-sync behavior.

### Event contract

- Hooks may send `repo_handoff` events at session bootstrap to capture the project understanding context assembled from the repo operating documents.
- Hooks may send `canonical_sync` events whenever canonical `knowledge/` notes are re-sent from Markdown to keep the local ingest index aligned with the canonical source of truth.
- Hooks must send `memory_promoted` events when a ready proposal is promoted into a canonical target.

### Reliability rule

- Canonical Markdown remains the source of truth.
- Re-sending canonical notes is an index refresh, not an authorization to mutate Markdown.
- The write path and the index-refresh path must remain separate.

### Retrieval rule

- The worker should treat bootstrap context as retrievable session context.
- The worker should treat `canonical_sync` and `memory_promoted` as canonical records in structured memory.

## Consequences

- The local memory index can be rebuilt continuously from the canonical Markdown base.
- Repo-understanding context becomes visible to later retrieval steps in the same session family.
- Promotion and persistent re-sync now share a clear event contract instead of depending on inference.

## Sources

- [hooks/memory_event_poster.py](../../../hooks/memory_event_poster.py)
- [hooks/memory_hooks.py](../../../hooks/memory_hooks.py)
- [local_stack/worker.py](../../../local_stack/worker.py)
- [hooks/README.md](../../../hooks/README.md)

## Acceptance criteria

- The proposal explicitly allows bootstrap `repo_handoff` events.
- It introduces persistent `canonical_sync` events for canonical Markdown refresh.
- It requires promoted notes to be emitted as `memory_promoted`.
- It states that the canonical Markdown store remains the source of truth.
