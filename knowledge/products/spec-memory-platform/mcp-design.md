---
id: spec-memory-platform-mcp-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---

# MCP design

## Role

MCP is the official consumption layer for agent runtimes. Runtimes consume memory through MCP resources and tools; they do not access database tables, vector indexes, or event projections directly.

## Resources

| Resource | Description |
| --- | --- |
| `memory://org/{org_id}` | Organization-wide active memory and governance. |
| `memory://product/{product_id}` | Product architecture, policies, and cross-repo knowledge. |
| `memory://repo/{repo_id}` | Repository conventions, local exceptions, and active specs. |
| `memory://spec/{spec_id}` | Feature memory, requirements, clarifications, tasks, and evidence. |
| `memory://adr/{adr_id}` | Architecture decision, alternatives, consequences, and linked events. |
| `memory://event/{event_id}` | Event details for audit and provenance when authorized. |

## Tools

| Tool | Purpose |
| --- | --- |
| `search_memory(query, scope, limit)` | Search active and deprecated memory with provenance. |
| `build_context_pack(task, scope, budget)` | Produce compact context for an active implementation or review. |
| `get_spec_context(spec_id)` | Return spec requirements, decisions, tasks, lessons, and open questions. |
| `list_recent_events(scope, event_types)` | Inspect recent event activity for a bounded scope. |
| `explain_memory(memory_id)` | Show why memory exists, which events support it, and what it supersedes. |

## Access policy

- MCP is read-only by default.
- Writes must go through Event Capture and Memory API endpoints.
- Runtime identity controls authorization and audit but must not create runtime-specific schemas.
- Responses include provenance, confidence, and deprecation warnings.

## Retrieval quality rules

- Prefer active memory over deprecated memory.
- Prefer higher-scope invariants unless a lower-scope exception applies.
- Return sources and known gaps, not just summaries.
- Bound response size to the requesting runtime's context budget.
