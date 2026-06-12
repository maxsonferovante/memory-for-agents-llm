# Coding Agent Memory Platform

This product scope started as the Claude Code memory platform and now represents the shared coding-agent memory platform. It shows how reusable memory knowledge moves across repositories while agent-specific adapters live under `.claude/` and `.codex/`.

## Canonical docs

- [shared-memory-contract.md](./shared-memory-contract.md)
- [distribution-plan.md](./distribution-plan.md)
- [installation-contract.md](./installation-contract.md)
- [release-checklist.md](./release-checklist.md)
- [backend-deployment-tutorial.md](./backend-deployment-tutorial.md)
- [memory-indexing-and-mcp.md](../../integrations/memory-indexing-and-mcp.md)

## Product rule

- Use the org-level contracts from `knowledge/org/` as the base.
- Put shared product behavior here when multiple repos need the same rule.
- Put repo-local deviations under `knowledge/repos/`.
- Treat Claude Code and Codex as clients of the same canonical Markdown, ingestion envelope, and MCP read surface.
