---
id: prop-spec-memory-platform-architecture-v1
type: proposal
scope: product
status: promoted
owner: spec-memory-platform
target_path: knowledge/products/spec-memory-platform/architecture.md
supersedes: null
confidence: high
promoted_to: knowledge/products/spec-memory-platform/architecture.md
promoted_at: 2026-06-15
---


# Spec Memory Platform architecture

## Problem

The current memory architecture is useful but needs a Spec Kit-first target that is independent from Claude Code, Codex, Copilot, or any future runtime.

## Proposal

## Goals

- Capture knowledge produced during the official Spec Kit lifecycle.
- Convert artifact changes and runtime observations into structured events.
- Persist events through a central Memory API.
- Derive memory from events instead of from conversations.
- Share knowledge across sessions, repositories, products, and the organization.
- Retrieve context through MCP rather than direct database access.
- Allow Claude Code, Codex, Copilot, and future runtimes to be replaced without architectural impact.

## Core components

### Spec Kit artifact layer

The artifact layer contains the durable work products of the process: constitution, specs, clarifications, checklists, plans, tasks, analysis outputs, implementation summaries, ADRs, and review notes. These artifacts are the canonical input to memory.

### Event Capture Layer

The Event Capture Layer is the only write-facing adapter boundary for runtimes and automation. It receives events from Claude Code hooks, Claude skills, Claude slash commands, Codex commands, GitHub Actions, GitHub Copilot agent flows, pull requests, commits, and CI/CD systems. All producers emit the same envelope and payload schema.

### Memory API

The Memory API owns validation, idempotency, provenance, tenant/project boundaries, and append-only event persistence. It rejects runtime-specific payloads that cannot be mapped to Spec Kit concepts.

### Memory Processing

Processing jobs normalize events, detect duplicates, derive facts, generate candidate memory updates, build graph edges, and update retrieval indexes. Processing is asynchronous and replayable from the Event Store.

### Knowledge Base

The Knowledge Base contains human-reviewable memory organized by session, feature, repository, product, and organization. Markdown remains useful for review and Git workflows, but it is a projection of structured events rather than the only system of record.

### Context Retrieval API and MCP server

The Context Retrieval API serves scoped context packs, related decisions, task history, dependency decisions, lessons, and deprecation notices. MCP is the official consumption surface for agent runtimes.

## Data ownership

- Events are append-only and owned by the Memory API.
- Memory is derived and can be regenerated from events.
- Runtime config is operational glue, not durable knowledge.
- ADRs document accepted architectural decisions and link to source events.

## Runtime responsibility boundary

| Runtime | Responsible for | Not responsible for |
| --- | --- | --- |
| Claude Code | generation, implementation, local execution, hooks | persistent memory, organizational knowledge ownership |
| Codex | generation, implementation, execution | persistent memory |
| GitHub Copilot | generation, implementation, review assistance | persistent memory |
| GitHub Actions/CI | deterministic event production and validation signals | semantic memory curation |

## Extension policy

Extensions may add event producers, validators, processors, retrieval tools, and documentation around the Spec Kit flow. Extensions must not replace the official command sequence or make a runtime-specific prompt the source of truth.

## Consequences

- The platform boundary moves from runtime-specific instructions to Spec Kit artifacts, events, memory, and MCP.
- Runtime assets become adapters and optional UX conveniences.
- Future implementation can evolve the local stack without changing the official Spec Kit flow.

## Sources

- [AGENTS.md](../../../AGENTS.md)
- [README.md](../../../README.md)
- [knowledge/README.md](../../../knowledge/README.md)
- [local_stack/README.md](../../../local_stack/README.md)

## Acceptance criteria

- The proposal preserves the official Spec Kit flow.
- The proposal treats runtimes as replaceable producers and consumers.
- The proposal defines durable knowledge outside runtime-specific prompts.
