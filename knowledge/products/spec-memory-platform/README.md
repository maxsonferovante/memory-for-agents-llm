---
id: spec-memory-platform-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---

# Spec Memory Platform

## Mission

Spec Memory Platform is a runtime-agnostic memory, context, and continuous-learning platform for software-development agents. The platform is organized around GitHub Spec Kit artifacts, structured events, derived memory, and MCP retrieval so Claude Code, OpenAI Codex, GitHub Copilot, and future MCP-compatible runtimes can be replaced without changing the development process.

## Fundamental principle

The process is stable; the agent runtime is replaceable. The platform must be designed around specs, plans, tasks, ADRs, decisions, events, and memory instead of `CLAUDE.md`, Codex instructions, Copilot prompts, or any other runtime-specific instruction file.

## Mandatory Spec Kit flow

No customization may fork, rename, skip, reorder, or replace the official flow:

1. `/speckit.constitution`
2. `/speckit.specify`
3. `/speckit.clarify`
4. `/speckit.checklist`
5. `/speckit.plan`
6. `/speckit.tasks`
7. `/speckit.analyze`
8. `/speckit.implement`

Extensions must exist around this flow as adapters, validators, event producers, processors, retrieval tools, or documentation.

## Conceptual model

```text
Human
  -> Spec Kit
  -> Artifacts
  -> Event Capture
  -> Memory API
  -> Memory Processing
  -> Knowledge Base
  -> Context Retrieval
  -> Agent Runtime
```

## Architecture package

- [Architecture](./architecture.md)
- [Flows](./flows.md)
- [Event taxonomy and schemas](./event-taxonomy-and-schemas.md)
- [Memory taxonomy](./memory-taxonomy.md)
- [API design](./api-design.md)
- [MCP design](./mcp-design.md)
- [Runtime adapters](./runtime-adapters.md)
- [Current component review](./component-review.md)
- [Migration plan](./migration-plan.md)
- [Implementation planning](./implementation-planning.md)

## Decision records

- [ADR: Adopt Spec Kit artifacts as the platform boundary](../../adr/spec-kit-artifact-boundary.md)
- [ADR: Use events as the memory write contract](../../adr/spec-memory-event-contract.md)
- [ADR: Make MCP the official context consumption layer](../../adr/spec-memory-mcp-consumption.md)

## Non-goals

- Persisting raw conversations as durable memory.
- Making runtime prompts the architecture source of truth.
- Encoding business logic inside hooks.
- Creating specialized agents before a document, workflow, hook, skill, or MCP tool is proven insufficient.
