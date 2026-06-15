---
id: spec-memory-platform-implementation-planning-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---

# Implementation planning

## Planning objective

This plan converts the target architecture into executable work while preserving the official Spec Kit flow. It is intentionally organized by platform capability rather than by Claude Code, Codex, or Copilot.

## Workstreams

| Workstream | Outcome | Primary artifacts |
| --- | --- | --- |
| Spec Kit contracts | Stable artifact and event language. | Constitution, specs, event schema, ADRs. |
| Event Capture Layer | Runtime and automation events converge into one schema. | Hook adapters, command adapters, GitHub Actions adapters. |
| Memory API | Central validated write path. | Event Store API, Memory Store API, idempotency rules. |
| Processing | Events become memory, graph edges, summaries, and indexes. | Workers, replay jobs, projection definitions. |
| MCP retrieval | Runtimes consume context through one read layer. | MCP resources, MCP tools, retrieval policies. |
| Runtime simplification | Runtime assets become adapters and optional UX. | Minimal Claude/Codex/Copilot wiring docs. |
| Governance | Memory remains source-backed and reviewable. | Promotion rules, deprecation rules, ownership model. |

## Milestone 1: Documentation and contracts

### Tasks

- Finalize Spec Kit artifact boundary ADR.
- Finalize event write contract ADR.
- Finalize MCP consumption ADR.
- Define event envelope JSON schema.
- Define memory item JSON schema.
- Define context-pack response schema.
- Define adapter acceptance checklist.

### Exit criteria

- Every event type has an owner, payload shape, and source artifact.
- Every memory scope has promotion and deprecation rules.
- Every runtime integration can be evaluated against the same adapter contract.

## Milestone 2: Event ingestion foundation

### Tasks

- Add Event Store persistence to the local stack.
- Implement `POST /events` and `POST /events/batch`.
- Add idempotency keys based on event type, artifact version, commit, PR, and producer.
- Add schema validation and clear `422` errors for events that cannot map to Spec Kit concepts.
- Add audit fields for runtime, actor, and provenance.

### Exit criteria

- Claude, Codex, GitHub Actions, and manual producers can submit equivalent test events.
- Replayed Git/CI events do not create duplicates.
- Invalid runtime-specific memory payloads are rejected.

## Milestone 3: Adapter conversion

### Tasks

- Convert existing Claude hook output into shared events.
- Convert existing Codex hook output into shared events.
- Add GitHub Actions event producer for PR open/update/merge and CI completion.
- Add commit scanner for Spec Kit artifact, ADR, and task changes.
- Document Copilot event mapping for review comments and PR summaries.

### Exit criteria

- Adapter code contains translation only.
- No adapter writes directly to canonical memory.
- All adapters include artifact path, scope, correlation, and provenance.

## Milestone 4: Memory processing and projections

### Tasks

- Build projection workers for Session, Feature, Repository, Product, and Organizational Memory.
- Generate candidate memories from repeated events and completed features.
- Generate graph edges for requirements, tasks, ADRs, dependencies, reviews, and lessons.
- Add replay command to rebuild projections from Event Store.
- Keep Markdown projections for human review.

### Exit criteria

- Memory can be regenerated from events.
- Candidate memory includes source events and owner.
- Deprecated memory includes replacement guidance.

## Milestone 5: MCP retrieval

### Tasks

- Add MCP resources for org, product, repo, spec, ADR, and event context.
- Add tools for memory search, context-pack generation, spec context, recent events, and memory explanation.
- Add retrieval ranking that respects scope hierarchy and deprecations.
- Add response budgets for different runtimes.

### Exit criteria

- Claude Code, Codex, and a generic MCP client can retrieve the same spec context.
- MCP responses include provenance, confidence, and known gaps.
- Runtimes do not need database credentials.

## Milestone 6: Runtime asset simplification

### Tasks

- Reduce custom agents to documented optional UX.
- Move durable runtime instructions into Spec Kit docs, ADRs, or memory docs.
- Keep only adapter setup, hook wiring, and MCP discovery in runtime config files.
- Add an agent justification template for any future custom agent.

### Exit criteria

- The platform can be explained without referencing Claude-specific or Codex-specific instructions.
- New runtimes only need event production and MCP consumption.

## Milestone 7: Operational hardening

### Tasks

- Add schema version migration policy.
- Add event replay smoke tests.
- Add projection freshness metrics.
- Add MCP retrieval quality checks.
- Add authorization and tenancy boundaries.
- Add runbooks for failed ingestion, replay, projection drift, and MCP outage.

### Exit criteria

- Operators can detect ingestion lag, projection failures, stale indexes, and MCP errors.
- Recovery does not require runtime-specific knowledge.
- The platform is ready for cross-repository and cross-product rollout.

## Dependency order

1. ADRs and schemas.
2. Event Store and ingestion API.
3. Runtime and automation adapters.
4. Processing projections.
5. MCP retrieval.
6. Runtime simplification.
7. Governance and operations.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Runtime adapters leak business logic. | Enforce adapter checklist and reject non-Spec payloads. |
| Event schema becomes too generic. | Require artifact kind, event type, scope, and provenance for all events. |
| Memory quality degrades from noisy events. | Use candidate memory, owners, confidence, and review states. |
| MCP context becomes too large. | Enforce budgets and context-pack assembly rules. |
| Migration duplicates existing memory. | Use idempotency keys, supersession links, and deprecation workflow. |
