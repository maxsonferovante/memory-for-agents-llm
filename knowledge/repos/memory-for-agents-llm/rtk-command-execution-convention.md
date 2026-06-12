---
id: prop-memory-for-agents-llm-rtk-command-execution-convention-v1
type: canonical
scope: repo
status: active
owner: memory-curator
source:
  - AGENTS.md
  - CODEX.md
  - /Users/mferovante/.codex/RTK.md
supersedes: null
confidence: high
reviewed_at: 2026-06-12
---


# RTK command execution convention candidate

## Problem

This repository instructs Codex operators to route shell commands through `rtk`, but that requirement is currently documented only in operator-facing instructions instead of repo-local canonical knowledge. Without a canonical note, the rule is easy to miss when work starts from `knowledge/` rather than from the live agent prompt.

## Proposal

Define a repo-local command execution convention for Codex work in this repository.

### Required behavior

- Prefix shell commands with `rtk` when executing them from Codex in this workspace.
- Use `rtk proxy <cmd>` only when a raw command is intentionally required.
- Treat `rtk` usage as an operator convention for repository workflows, not as an application runtime dependency.

### Scope boundary

- This rule applies to repository operation and troubleshooting sessions in `memory for agents llm`.
- The rule does not change the documented underlying commands in `README.md`, `AGENTS.md`, or hook contracts; it changes how Codex should execute them during an interactive session.

## Consequences

- Codex sessions follow the repo's token-efficiency rule consistently.
- Repo-local operational guidance no longer depends on transient chat instructions alone.
- Future repo-local notes can cite a canonical source when they assume `rtk`-prefixed execution.

## Sources

- [AGENTS.md](../../../AGENTS.md)
- [/Users/mferovante/.codex/RTK.md](/Users/mferovante/.codex/RTK.md)
- [CODEX.md](../../../CODEX.md)

## Acceptance criteria

- The note states that Codex should prefix shell commands with `rtk` in this repository.
- It distinguishes repository operation from application runtime behavior.
- It preserves the underlying documented commands while defining the interactive execution wrapper.
