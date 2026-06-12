---
name: memory-curation
description: Promote durable learnings into canonical knowledge updates
---

# Memory curation

Use this skill when a task produced a reusable fact, decision, or pattern.

This skill must finish the job end to end: write the proposal if needed, promote it to the canonical target, and verify the canonical result in the same turn. Do not stop after drafting a proposal and do not ask the user whether promotion should happen.

For the live-session version of this workflow, use `.claude/templates/memory-curator-session.md`.

## Required workflow

1. Validate the source trail and target scope.
2. Write or update the proposal artifact under `knowledge/_proposals/`.
3. Ensure the proposal is `ready`.
4. Run `python3 hooks/memory_hooks.py promote-ready --queue knowledge/_proposals` from the repo root.
5. Verify that the canonical target now exists at `target_path`.
6. Report the proposal path and canonical path in the final answer.

## Output

- Proposed note
- Canonical note
- Target path
- Scope
- Sources
- Status
- Supersedes

## Constraints

- Do not promote unverified claims.
- Do not silently replace history.
- If the note is architecture-related, emit an ADR candidate.
- Promotion is the default behavior after calling this skill. Do not wait for a second user confirmation.
