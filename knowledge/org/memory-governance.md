---
id: memory-governance-v1
type: canonical
scope: org
status: active
owner: memory-curator
source:
  - knowledge/_proposals/2026-06-09-memory-foundation/01-memory-governance.md
  - CLAUDE.md
  - .claude/CLAUDE.md
supersedes: null
---

# Memory governance

## Purpose

Define how knowledge moves from transient work into canonical documentation without losing provenance or creating stale duplicates.

## Knowledge states

- `transient`: live conversation, working notes, and subagent output
- `proposed`: draft notes in `knowledge/_proposals/`
- `ready`: a proposed note that has passed validation and can be promoted by hooks
- `canonical`: source-backed knowledge stored under `knowledge/`
- `deprecated`: older knowledge that remains visible but is no longer current
- `superseded`: a note that has been replaced by a newer canonical note

## Canonical rules

- A canonical note must have a clear scope.
- A canonical note must have a source trail.
- A canonical note must have an owner.
- A canonical note must have a review state.
- A replacement note must explicitly say what it supersedes.
- A proposal must never be treated as canonical without review.

## Promotion boundary

- The main conversation can produce candidates, but it does not create canonical knowledge directly.
- `memory-curator` is the normal promotion path.
- Hooks may block unsafe direct writes to canonical knowledge.
- Hooks may promote a proposal marked `ready` into its canonical target path.

## Why this matters

- The main conversation stays small.
- Durable knowledge becomes reviewable before acceptance.
- Stale facts can be marked as deprecated instead of being silently overwritten.
