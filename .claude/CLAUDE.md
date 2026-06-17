# Claude Code session contract

Use this file as the operational layer for Claude Code sessions in this repo.

## What to do first

- Read `README.md`
- Read `knowledge/README.md`
- Read the relevant proposal files in `knowledge/_proposals/`
- Read only the rules that match the task

## Session behavior

- Delegate verbose research to `context-researcher`.
- Delegate spec shaping to `spec-analyst`.
- Delegate architecture decisions to `architect`.
- Delegate code changes to `implementer`.
- Delegate review to `reviewer`.
- Delegate durable knowledge promotion to `memory-curator`.
- Use `.claude/templates/` when you need a copy-paste session prompt for `context-researcher`, `spec-analyst`, `architect`, `reviewer`, or `memory-curator`.
- Use `hooks/` as the enforcement layer for canonical-write guards and ready-proposal promotion.
- Use MCP memory resources before broad repository exploration when the task depends on prior decisions, repeated lessons, or cross-repo invariants.
- Use `scripts/install_claude_assets.py` to bootstrap the local Claude config with this repo's agents, skills, and hook wiring.

## Conversation shape

- Keep responses short and structured.
- Prefer source-backed claims over intuition.
- If sources conflict, surface the conflict instead of hiding it.
- If a task spans repos, split the answer into shared facts and repo-local facts.

## Memory conversation

- Treat `knowledge/_proposals/` as the handoff queue between sessions.
- Treat `knowledge/` as the durable memory store.
- Treat subagent memory as a convenience layer, not the source of truth.
- Every proposal must say what changed, why, what it depends on, and what it supersedes.
- End every user-facing answer with a short offer to convert the reusable outcome into durable knowledge.
