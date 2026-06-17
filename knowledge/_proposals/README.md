# Proposals staging area

This directory holds draft memory updates before they are promoted into canonical knowledge.

## Current state

- 50 markdown files in `knowledge/_proposals/`
- 31 promoted proposal drafts retained as history
- 5 active draft proposals still under review
- Package `README.md` files document bundle scope and promotion intent
- No exact duplicate proposal content was detected during audit

## Rules

- One topic per file.
- Include sources in every proposal.
- Include the target canonical path.
- State whether the proposal adds, updates, deprecates, or supersedes a note.
- Keep the proposal short enough to review in one pass.

## Status contract

- `draft`: the proposal is still under review or editing.
- `ready`: the proposal has passed validation and is eligible for hook-driven promotion.
- `promoted`: the canonical copy exists at the target path and the draft is retained as history.
- `rejected`: the proposal will not be promoted in its current form.

## Package structure

- You can group related proposals into dated folders when they belong to the same memory initiative.
- Each folder should include a `README.md` that explains the bundle and the promotion order.
- The first package for this repo is `2026-06-09-memory-foundation/`.
- Additional packages should be added here as they appear so reviewers can find the staged work quickly.
- When the package is promoted, keep the proposal files as historical drafts and point readers to `knowledge/org/`.

## Suggested filename

- `YYYY-MM-DD-topic.md`

## Ownership

- `memory-curator` is the default agent that promotes or rejects proposals.
- Other agents may write proposals, but they should not silently mutate canonical docs.
- Hook automation may only promote proposals that are marked `ready`.

## Additional packages

- [2026-06-10-distribution-installation/](./2026-06-10-distribution-installation/) - versioned package distribution and Claude Code installation contract.
- [2026-06-11-structured-memory-mcp/](./2026-06-11-structured-memory-mcp/) - structured memory, vector indexing, and MCP consumption roadmap.
- [2026-06-12-claude-project-mcp-registration/](./2026-06-12-claude-project-mcp-registration/) - Claude project MCP registration and product doc index maintenance.
- [2026-06-12-codex-installer-and-local-observability/](./2026-06-12-codex-installer-and-local-observability/) - Codex installer TOML serialization invariants and local stack runtime observability baseline.
- [2026-06-12-local-stack-postgres-mcp/](./2026-06-12-local-stack-postgres-mcp/) - local-stack Postgres MCP runtime ADR.
- [2026-06-12-memory-curation-autopromotion/](./2026-06-12-memory-curation-autopromotion/) - shared autopromotion rule for Codex and Claude memory-curation sessions.
- [2026-06-12-repo-operator-conventions/](./2026-06-12-repo-operator-conventions/) - operator conventions for RTK command execution in repo projects.
- [2026-06-13-local-memory-compose-proxy-routing/](./2026-06-13-local-memory-compose-proxy-routing/) - local memory compose proxy routing ADR.
- [2026-06-14-mcp-oauth-discovery/](./2026-06-14-mcp-oauth-discovery/) - MCP OAuth discovery and architecture decision record.
- [2026-06-15-spec-memory-platform/](./2026-06-15-spec-memory-platform/) - spec memory platform architecture, event taxonomy, and MCP consumption.
- [2026-06-16-session-bootstrap-and-canonical-sync/](./2026-06-16-session-bootstrap-and-canonical-sync/) - session bootstrap, canonical sync, and hook coverage baseline.

## Package themes

- Memory foundation: `2026-06-09-memory-foundation`
- Distribution and install contracts: `2026-06-10-distribution-installation`, `2026-06-12-codex-installer-and-local-observability`
- MCP and local stack runtime: `2026-06-11-structured-memory-mcp`, `2026-06-12-local-stack-postgres-mcp`, `2026-06-14-mcp-oauth-discovery`
- Memory curation and repository lifecycle: `2026-06-12-memory-curation-autopromotion`, `2026-06-12-repo-operator-conventions`, `2026-06-16-session-bootstrap-and-canonical-sync`
- Spec memory platform: `2026-06-15-spec-memory-platform`

## Historical drafts

- Promoted proposals may remain in their package directories as stable historical drafts.
- Use package `README.md` files to understand the bundle scope and promotion intent.
- Keep this root index current so reviewers can find all active and historical packages.
