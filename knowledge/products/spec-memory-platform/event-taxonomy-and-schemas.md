---
id: spec-memory-platform-events-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---

# Event taxonomy and schemas

## Event envelope

All producers must emit the same envelope. Runtime-specific details belong in `producer` or adapter metadata, not in the event type system.

```json
{
  "event_id": "uuid-or-deterministic-id",
  "event_type": "spec.created",
  "schema_version": "1.0",
  "occurred_at": "2026-06-15T00:00:00Z",
  "producer": {
    "runtime": "claude-code|codex|copilot|github-actions|git|ci|manual",
    "adapter": "adapter-name",
    "version": "semver"
  },
  "scope": {
    "org": "org-id",
    "product": "product-id",
    "repository": "repo-name",
    "spec": "spec-id",
    "feature": "feature-id"
  },
  "actor": {
    "type": "human|agent|system",
    "id": "stable-actor-id"
  },
  "artifact": {
    "kind": "constitution|spec|clarification|checklist|plan|tasks|analysis|implementation|review|adr|memory",
    "path": "relative/path.md",
    "uri": "optional-canonical-uri",
    "version": "git-sha-or-artifact-version"
  },
  "correlation": {
    "session_id": "session-id",
    "trace_id": "trace-id",
    "parent_event_id": "optional-event-id",
    "pull_request": "optional-pr-number",
    "commit": "optional-git-sha"
  },
  "payload": {},
  "provenance": {
    "source_url": "optional-url",
    "evidence": ["paths", "commands", "checks"]
  }
}
```

## Taxonomy

| Category | Events |
| --- | --- |
| Constitution | `constitution.created`, `constitution.updated` |
| Specification | `spec.created`, `spec.updated`, `requirement.created`, `requirement.updated` |
| Clarification | `clarification.requested`, `clarification.resolved` |
| Planning | `plan.created`, `architecture.decision.created`, `dependency.selected` |
| Tasks | `tasks.generated`, `task.created`, `task.completed` |
| Analysis | `analysis.completed`, `inconsistency.detected` |
| Implementation | `implementation.started`, `implementation.completed` |
| Review | `review.completed` |
| Retrospective | `lesson.learned`, `improvement.suggested` |
| Memory | `memory.created`, `memory.updated`, `memory.deprecated`, `memory.consolidated` |

## Payload rules

- Payloads must describe Spec Kit artifacts, decisions, tasks, checks, and evidence.
- Raw conversations may be referenced as non-canonical provenance only when policy allows it.
- Event IDs should be deterministic for Git, PR, CI, and migration replays.
- Every memory-changing event must include scope, artifact, and provenance.
- Schema changes must be versioned and replayable.

## Example payloads

### `architecture.decision.created`

```json
{
  "adr_id": "adr-0042",
  "title": "Use MCP as context consumption layer",
  "status": "proposed",
  "decision_scope": "product",
  "alternatives": ["runtime-specific retrieval", "markdown-only context"],
  "consequences": ["runtimes consume one read surface", "database remains hidden"]
}
```

### `task.completed`

```json
{
  "task_id": "T-014",
  "spec_id": "spec-memory-platform",
  "summary": "Added event envelope validation",
  "changed_paths": ["local_stack/api/src/events.rs"],
  "checks": ["cargo check"]
}
```
