---
id: memory-curator-promotion-example-v1
type: canonical
scope: org
status: active
owner: memory-curator
source:
  - ../../../knowledge/_proposals/2026-06-09-memory-foundation/06-context-pack-example.md
  - ../../../knowledge/products/claude-code-memory-platform/shared-memory-contract.md
  - ../../../knowledge/repos/memory-for-agents-llm/repo-local-memory-overrides.md
  - ./memory-curation-flow.md
supersedes: null
---

# Memory curator promotion example

This note records the first concrete promotion example using the phase-1 contracts.

## Promotion decision

- Promote the shared memory contract into the product scope.
- Promote the local override notes into the repo scope.
- Keep the context pack as a draft example under `knowledge/_proposals/`.

## Checklist

- [x] The note has a single clear topic.
- [x] The source trail is present.
- [x] The scope is classified.
- [x] The target path is correct.
- [x] The note does not duplicate an existing canonical fact.
- [x] If replacing something, `supersedes` is explicit.
- [x] If the note changes architecture, an ADR candidate exists or is queued.
- [x] If the note affects more than one repo, the shared invariant is located.
- [x] The proposal status will be updated after promotion.
- [x] Related indexes and README links will be updated.

## Acceptance criteria

- [x] The canonical note exists in the correct bucket.
- [x] The canonical note has scope, sources, owner, and status.
- [x] Any replacement is explicitly linked to what it supersedes.
- [x] The proposal is no longer treated as a live draft after promotion.
- [x] Any architectural change has an ADR candidate or a recorded reason not to create one.
- [x] Any cross-repo change has a canonical home and a sync path.

## Promoted notes

- [knowledge/products/claude-code-memory-platform/shared-memory-contract.md](../../../knowledge/products/claude-code-memory-platform/shared-memory-contract.md)
- [knowledge/repos/memory-for-agents-llm/repo-local-memory-overrides.md](../../../knowledge/repos/memory-for-agents-llm/repo-local-memory-overrides.md)

## Rejected notes

- None

## Deprecated notes

- None

## Conflicts to resolve

- None

## Next sync

- Keep the product note and repo note synchronized when new repos are added to the product.
