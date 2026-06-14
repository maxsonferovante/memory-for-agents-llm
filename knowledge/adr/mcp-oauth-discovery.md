---
id: prop-mcp-oauth-discovery-adr-v1
type: canonical
scope: repo
status: active
owner: memory-curator
supersedes: null
confidence: high
reviewed_at: 2026-06-14
promoted_to: knowledge/adr/mcp-oauth-discovery.md
---


# MCP OAuth discovery ADR candidate

## Problem

Some MCP clients probe OAuth discovery endpoints such as `/.well-known/oauth-authorization-server` and `/.well-known/oauth-protected-resource` before they treat a server as usable. The local memory stack previously exposed only `/mcp`, which caused discovery requests to fall through the proxy and generated 404/406 noise even though the MCP server itself was healthy.

## Proposal

Standardize OAuth discovery metadata for the repo-local MCP surface.

- The Nginx proxy must forward `.well-known` OAuth discovery paths to the MCP server instead of serving 404s.
- The MCP server must expose authorization-server metadata and protected-resource metadata for both the root and `/mcp`-prefixed discovery paths.
- The published discovery metadata must include stable endpoints for authorization, token exchange, introspection, revocation, and dynamic registration even if the local implementation only provides discovery metadata and not a full interactive identity provider.
- The local stack should treat discovery as part of the public MCP contract so clients can complete connection setup without special casing the repo-local deployment.

## Consequences

- MCP clients that expect OAuth discovery can resolve the local stack without failing on missing metadata routes.
- The proxy contract becomes more complete because `/mcp` and the associated `.well-known` paths are both routable.
- The local stack remains explicit about capabilities: it can publish discovery metadata without pretending to be a full external identity provider.

## Sources

- [local_stack/mcp-server/src/main.rs](../../../local_stack/mcp-server/src/main.rs)
- [local_stack/proxy/nginx.conf](../../../local_stack/proxy/nginx.conf)
- [knowledge/adr/local-memory-compose-proxy-routing.md](../../../knowledge/adr/local-memory-compose-proxy-routing.md)
- [knowledge/adr/local-stack-postgres-mcp-runtime.md](../../../knowledge/adr/local-stack-postgres-mcp-runtime.md)
- [local_stack/README.md](../../../local_stack/README.md)

## Acceptance criteria

- The decision states that `.well-known` OAuth discovery paths are routed through the proxy.
- The decision states that the MCP server serves authorization-server and protected-resource metadata.
- The decision states that local MCP clients can complete discovery without 404/406 fallback behavior on the public proxy.
