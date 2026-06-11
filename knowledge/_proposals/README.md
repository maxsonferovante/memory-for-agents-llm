# Proposals staging area

This directory holds draft memory updates before they are promoted into canonical knowledge.

## Rules

- One topic per file.
- Include sources in every proposal.
- Include the target canonical path.
- State whether the proposal adds, updates, deprecates, or supersedes a note.
- Keep the proposal short enough to review in one pass.

## Status contract

- `draft`: the proposal is still under review or editing.
- `ready`: the proposal has passed validation and is eligible for hook-driven promotion.
- `promoted`: the canonical copy exists at the target path and the draft is retained as history.
- `rejected`: the proposal will not be promoted in its current form.

## Package structure

- You can group related proposals into dated folders when they belong to the same memory initiative.
- Each folder should include a `README.md` that explains the bundle and the promotion order.
- The first package for this repo is `2026-06-09-memory-foundation/`.
- Additional packages should be added here as they appear so reviewers can find the staged work quickly.
- When the package is promoted, keep the proposal files as historical drafts and point readers to `knowledge/org/`.

## Suggested filename

- `YYYY-MM-DD-topic.md`

## Ownership

- `memory-curator` is the default agent that promotes or rejects proposals.
- Other agents may write proposals, but they should not silently mutate canonical docs.
- Hook automation may only promote proposals that are marked `ready`.

## Additional packages

- [2026-06-10-central-memory-backend/](./2026-06-10-central-memory-backend/) - AWS-backed central memory ingest and agent usage contract.
- [2026-06-10-distribution-installation/](./2026-06-10-distribution-installation/) - versioned package distribution and Claude Code installation contract.
