---
id: spec-memory-platform-runtime-adapters-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---

# Runtime adapters

## Adapter contract

Every adapter translates runtime-specific signals into the shared event envelope and retrieves context through MCP. Adapters must be thin, replaceable, and free of durable memory semantics.

## Claude Code adapter

- Produces events through hooks, skills, and slash-command wrappers.
- Captures local command evidence and artifact updates.
- Consumes context through MCP resources and tools.
- Does not own persistent memory or organizational knowledge.

## OpenAI Codex adapter

- Produces events through commands, hooks, and repository workflows.
- Emits events for spec updates, task completion, analysis, implementation summaries, and review evidence.
- Consumes context through MCP.
- Does not write directly to memory storage.

## GitHub Copilot adapter

- Produces events from agent-mode activity, review comments, PR summaries, and implementation assistance.
- Maps observations to Spec Kit artifacts, tasks, or review events before ingestion.
- Consumes context through MCP where supported.

## GitHub Actions and CI/CD adapter

- Produces deterministic events for commits, pull requests, checks, releases, dependency changes, and validation outcomes.
- Uses deterministic event IDs so reruns are idempotent.
- Provides high-confidence evidence for implementation and review memory.

## Pull request and commit adapter

- Detects changed Spec Kit artifacts, ADRs, task files, implementation diffs, and merge metadata.
- Emits events linked to commit SHA, PR number, and changed paths.
- Treats commit messages as metadata, not durable memory by themselves.

## Adapter acceptance checklist

- Emits the shared envelope.
- Includes artifact path and version when applicable.
- Includes scope and provenance.
- Handles retries idempotently.
- Uses MCP for reads.
- Contains no platform-specific business logic beyond translation.
