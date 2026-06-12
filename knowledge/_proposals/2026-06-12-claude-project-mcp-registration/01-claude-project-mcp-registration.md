---
id: prop-claude-project-mcp-registration-v1
type: proposal
scope: product
status: promoted
owner: cross-repo-coordinator
source:
  - scripts/install_claude_assets.py
  - README.md
  - hooks/README.md
  - knowledge/products/claude-code-memory-platform/installation-contract.md
target_path: knowledge/products/claude-code-memory-platform/claude-project-mcp-registration.md
supersedes: null
confidence: high
promoted_to: knowledge/products/claude-code-memory-platform/claude-project-mcp-registration.md
promoted_at: 2026-06-12
---


# Claude project MCP registration

## Problem

The Claude installer previously copied agents, skills, and hooks, but it did not register the repo MCP server in the Claude client state. That left Claude-side guidance telling agents to prefer MCP memory resources while the actual `localMemory` server binding still depended on a manual external configuration step.

## Proposal

Document the Claude installation split explicitly.

### Required behavior

- The installer must keep Claude hook wiring in `~/.claude/settings.json`.
- The installer must register repo-scoped MCP servers in `~/.claude.json` under `projects["<repo path>"].mcpServers`.
- The `localMemory` entry should launch the repo MCP server through `cargo run --quiet --manifest-path <repo>/local_stack/mcp-server/Cargo.toml`.
- The installer should set `MEMORY_INDEX_PATH` to the repo-derived index path so Claude sessions can resolve the same local memory surface consistently.

### Verification contract

- A dry run must report updates to both `settings.json` and `.claude.json` when the MCP registration is missing.
- A real install must create or update the per-project `mcpServers.localMemory` entry for the repo path.
- A second install against the same target should report the Claude MCP registration as unchanged.

## Consequences

- Claude agents that are instructed to use MCP memory no longer depend on undocumented machine-local setup.
- The Claude installer becomes consistent with the Codex installer in wiring the local memory read surface automatically.
- Claude configuration becomes easier to inspect because hooks and MCP registration live in their actual client-owned files instead of an implied external step.

## Sources

- [scripts/install_claude_assets.py](../../../scripts/install_claude_assets.py)
- [README.md](../../../README.md)
- [hooks/README.md](../../../hooks/README.md)
- [knowledge/products/claude-code-memory-platform/installation-contract.md](../../../knowledge/products/claude-code-memory-platform/installation-contract.md)

## Acceptance criteria

- The note states that Claude hooks live in `settings.json`.
- The note states that project MCP registration lives in `~/.claude.json`.
- The note names the `localMemory` server and its repo-local `MEMORY_INDEX_PATH`.
- The note includes an idempotent verification rule for repeated installs.
