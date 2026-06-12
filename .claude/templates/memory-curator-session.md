---
name: memory-curator-session
agent: memory-curator
status: active
scope: session
source:
  - ../agents/memory-curator.md
  - ../../knowledge/org/memory-curation-flow.md
  - ../../knowledge/org/memory-governance.md
supersedes: null
---

# Memory curator session template

Use this template when a proposal or repeated learning is ready to become durable memory.

## Required inputs

- Candidate proposal path or source note
- Target bucket
- Scope
- Source trail
- Supersession target, if any
- Whether an ADR candidate is needed
- Any repo-local note that needs a backlink

## Operating steps

1. Validate the source trail.
2. Check for duplicates and stale notes.
3. Confirm the scope and target path.
4. Decide whether the action is `add`, `update`, `deprecate`, or `supersede`.
5. Fill out the checklist with pass/fail.
6. Evaluate the acceptance criteria with pass/fail.
7. Write or update the canonical note.
8. Update the proposal record.
9. Mark the proposal `ready` when it passes validation.
10. Run `python3 hooks/memory_hooks.py promote-ready --queue knowledge/_proposals`.
11. Verify that the canonical target exists and that the proposal is no longer a live draft.
12. Link the relevant indexes and repo-local notes.
13. Record unresolved conflicts or follow-ups.

## Output contract

Return only these eight sections, in order:

1. Promotion decision
2. Checklist
3. Acceptance criteria
4. Promoted notes
5. Rejected notes
6. Deprecated notes
7. Conflicts to resolve
8. Next sync

## Checklist

- [ ] The note has a single clear topic.
- [ ] The source trail is present.
- [ ] The scope is classified.
- [ ] The target path is correct.
- [ ] The note does not duplicate an existing canonical fact.
- [ ] If replacing something, `supersedes` is explicit.
- [ ] If the note changes architecture, an ADR candidate exists or is queued.
- [ ] If the note affects more than one repo, the shared invariant is located.
- [ ] The proposal status will be updated after promotion.
- [ ] The promotion command will be run in the same session.
- [ ] Related indexes and README links will be updated.

## Acceptance criteria

- [ ] The canonical note exists in the correct bucket.
- [ ] The canonical note has scope, sources, owner, and status.
- [ ] Any replacement is explicitly linked to what it supersedes.
- [ ] The proposal is no longer treated as a live draft after promotion.
- [ ] Any architectural change has an ADR candidate or a recorded reason not to create one.
- [ ] Any cross-repo change has a canonical home and a sync path.
- [ ] The user was not asked for an extra confirmation to perform promotion.

## Session prompt

```text
You are memory-curator.

Candidate notes:
<proposal paths>

Target bucket:
<knowledge/org|products|domains|repos|specs|adr|incidents|runbooks|glossary|integrations>

Scope:
<org|product|domain|repo + identifier>

Supersedes:
<existing note or "None">

Constraints:
- Do not promote unverified claims.
- Do not silently replace history.
- If the note changes architecture, emit or queue an ADR candidate.
- If the note affects more than one repo, keep the shared invariant in the highest applicable scope.
```

## Done when

- The canonical note exists in the correct bucket.
- The proposal is no longer a live draft.
- The canonical links and indexes are updated.
- Any ready proposal has been promoted in the same session.
