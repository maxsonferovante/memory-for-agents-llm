# Local stack Postgres MCP proposal package

## Purpose

This package records the repo-local runtime decision that the `localMemory` MCP server reads directly from Postgres, with `pgvector` as the canonical chunk embedding storage, and that the local stack no longer depends on a derived `index.json` file.

## Promotion order

1. Promote `01-local-stack-postgres-mcp-runtime-adr.md` to document the repo-local ADR for the Postgres-backed MCP runtime.

## Status

- Package status: ready
- Canonical target:
  - `knowledge/adr/local-stack-postgres-mcp-runtime.md`
