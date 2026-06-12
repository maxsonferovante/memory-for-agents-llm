---
id: prop-memory-curation-autopromotion-v1
type: proposal
scope: org
status: promoted
owner: memory-curator
source:
  - .agents/skills/memory-curation/SKILL.md
  - .claude/skills/memory-curation/SKILL.md
  - .claude/agents/memory-curator.md
  - .claude/templates/memory-curator-session.md
  - .codex/agents/memory-curator.toml
  - knowledge/org/memory-curation-flow.md
  - hooks/README.md
target_path: knowledge/org/memory-curation-autopromotion.md
supersedes: null
confidence: high
promoted_to: knowledge/org/memory-curation-autopromotion.md
promoted_at: 2026-06-12
---


# Memory curation autopromotion candidate

## Problem

The shared memory-curation workflow previously allowed an agent to stop after drafting a proposal and ask the user whether promotion should happen. That adds unnecessary interaction and makes Codex and Claude behave inconsistently even when the source trail, target path, and acceptance criteria are already satisfied.

## Proposal

Define autopromotion as the default completion rule for `memory-curation`.

### Required behavior

- A `memory-curation` session must complete proposal drafting, proposal validation, canonical promotion, and post-promotion verification in the same session.
- Once the memory-curation workflow starts, the agent must not ask the user for a second confirmation to run promotion.
- The proposal artifact should still exist in `knowledge/_proposals/` as historical trace, but it should end the session as `promoted`, not as a lingering live draft.

### Shared execution contract

- The workflow must ensure the proposal is `ready`.
- The workflow must run `python3 hooks/memory_hooks.py promote-ready --queue knowledge/_proposals` from the repo root.
- The workflow must verify that the canonical target exists after promotion.
- The workflow must report both the proposal path and canonical path in the final result.

## Consequences

- Codex and Claude follow the same end-to-end curation contract.
- Durable learnings become canonical immediately when they have already met the review bar.
- The Stop hook remains a safety net instead of the primary way to finish a curation session.

## Sources

- [.agents/skills/memory-curation/SKILL.md](../../../.agents/skills/memory-curation/SKILL.md)
- [.claude/skills/memory-curation/SKILL.md](../../../.claude/skills/memory-curation/SKILL.md)
- [.claude/agents/memory-curator.md](../../../.claude/agents/memory-curator.md)
- [.claude/templates/memory-curator-session.md](../../../.claude/templates/memory-curator-session.md)
- [.codex/agents/memory-curator.toml](../../../.codex/agents/memory-curator.toml)
- [knowledge/org/memory-curation-flow.md](../../../knowledge/org/memory-curation-flow.md)
- [hooks/README.md](../../../hooks/README.md)

## Acceptance criteria

- The proposal states that a memory-curation run must promote in the same session.
- It forbids a second user confirmation once curation has started.
- It names the promotion command and the verification step explicitly.
