---
id: memory-curation-flow-v1
type: canonical
scope: org
status: active
owner: memory-curator
source:
  - knowledge/_proposals/2026-06-09-memory-foundation/README.md
  - knowledge/_proposals/2026-06-09-memory-foundation/01-memory-governance.md
  - knowledge/_proposals/2026-06-09-memory-foundation/04-agent-memory-cycle.md
  - .claude/agents/memory-curator.md
supersedes: null
---

# Memory curation flow

## Purpose

Turn a proposal or repeated learning into canonical knowledge without losing provenance or introducing duplicates.

## Inputs

- open proposals
- repeated memory candidates from agents
- incident notes
- ADR candidates
- repo-local deltas that may need promotion

## Promotion checklist

- [ ] The note has a single clear topic.
- [ ] The source trail is present.
- [ ] The scope is classified.
- [ ] The target path is correct.
- [ ] The note does not duplicate an existing canonical fact.
- [ ] If replacing something, `supersedes` is explicit.
- [ ] If the note changes architecture, an ADR candidate exists or is queued.
- [ ] If the note affects more than one repo, the shared invariant is located.
- [ ] The proposal status will be updated after promotion.
- [ ] Related indexes and README links will be updated.

## Promotion steps

1. Review the proposal or memory candidate.
2. Compare it with existing canonical notes.
3. Decide whether the action is `add`, `update`, `deprecate`, or `supersede`.
4. Choose the canonical target path.
5. Write or update the canonical note in `knowledge/`.
6. Update the proposal record to show promotion or rejection.
7. Mark the proposal `ready` when it passes validation so the Stop hook can promote it automatically.
8. Link the canonical note from the relevant indexes or repo-local docs.
9. Record any unresolved conflict that still needs human review.

## Acceptance criteria

- The canonical note exists in the correct bucket.
- The canonical note has scope, sources, owner, and status.
- Any replacement is explicitly linked to what it supersedes.
- The proposal is no longer treated as a live draft after promotion.
- Any architectural change has an ADR candidate or a recorded reason not to create one.
- Any cross-repo change has a canonical home and a sync path.

## Output format

- Promoted notes
- Rejected notes
- Deprecated notes
- Conflicts to resolve
- Next sync
