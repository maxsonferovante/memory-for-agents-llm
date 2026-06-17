# Repository Guidelines

## Project Structure & Module Organization
This repository is the phase-1 reference for coding-agent memory and orchestration across Claude Code, Codex, and future agent clients. Keep durable knowledge in `knowledge/`, not in chat logs. The most important areas are:

- `knowledge/org/`: org-wide policies and memory contracts
- `knowledge/products/`: product-level shared behavior
- `knowledge/repos/`: repo-specific conventions and overrides
- `knowledge/_proposals/`: draft updates before promotion
- `hooks/`: shared enforcement, ingestion, and promotion hooks
- `.claude/`: Claude Code rules, skills, and templates
- `runtime_sources/claude/subagents/`: Claude Code subagent source files installed by the Claude installer
- `.codex/`: Codex project config, MCP config, hooks, and custom agents
- `.agents/skills/`: repo-scoped Codex skills discovered from any subdirectory
- `scripts/`: install, packaging, and smoke-test utilities
- `local_stack/`: fully local Rust/Python ingest/index/MCP stack

## Build, Test, and Development Commands
- `python3 scripts/install_claude_assets.py --dry-run`: preview local Claude config installation
- `python3 scripts/install_claude_assets.py`: install repo agents, skills, and hooks
- `python3 scripts/install_codex_assets.py --dry-run`: preview global Codex config installation
- `python3 scripts/install_codex_assets.py`: install Codex agents, skills, hooks, and MCP config globally
- `docker compose up --build`: start the local memory stack
- `python3 scripts/smoke_test_local_memory_stack.py`: run the end-to-end local ingest/index smoke test
- `python3 hooks/memory_hooks.py validate-proposal <path>`: validate a proposal before promotion
- `python3 hooks/memory_hooks.py guard-write --path <path>`: check whether a write touches canonical memory

## Coding Style & Naming Conventions
Use UTF-8 Markdown with short sections and explicit headings. Prefer direct, source-backed language over speculation. For code and scripts, follow the existing language defaults: Rust 2021 in `local_stack/api/` and `local_stack/mcp-server/`, Python 3 for `scripts/` and `hooks/`. Keep filenames descriptive and scoped, such as `knowledge/repos/<repo-name>/README.md` or `knowledge/_proposals/YYYY-MM-DD-topic/NN-title.md`.

## Testing Guidelines
There is no large test suite at the repository root. Verify changes with the smallest meaningful command:

- local stack changes: `python3 scripts/smoke_test_local_memory_stack.py`
- hook changes: run the relevant `python3 hooks/memory_hooks.py ...` command
- Rust changes: run `cargo check` inside the affected crate directory

Name new smoke inputs and proposal files so they are easy to trace back to the feature or decision they validate.

## Commit & Pull Request Guidelines
Commit history uses short conventional prefixes such as `feat:`, `fix:`, `docs:`, and `chore:`. Keep commits focused and descriptive, for example `docs: add architecture brief`. Pull requests should explain the behavior change, list validation performed, and link any related proposal or issue. Include screenshots only when the change affects rendered docs or UI-like output.

## Agent-Specific Instructions
Keep the main conversation small. Codex should use `.codex/config.toml`, `.codex/hooks.json`, `.codex/agents/*.toml`, and `.agents/skills/*/SKILL.md`; Claude Code should use `.claude/` and the Claude installer. Use `knowledge/_proposals/` for draft facts, and promote to canonical docs only after validation. If a change affects shared behavior, update the relevant higher-scope note first and link back from repo-local notes. Every user-facing answer should end with a short offer to turn the reusable part of the conversation into durable knowledge.
