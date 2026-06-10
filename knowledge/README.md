# Knowledge store

This directory is the durable knowledge layer for the repo.

## Purpose

- Keep reusable knowledge out of prompt context.
- Make decisions source-backed and versioned.
- Separate shared knowledge from repo-local knowledge.
- Give agents a stable place to write proposals before promotion.

## Buckets

- `org/`: organization-wide invariants
- `products/`: product-wide rules and shared behavior
- `domains/`: domain concepts and business rules
- `repos/`: repo-specific conventions and local knowledge
- `specs/`: SDD specs and historical specs
- `adr/`: architecture decision records
- `incidents/`: incidents, postmortems, and lessons learned
- `runbooks/`: operational runbooks and recovery steps
- `glossary/`: domain glossary and canonical term definitions
- `integrations/`: external systems and integration contracts
- `_proposals/`: draft updates, memory deltas, and ADR candidates

## Update flow

1. Research with `context-researcher`.
2. Draft the change as a proposal.
3. Curate the proposal with `memory-curator`.
4. Promote the accepted result into the relevant bucket.
5. Link the new canonical note from the related repo or domain note.

## Memory contract

- A note is not canonical until it is source-backed.
- A note is not reusable until it has scope and status.
- A note is not stable until it has a review date or owner.
