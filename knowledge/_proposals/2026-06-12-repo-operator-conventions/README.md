# Repo operator conventions proposal package

## Purpose

This package captures a repo-local operator convention that is required when working in this workspace: shell commands should be executed through `rtk` so Codex CLI traffic stays token-efficient while following the repo's operating instructions.

## Promotion order

1. Promote `01-rtk-command-execution-convention.md` to document the repo-local shell execution rule.

## Status

- Package status: ready
- Canonical targets:
  - `knowledge/repos/memory-for-agents-llm/rtk-command-execution-convention.md`
