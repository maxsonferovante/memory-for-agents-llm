# Local memory compose proxy routing proposal package

## Purpose

This package records the repo-local runtime decision that the local memory stack exposes one public base endpoint on the Docker Compose proxy, routing `/api/...` to the ingestion API and `/mcp` to the MCP server while keeping the backend services internal.

## Promotion order

1. Promote `01-local-memory-compose-proxy-routing-adr.md` to document the repo-local ADR for proxy-routed local memory access.

## Status

- Package status: ready
- Canonical target:
  - `knowledge/adr/local-memory-compose-proxy-routing.md`
