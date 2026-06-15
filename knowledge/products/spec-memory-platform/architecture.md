---
id: spec-memory-platform-architecture-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---

# Spec Memory Platform architecture

## Architecture goals

- Capture knowledge produced during the official Spec Kit lifecycle.
- Transform artifact changes and execution observations into structured events.
- Persist events through a central Memory API.
- Derive memory from events; never treat raw chat as canonical memory.
- Share knowledge across sessions, repositories, products, and the organization.
- Expose context through MCP instead of direct database access.
- Allow the agent runtime to change without changing the platform architecture.

## Layered architecture

| Layer | Responsibility | Examples |
| --- | --- | --- |
| Spec Kit artifact layer | Owns the development process and durable work products. | Constitution, spec, clarifications, checklist, plan, tasks, analysis, implementation evidence. |
| Event Capture Layer | Converts runtime, Git, PR, and CI signals into one event schema. | Claude hook event, Codex command event, Copilot review event, PR merge event. |
| Memory API | Validates and stores append-only events and curated memory commands. | `POST /events`, idempotency, provenance, scope validation. |
| Memory Processing | Builds derived memories, graph edges, summaries, and retrieval indexes. | Requirement-to-task edges, ADR links, lesson candidates, embeddings. |
| Knowledge Base | Stores human-reviewable projections and canonical memory by scope. | `knowledge/specs`, `knowledge/adr`, product memory, repo memory. |
| Context Retrieval | Returns scoped context to tools and runtimes. | Context packs, spec context, decision history, lessons. |
| MCP server | Official runtime consumption layer. | `memory://spec/{id}`, `search_memory`, `build_context_pack`. |
| Runtime adapters | Produce events and consume MCP context. | Claude Code, Codex, Copilot, GitHub Actions. |

## Core data objects

| Object | Description | Persistence model |
| --- | --- | --- |
| Artifact | A Spec Kit or architecture document with a stable path and version. | Git-backed file plus artifact metadata. |
| Event | Immutable observation or state transition emitted by an adapter. | Append-only Event Store. |
| Memory item | Derived or curated reusable knowledge with scope and provenance. | Memory Store projection and Markdown projection. |
| Context pack | Bounded retrieval result for an active task. | Generated on demand; optionally cached. |
| Graph edge | Relationship between specs, requirements, tasks, decisions, dependencies, lessons, and memories. | Derived projection from events. |

## Runtime responsibility boundary

| Runtime | Responsible for | Not responsible for |
| --- | --- | --- |
| Claude Code | Generation, implementation, local execution, hook invocation. | Persistent memory storage, organizational knowledge ownership. |
| OpenAI Codex | Generation, implementation, command execution, MCP consumption. | Persistent memory storage. |
| GitHub Copilot | Generation, implementation assistance, review assistance. | Persistent memory storage. |
| GitHub Actions and CI/CD | Deterministic validation, PR, commit, release, and dependency evidence. | Semantic memory curation. |

## Write path

1. A Spec Kit artifact changes or a runtime/automation observes an important lifecycle event.
2. The adapter emits a structured event using the shared envelope.
3. The Memory API validates schema, scope, provenance, idempotency, and authorization.
4. The Event Store appends the accepted event.
5. Processing workers derive memories, summaries, graph edges, and retrieval chunks.
6. Human review or policy promotes candidate memory into the appropriate scope.

## Read path

1. A runtime requests context through MCP.
2. MCP calls the Context Retrieval API with runtime identity, task, scope, and budget.
3. Retrieval combines active memory, relevant events, artifact snippets, ADRs, and graph relationships.
4. MCP returns compact, source-backed context with provenance and deprecation warnings.

## Design constraints

- Events are immutable.
- Memory projections are rebuildable.
- Markdown is a reviewable projection, not the only storage contract.
- Hooks are thin adapters, not business-rule engines.
- Skills are bounded cognitive workflows, not durable memory stores.
- Agents are optional and require explicit ROI justification.
