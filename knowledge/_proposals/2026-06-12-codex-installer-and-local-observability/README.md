# Codex installer and local observability proposal package

## Purpose

This package captures two reusable implementation learnings from the current repo:

1. the Codex installer must serialize user-level `config.toml` with TOML-safe quoted keys for paths, version-like names, and plugin or hook identifiers
2. the local memory stack should emit runtime logs at API, worker, and MCP boundaries so developers can follow execution without attaching a debugger
3. the local memory stack must treat hook ingestion as an idempotent event stream and must not fail on empty lifecycle events

## Promotion order

1. Promote `01-codex-installer-toml-serialization.md` to document the repo-local Codex installer invariant.
2. Promote `02-local-stack-observability.md` to document the local stack observability baseline.
3. Promote `03-local-stack-ingest-idempotency.md` to document the local stack ingest idempotency and empty-event handling rules.

## Status

- Package status: promoted
- Canonical targets:
  - `knowledge/repos/memory-for-agents-llm/codex-installer-toml-serialization.md`
  - `knowledge/repos/memory-for-agents-llm/local-stack-observability.md`
  - `knowledge/repos/memory-for-agents-llm/local-stack-ingest-idempotency.md`
