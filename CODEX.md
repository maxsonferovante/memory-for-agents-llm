# Codex session contract

Use this file as the human-readable companion to `.codex/config.toml`, `.codex/hooks.json`, and `.codex/agents/*.toml`.

## What to do first

- Read `AGENTS.md`, `README.md`, and `knowledge/README.md`.
- Read relevant proposals under `knowledge/_proposals/` before changing canonical memory.
- Query the `localMemory` MCP server before broad repository exploration when a task depends on prior decisions, repeated lessons, or cross-repo invariants.

## Codex-specific assets

- `.codex/config.toml`: project model defaults, subagent limits, and MCP servers.
- `.codex/hooks.json`: lifecycle hooks for write guards, proposal validation, ingestion, subagent handoffs, and ready-proposal promotion.
- `.codex/agents/*.toml`: project custom agents for memory orchestration.
- `.agents/skills/*/SKILL.md`: repo-scoped reusable memory workflows.
- `scripts/install_codex_assets.py`: global installer for Codex agents, skills, hooks, and MCP config.

## Memory rules

- Markdown under `knowledge/` is canonical.
- Draft durable facts in `knowledge/_proposals/` first.
- Treat MCP and vector search as retrieval/index layers, not the source of truth.
- Keep facts scoped as `org`, `product`, `domain`, `repo`, `spec`, or `adr`.
