---
id: prop-knowledge-scope-model-v1
type: proposal
scope: org
status: draft
owner: cross-repo-coordinator
target_path: knowledge/org/knowledge-scope-model.md
supersedes: null
confidence: high
---

# Knowledge scope model v1

## Problem

Knowledge gets duplicated when the same rule exists in multiple repos with slightly different wording or ownership.

## Proposal

Classify every durable note into one of four scopes:

- org: applies to the whole organization
- product: applies to all repos inside one product
- domain: applies to one business domain
- repo: applies only to one repository

Rules for sharing:

- store the shared invariant once
- store repo-local differences separately
- link back to the canonical note instead of copying it
- escalate to an org or product note when the same rule appears in more than one repo

## Consequences

- Shared knowledge stays consistent across repositories.
- Local exceptions remain visible without polluting the shared layer.
- Cross-repo coordination becomes a metadata problem instead of an oral-history problem.

## Sources

- [README.md](../../README.md)
- [knowledge/README.md](../README.md)
- [.claude/rules/10-cross-repo-context.md](../../../.claude/rules/10-cross-repo-context.md)
- [Claude large codebase guidance](https://code.claude.com/docs/en/large-codebases.md)

## Acceptance criteria

- Every durable note can be classified into exactly one primary scope.
- Shared invariants can be located without opening every repository.
- Repo-local exceptions can be traced back to the shared canonical note.
