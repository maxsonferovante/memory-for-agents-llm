---
id: spec-memory-platform-api-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---

# API design

## API boundaries

The Memory API is the write boundary. The Context Retrieval API is the read/query boundary used by MCP. Runtime adapters must not write directly to the database or bypass schema validation.

## Event Store API

| Endpoint | Purpose | Notes |
| --- | --- | --- |
| `POST /events` | Accept one event envelope. | Validates schema, scope, provenance, idempotency, and authorization. |
| `POST /events/batch` | Accept Git, PR, CI, or migration batches. | Returns accepted, duplicate, and rejected items. |
| `GET /events/{event_id}` | Fetch canonical event and processing status. | Useful for debugging adapters. |
| `GET /events` | Query events by scope, artifact, type, correlation, actor, or time. | Requires scoped authorization. |

## Memory Store API

| Endpoint | Purpose |
| --- | --- |
| `GET /memory/{memory_id}` | Return memory item, status, provenance, and supersession history. |
| `POST /memory/candidates` | Create candidate memory from events or curation. |
| `POST /memory/{memory_id}/accept` | Promote candidate memory into active memory. |
| `POST /memory/{memory_id}/deprecate` | Deprecate memory with replacement guidance. |
| `GET /memory` | Query memory by scope, tag, status, owner, spec, repo, product, or dependency. |

## Context Retrieval API

| Endpoint | Purpose |
| --- | --- |
| `POST /context/query` | Retrieve scoped memory and evidence for a question. |
| `POST /context/pack` | Build compact context for an active task and token budget. |
| `GET /context/spec/{spec_id}` | Return requirements, clarifications, tasks, ADRs, lessons, and active memory for a spec. |
| `GET /context/repo/{repo_id}` | Return repo conventions, local exceptions, active specs, and relevant product memory. |

## Processing API

| Endpoint | Purpose |
| --- | --- |
| `POST /processing/replay` | Rebuild projections and indexes from Event Store. |
| `POST /processing/reindex` | Rebuild retrieval indexes without rewriting events. |
| `GET /processing/status` | Report lag, failed events, projection versions, and index health. |

## Error model

- `400`: invalid schema or missing required artifact data.
- `401`/`403`: unauthenticated or unauthorized runtime/actor.
- `409`: duplicate event or idempotency conflict.
- `422`: valid JSON that cannot map to Spec Kit concepts.
- `503`: processing unavailable; ingestion may still accept append-only events if storage is healthy.
