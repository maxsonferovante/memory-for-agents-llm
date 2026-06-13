# Codex project layer

This directory makes the memory system first-class for Codex, not only Claude Code. Use `scripts/install_codex_assets.py` when you want the same agents, hooks, MCP config, and skills available globally across repositories.

## What Codex loads

- `config.toml`: project-scoped model, subagent limits, and MCP servers.
- `hooks.json`: lifecycle hooks that enforce canonical-memory policy and post memory events.
- `agents/*.toml`: focused custom agents for research, spec, architecture, implementation, review, curation, and cross-repo coordination.
- `../.agents/skills/*/SKILL.md`: repo-scoped Codex skills discovered from any subdirectory in this repository.

## Trust and MCP

Codex loads project-local hooks and MCP only after this `.codex/` layer is trusted. The local memory MCP server is optional (`required = false`) so Codex still works before the local stack database is available.

The default MCP config starts the Rust MCP server from this repo and connects to:

```txt
postgresql://memory:memory@127.0.0.1:5432/memory
```

For Docker Compose runs, keep the local Postgres service exposed on `127.0.0.1:5432`, or override `MEMORY_DATABASE_URL` in your user-level `~/.codex/config.toml`.

## Global install

Run `python3 scripts/install_codex_assets.py --dry-run` to preview installation into user-level Codex locations. By default the installer writes:

- `~/.codex/config.toml` for global features, subagent limits, and MCP servers.
- `~/.codex/hooks.json` for global lifecycle hooks.
- `~/.codex/agents/*.toml` for global custom agents.
- `~/.agents/skills/*/SKILL.md` for global user skills.
- `~/.codex/memory-for-agents-llm/hooks/` for the shared hook scripts.
