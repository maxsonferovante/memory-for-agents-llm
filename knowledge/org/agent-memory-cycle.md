---
id: agent-memory-cycle-v1
type: canonical
scope: org
status: active
owner: coordinator
source:
  - knowledge/_proposals/2026-06-09-memory-foundation/04-agent-memory-cycle.md
  - .claude/agents/coordinator.md
  - .claude/agents/context-researcher.md
  - .claude/agents/memory-curator.md
supersedes: null
---

# Agent memory cycle

## Phase-1 sequence

1. `coordinator` selects the path and keeps the main conversation small.
2. `context-researcher` gathers sources and produces a context pack.
3. `spec-analyst` turns the request into an SDD-ready spec.
4. `architect` decides whether the change needs an ADR.
5. `implementer` changes the code or docs.
6. `reviewer` checks correctness and knowledge drift.
7. `memory-curator` promotes durable learnings into canonical notes.

## Hand-off rules

- The coordinator owns the workflow.
- The researcher owns source collection.
- The curator owns promotion into canonical knowledge.
- The main conversation should only carry the minimum needed context from one step to the next.

## Hook integration

- `PreToolUse` blocks unsafe direct writes to canonical memory.
- `PostToolUse` captures memory candidates into the proposal queue.
- `Stop` reminds the session to curate open proposals before exiting and may auto-promote proposals marked `ready`.

## Why this matters

- Memory becomes a first-class output of the workflow.
- The system can learn between sessions without relying on chat history.
- Repeated knowledge moves through a predictable promotion path.
