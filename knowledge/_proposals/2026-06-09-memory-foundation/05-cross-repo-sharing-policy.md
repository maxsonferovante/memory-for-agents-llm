---
id: prop-cross-repo-sharing-policy-v1
type: proposal
scope: org
status: draft
owner: cross-repo-coordinator
target_path: knowledge/org/cross-repo-sharing-policy.md
supersedes: null
confidence: high
---

# Cross-repo sharing policy v1

## Problem

The same business or technical rule will appear in several repositories, and the team needs a single place to say which version is canonical.

## Proposal

Use a simple rule:

- one shared invariant lives in the highest applicable scope
- repo-specific behavior is recorded as a delta
- any shared change produces a sync plan for all affected repos
- a cross-repo note should say which repo is the canonical owner

## Consequences

- Shared changes become easier to propagate.
- Repos no longer need to re-explain the same invariant independently.
- Ownership becomes explicit.

## Sources

- [.claude/agents/cross-repo-coordinator.md](../../../.claude/agents/cross-repo-coordinator.md)
- [knowledge/README.md](../README.md)
- [.claude/rules/10-cross-repo-context.md](../../../.claude/rules/10-cross-repo-context.md)

## Acceptance criteria

- Every shared rule has a canonical home.
- Every repo-local deviation points back to the shared note.
- Cross-repo synchronization is tracked as a deliberate action.
