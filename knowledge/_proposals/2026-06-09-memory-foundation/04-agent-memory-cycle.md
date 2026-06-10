---
id: prop-agent-memory-cycle-v1
type: proposal
scope: org
status: draft
owner: coordinator
target_path: knowledge/org/agent-memory-cycle.md
supersedes: null
confidence: high
---

# Agent memory cycle v1

## Problem

The roles needed for memory-aware development exist, but the handoff between them is still implicit.

## Proposal

Define the phase-1 agent cycle as:

1. `coordinator` selects the path and keeps the main conversation small.
2. `context-researcher` gathers sources and produces a context pack.
3. `spec-analyst` turns the request into an SDD-ready spec.
4. `architect` decides whether the change needs an ADR.
5. `implementer` changes the code or docs.
6. `reviewer` checks correctness and knowledge drift.
7. `memory-curator` promotes durable learnings into canonical notes.

Hooks support the cycle:

- `PreToolUse` blocks unsafe direct writes to canonical memory.
- `PostToolUse` captures memory candidates into the proposal queue.
- `Stop` reminds the session to curate open proposals before exiting.

## Consequences

- Memory becomes a first-class output of the workflow.
- The system can learn between sessions without relying on chat history.
- Repeated knowledge moves through a predictable promotion path.

## Sources

- [.claude/agents/coordinator.md](../../../.claude/agents/coordinator.md)
- [.claude/agents/memory-curator.md](../../../.claude/agents/memory-curator.md)
- [hooks/README.md](../../../hooks/README.md)
- [Claude docs on hooks](https://code.claude.com/docs/en/hooks-guide.md)

## Acceptance criteria

- Every task can name the agent responsible for the next memory step.
- Durable learnings always have a promotion path.
- Unsafe direct canonical writes are treated as violations, not as normal behavior.
