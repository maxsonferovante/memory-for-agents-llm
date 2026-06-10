# Knowledge store

This directory is the durable knowledge layer for the repo. It is the canonical home for reusable facts that should survive across Claude Code sessions.

## What belongs here

- `org/`: organization-wide invariants and policies.
- `products/`: shared behavior for one product across multiple repos.
- `domains/`: domain concepts, rules, and glossary terms.
- `repos/`: repo-specific conventions and local deltas.
- `specs/`: SDD specs and historical specs.
- `adr/`: architecture decision records.
- `incidents/`: incidents, postmortems, and lessons learned.
- `runbooks/`: operational runbooks and recovery steps.
- `glossary/`: canonical term definitions.
- `integrations/`: external systems and integration contracts.
- `_proposals/`: draft updates, ADR candidates, and cross-repo notes before promotion.

## How knowledge moves

1. Research with `context-researcher`.
2. Capture the result as a proposal in `knowledge/_proposals/`.
3. Curate the proposal with `memory-curator`.
4. Promote the accepted note into the correct bucket.
5. Link the canonical note back from the relevant repo or domain note.

## Bucket rules

- Keep shared invariants in the highest applicable scope.
- Keep repo-local exceptions local and linked back to shared notes.
- Do not duplicate canonical facts silently.
- If scope is unclear, keep the note in `_proposals/` until it is resolved.

## Memory contract

- A note is not canonical until it is source-backed.
- A note is not reusable until it has scope and status.
- A note is not stable until it has an owner and a review state.
