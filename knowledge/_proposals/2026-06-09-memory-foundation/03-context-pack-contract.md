---
id: prop-context-pack-contract-v1
type: proposal
scope: org
status: draft
owner: context-researcher
target_path: knowledge/org/context-pack-contract.md
supersedes: null
confidence: high
---

# Context pack contract v1

## Problem

Research output is too large to drop into the main conversation directly, so the system needs a standard compressed format.

## Proposal

Standardize a `Context Pack` with these sections:

- objective
- canonical sources
- verified facts
- open questions
- conflicts
- relevant code paths
- memory candidates

Contract rules:

- keep the pack minimal
- prefer source links over paraphrase
- separate shared facts from repo-local facts
- include the scope of each fact when that matters

## Consequences

- The main session receives only the useful context.
- Multiple sessions can compare the same task output in a consistent format.
- Memory promotion becomes easier because the candidate facts are already separated.

## Sources

- [.claude/agents/context-researcher.md](../../../.claude/agents/context-researcher.md)
- [knowledge/README.md](../README.md)
- [Claude docs on subagents](https://code.claude.com/docs/en/sub-agents.md)
- [Claude docs on context and memory](https://code.claude.com/docs/en/memory.md)

## Acceptance criteria

- Every researcher output can be rendered into the same section order.
- Conflicts are visible instead of buried.
- Memory candidates are separated from verified facts.
