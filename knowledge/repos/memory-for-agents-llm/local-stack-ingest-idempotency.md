---
id: prop-local-stack-ingest-idempotency-v1
type: canonical
scope: repo
status: active
owner: memory-curator
supersedes: null
confidence: high
reviewed_at: 2026-06-12
---


# Local stack ingest idempotency candidate

## Problem

The local memory backend consumes hook events that may be replayed, retried, or emitted more than once for the same lifecycle moment. If event ids are derived from overly small seeds, duplicate `session_stop` events can collide on the database primary key. Separately, lifecycle events without Markdown content should not poison the worker queue.

## Proposal

Define a repo-local ingest contract for `hooks/memory_event_poster.py`, `local_stack/api/`, and `local_stack/worker.py`.

### Event identity rule

- The hook poster must not derive `event_id` from `event_type` alone.
- When the caller does not provide `id`, the poster must derive a stable id from the resolved event type plus repo, branch, commit, file path, session id, created_at, and content hash.
- Empty lifecycle events with neither content nor file path must be dropped at the poster layer instead of being posted as synthetic memory work.

### API idempotency rule

- The ingest API must treat `id` as an idempotency key.
- Replayed events with the same id must not surface as storage errors.
- Duplicate ingest requests should return an accepted response that makes the duplicate status explicit instead of failing with a primary-key violation.

### Worker handling rule

- The worker must not fail a queued event solely because it has no Markdown content.
- If an event reaches the worker without usable text, the worker should treat it as a no-op and mark it processed without producing derived memory output.

## Consequences

- Hook retries and duplicate lifecycle posts stop looking like backend failures.
- The API and worker gain a consistent contract for empty lifecycle events.
- Maintainers can distinguish real ingest bugs from benign event replays.

## Sources

- [hooks/memory_event_poster.py](../../../hooks/memory_event_poster.py)
- [local_stack/api/src/main.rs](../../../local_stack/api/src/main.rs)
- [local_stack/worker.py](../../../local_stack/worker.py)
- [hooks/README.md](../../../hooks/README.md)
- [local_stack/README.md](../../../local_stack/README.md)

## Acceptance criteria

- The proposal states that `event_id` must include more than the event type.
- It requires duplicate ingest handling in the API.
- It requires no-op handling for empty events in the worker.
