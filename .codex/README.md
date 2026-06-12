# Codex project layer

This directory makes the memory system first-class for Codex, not only Claude Code.

## What Codex loads

- `config.toml`: project-scoped model, subagent limits, and MCP servers.
- `hooks.json`: lifecycle hooks that enforce canonical-memory policy and post memory events.
- `agents/*.toml`: focused custom agents for research, spec, architecture, implementation, review, curation, and cross-repo coordination.
- `skills/*/SKILL.md`: Codex-readable copies of the repeatable memory workflows.

## Trust and MCP

Codex loads project-local hooks and MCP only after this `.codex/` layer is trusted. The local memory MCP server is optional (`required = false`) so Codex still works before the local stack has produced an index.

The default MCP config starts the Rust MCP server from this repo and reads:

```txt
local_stack/data/derived/index.json
```

For Docker Compose runs, export or copy the generated `/data/derived/index.json` from the `local-memory-data` volume into that path, or override `MEMORY_INDEX_PATH` in your user-level `~/.codex/config.toml`.
