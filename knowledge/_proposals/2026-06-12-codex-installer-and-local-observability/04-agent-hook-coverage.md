---
id: prop-agent-hook-coverage-v1
type: proposal
scope: repo
status: promoted
owner: memory-curator
target_path: knowledge/repos/memory-for-agents-llm/agent-hook-coverage.md
supersedes: null
confidence: high
promoted_to: knowledge/repos/memory-for-agents-llm/agent-hook-coverage.md
promoted_at: 2026-06-14
---


# Agent hook coverage baseline

## Problem

The repo-local hook configuration initially captured only explicit write paths for some policy checks, which made Codex and Claude Code less consistent at recording memory events during sessions that did not expose a file path in the payload.

## Proposal

Define a repo-local hook coverage baseline for both Codex and Claude Code installers.

### Coverage rule

- Codex and Claude Code should use a broad hook matcher for `PreToolUse`, `PostToolUse`, and `Stop` so the runner can decide whether a payload is meaningful.
- The hook runner should ignore no-op payloads that do not include a usable path rather than failing the hook command.
- Session handoff should still rely on `Stop` as the safety net for posting final lifecycle events and promoting ready proposals.

### Installer rule

- `scripts/install_codex_assets.py` and `scripts/install_claude_assets.py` should generate the same broad hook coverage policy.
- The Codex installer should keep the global local-memory hook wiring and MCP registration.
- The Claude installer should keep the per-project MCP registration and use the same local-memory endpoint derived from `--stack-host`.

### Noise control

- Broad coverage must not turn every payload into a write or promotion action.
- The runner should keep policy enforcement narrow and skip payloads that do not map to a file path or proposal target.

## Consequences

- Codex and Claude Code both post hook events more consistently across write-heavy and non-file-backed actions.
- Session handoff remains safe because `Stop` still performs final posting and promotion.
- The repo preserves the existing separation between capture, policy enforcement, and canonical promotion.

## Sources

- [scripts/install_codex_assets.py](../../../scripts/install_codex_assets.py)
- [scripts/install_claude_assets.py](../../../scripts/install_claude_assets.py)
- [hooks/README.md](../../../hooks/README.md)
- [hooks/codex_hook_runner.py](../../../hooks/codex_hook_runner.py)
- [knowledge/org/memory-curation-flow.md](../../../knowledge/org/memory-curation-flow.md)

## Acceptance criteria

- The proposal states that Codex and Claude use broad hook coverage.
- It requires the runner to ignore no-op payloads instead of failing.
- It preserves `Stop` as the final handoff and promotion safety net.
