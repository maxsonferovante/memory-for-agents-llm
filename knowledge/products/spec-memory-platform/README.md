---
id: prop-spec-memory-platform-readme-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---


# Spec Memory Platform

## Problem

The current memory architecture is useful but needs a Spec Kit-first target that is independent from Claude Code, Codex, Copilot, or any future runtime.

## Proposal

## Status

Proposed target architecture for replacing runtime-centric agent memory with a Spec Kit-oriented memory, context, and continuous-learning platform.

## Mission

Spec Memory Platform is a runtime-agnostic memory platform for software-development agents. GitHub Spec Kit artifacts define the process, and Claude Code, OpenAI Codex, GitHub Copilot, and future MCP-compatible agents are interchangeable producers and consumers.

## Fundamental principle

The process is stable; the agent runtime is replaceable. Customizations must surround the official Spec Kit flow and must not fork, rename, skip, or reorder it.

Official flow:

1. `/speckit.constitution`
2. `/speckit.specify`
3. `/speckit.clarify`
4. `/speckit.checklist`
5. `/speckit.plan`
6. `/speckit.tasks`
7. `/speckit.analyze`
8. `/speckit.implement`

## Conceptual model

```text
Human -> Spec Kit -> Artifacts -> Event Capture -> Memory API -> Memory Processing -> Knowledge Base -> Context Retrieval -> Agent Runtime
```

## Architecture documents

- [Architecture](./architecture.md)
- [Flows](./flows.md)
- [Event taxonomy and schemas](./event-taxonomy-and-schemas.md)
- [Memory taxonomy](./memory-taxonomy.md)
- [API design](./api-design.md)
- [MCP design](./mcp-design.md)
- [Runtime adapters](./runtime-adapters.md)
- [Current component review](./component-review.md)
- [Migration plan](./migration-plan.md)

## Decision records

- [ADR: Adopt Spec Kit artifacts as the platform boundary](../../adr/spec-kit-artifact-boundary.md)
- [ADR: Use events as the memory write contract](../../adr/spec-memory-event-contract.md)
- [ADR: Make MCP the official context consumption layer](../../adr/spec-memory-mcp-consumption.md)

## Non-goals

- Persisting raw chat logs as durable memory.
- Making runtime prompts or instructions the architectural source of truth.
- Encoding business logic inside hooks.
- Creating specialized agents before a hook, skill, workflow, or document is proven insufficient.

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
