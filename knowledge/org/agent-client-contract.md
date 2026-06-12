---
id: org-agent-client-contract
type: canonical
scope: org
source:
  - README.md
  - .codex/config.toml
  - .codex/hooks.json
  - .codex/agents/memory-coordinator.toml
  - https://developers.openai.com/codex/guides/agents-md
  - https://developers.openai.com/codex/mcp
  - https://developers.openai.com/codex/hooks
  - https://developers.openai.com/codex/subagents
status: active
owner: platform-memory
reviewed_at: 2026-06-12
supersedes: []
confidence: high
---

# Agent client contract

## Decision

This repository is no longer Claude Code exclusive. The canonical memory system must support Claude Code, Codex, and future coding-agent clients through the same durable Markdown knowledge store, shared ingestion envelope, local indexer, and MCP read surface.

## Invariants

- Markdown under `knowledge/` remains the source of truth.
- Agent-specific files are adapters, not separate truth stores.
- Claude Code assets live under `.claude/` and may be installed into a local Claude config directory.
- Codex assets live under `.codex/` and are project-scoped after the project layer is trusted.
- Hooks must preserve provenance through the `source` field, such as `claude-code-hook`, `codex-code-hook`, or `codex-subagent-hook`.
- MCP is the shared read surface for agents. It exposes indexed memory but does not replace canonical Markdown.

## Codex adapter

The Codex adapter includes:

- `.codex/config.toml` for model defaults, subagent limits, and MCP servers.
- `.codex/hooks.json` for lifecycle hooks.
- `.codex/agents/*.toml` for custom agents.
- `.codex/skills/*/SKILL.md` for reusable memory workflows.
- `hooks/codex_hook_runner.py` for Codex-safe policy enforcement and promotion commands.

## Hook events

Codex and Claude Code should both emit the same ingestion envelope:

```json
{
  "event_type": "session_stop | subagent_stop | proposal_ready | memory_promoted | repo_handoff",
  "repo": "memory-for-agents-llm",
  "branch": "feature/x",
  "commit_sha": "...",
  "file_path": "knowledge/repos/...",
  "content_hash": "...",
  "content": "...",
  "scope": "org | product | domain | repo | spec | adr",
  "source": "codex-code-hook | claude-code-hook",
  "session_id": "...",
  "created_at": "..."
}
```

## MCP consumption

Codex should use the `localMemory` MCP server before broad repository exploration when the task depends on prior decisions, repeated lessons, or cross-repo invariants. Claude Code and other clients should follow the same policy when they can consume MCP resources or tools.

## Acceptance criteria

- [x] Codex has project-scoped config for MCP and subagent limits.
- [x] Codex has custom agents that mirror the shared memory workflow roles.
- [x] Codex hooks can guard canonical writes, validate proposals, post ingestion events, and promote ready proposals.
- [x] Shared hooks can preserve per-client provenance.
- [x] Documentation describes the project as a broad agent memory system rather than a Claude-only system.
