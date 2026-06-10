---
id: prop-memory-governance-v1
type: proposal
scope: org
status: draft
owner: memory-curator
target_path: knowledge/org/memory-governance.md
supersedes: null
confidence: high
---

# Memory governance v1

## Problem

The repo needs a durable way to move knowledge from transient chat context into canonical documentation without losing provenance or creating stale duplicates.

## Proposal

Define three states for knowledge:

- transient: live conversation, working notes, and subagent output
- proposed: draft notes in `knowledge/_proposals/`
- canonical: source-backed knowledge stored under `knowledge/`

Promotion into canonical knowledge requires:

- a clear scope
- a source trail
- an owner
- a review state
- an explicit supersession rule when replacing older knowledge

## Consequences

- The main conversation stays small.
- Durable knowledge becomes reviewable before it is accepted.
- Stale facts can be marked as deprecated instead of being silently overwritten.

## Sources

- [CLAUDE.md](../../../CLAUDE.md)
- [.claude/CLAUDE.md](../../../.claude/CLAUDE.md)
- [knowledge/README.md](../README.md)
- [Claude memory docs](https://code.claude.com/docs/en/memory.md)
- [Claude subagents docs](https://code.claude.com/docs/en/sub-agents.md)

## Acceptance criteria

- A proposal must never be treated as canonical without review.
- A canonical note must always show scope and provenance.
- A replacement note must explicitly say what it supersedes.
