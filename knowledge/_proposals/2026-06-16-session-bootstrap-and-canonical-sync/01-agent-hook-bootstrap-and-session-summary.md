---
id: prop-agent-hook-bootstrap-and-session-summary-v1
type: proposal
scope: repo
status: promoted
owner: memory-curator
source:
  - ../../../hooks/memory_event_poster.py
  - ../../../hooks/README.md
  - ../../../scripts/install_codex_assets.py
  - ../../../scripts/install_claude_assets.py
  - ../../../.codex/hooks.json
target_path: knowledge/repos/memory-for-agents-llm/session-bootstrap-and-canonical-sync.md
supersedes: knowledge/repos/memory-for-agents-llm/agent-hook-coverage.md
confidence: high
promoted_to: knowledge/repos/memory-for-agents-llm/session-bootstrap-and-canonical-sync.md
promoted_at: 2026-06-16
---


# Agent hook bootstrap and session summary

## Problem

The existing hook baseline captures many file-backed events, but it does not guarantee that a session posts the repo understanding context at startup, it does not persistently re-send canonical `knowledge/` notes to the local ingest API, and it does not reliably produce a useful session summary when the stop hook has no explicit payload.

## Proposal

Define a stronger repo-local hook coverage baseline for both Codex and Claude Code.

### Bootstrap rule

- The first hook invocation in each session must post a repo-context snapshot built from the project operating documents.
- The same bootstrap step must re-send canonical Markdown under `knowledge/` to the local ingest API so the canonical store is always reindexed from source-backed documents.

### Session summary rule

- The stop hook must still act as the safety net for end-of-session capture.
- When no explicit Markdown payload exists, the stop hook should synthesize a work summary from the repository state, including working tree changes and recent commit context.

### Installer rule

- `scripts/install_codex_assets.py` and `scripts/install_claude_assets.py` must generate the same bootstrap hook behavior.
- Repo-local `.codex/hooks.json` should mirror the generated Codex behavior so local project trust and global installation stay aligned.

### Conversation rule

- User-facing answers should end with a short offer to convert reusable outcomes into durable knowledge.

## Consequences

- Session context becomes available to the ingest pipeline even before the user asks for explicit curation.
- Canonical `knowledge/` documents are re-sent from Markdown regularly instead of depending only on historical promotions.
- End-of-session capture becomes useful even for edit-heavy turns where the lifecycle hook has no direct file payload.

## Sources

- [hooks/memory_event_poster.py](../../../hooks/memory_event_poster.py)
- [hooks/README.md](../../../hooks/README.md)
- [scripts/install_codex_assets.py](../../../scripts/install_codex_assets.py)
- [scripts/install_claude_assets.py](../../../scripts/install_claude_assets.py)
- [.codex/hooks.json](../../../.codex/hooks.json)

## Acceptance criteria

- The proposal requires a session-start bootstrap event.
- It requires canonical `knowledge/` notes to be re-sent to the ingest API.
- It requires a synthesized stop summary when no explicit payload exists.
- It requires the Codex and Claude installers to emit the same hook behavior.
- It requires a short durable-knowledge offer in user-facing responses.
