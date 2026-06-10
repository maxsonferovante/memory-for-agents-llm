---
id: cross-repo-sharing-policy-v1
type: canonical
scope: org
status: active
owner: cross-repo-coordinator
source:
  - knowledge/_proposals/2026-06-09-memory-foundation/05-cross-repo-sharing-policy.md
  - .claude/rules/10-cross-repo-context.md
supersedes: null
---

# Cross-repo sharing policy

## Rule

- One shared invariant lives in the highest applicable scope.
- Repo-specific behavior is recorded as a delta.
- Any shared change produces a sync plan for the affected repos.
- The canonical owner for the shared fact must be explicit.

## Promotion rule

- If a fact appears in more than one repo, check whether it belongs in `org` or `product`.
- If the fact is only a local implementation detail, keep it in `repo`.
- If the fact needs propagation across repos, capture the sync plan with the canonical note.

## Why this matters

- Shared changes become easier to propagate.
- Repos do not need to re-explain the same invariant independently.
- Ownership becomes explicit instead of implied.
