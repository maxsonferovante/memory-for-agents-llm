---
id: prop-spec-memory-platform-component-review-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---


# Current component review

## Problem

The platform needs implementable Spec Kit-first documentation that replaces runtime-centric memory design with artifact, event, memory, and MCP contracts.

## Proposal

## Summary

The current repository is valuable as a phase-1 reference, but it is runtime-centric in several places. The target design keeps durable knowledge, hooks, skills, MCP, and the local stack, while demoting agents and runtime instruction files to adapters or examples.

## Component decisions

| Component | Problem solved today | Keep? | Target action |
| --- | --- | --- | --- |
| `knowledge/` | Durable Markdown knowledge across scopes | Yes | Keep as Knowledge Base projection aligned to Spec, ADR, Event, and Memory taxonomy. |
| `knowledge/_proposals/` | Draft memory and ADR updates | Yes | Keep as candidate-memory workflow connected to source events. |
| `knowledge/specs/` | SDD specs and history | Yes | Make it the primary feature-memory anchor. |
| `knowledge/adr/` | Architecture decisions | Yes | Keep; emit `architecture.decision.created` events. |
| `hooks/` | Enforcement, ingestion, promotion | Yes | Keep only for event capture, mandatory validation, memory updates, and summary generation. |
| `local_stack/` | Local API, worker, and MCP | Yes | Evolve into Event Store, Memory Store, Processing, and MCP reference implementation. |
| `.agents/skills/` | Reusable Codex workflows | Yes | Keep for decision classification, ADR generation, implementation summaries, memory consolidation, and context retrieval. |
| `.claude/skills/` | Claude reusable workflows | Conditional | Keep as Claude adapter packaging for the same responsibilities. |
| `.claude/agents/` | Specialized Claude subagents | Reduce | Remove or archive unless simpler mechanisms cannot solve the problem. |
| `.codex/agents/` | Specialized Codex subagents | Reduce | Treat as optional runtime convenience. |
| `CLAUDE.md` | Claude operating rules | Adapter only | Keep minimal runtime adapter instructions. |
| `CODEX.md` and `.codex/config.toml` | Codex operating config | Adapter only | Keep operational config and MCP discovery. |
| `.github/workflows/` | PR and image automation | Yes | Add event-producing workflows for PR, commit, CI, and release evidence. |
| Installer scripts | Copy runtime assets locally | Conditional | Keep during migration; reduce once MCP and adapters are discoverable. |
| Session templates | Repeatable agent prompts | Conditional | Replace durable guidance with Spec Kit artifact templates. |

## Agents policy

Assume no custom agents are needed by default. A new agent requires a documented reason, operational cost, and simpler alternative analysis. Prefer document, workflow, hook, skill, MCP tool, then agent.

## Hooks policy

Hooks are preferred over agents only for event capture, mandatory validation, memory updates, and summary generation. Hooks must not contain product business logic.

## Skills policy

Skills should perform bounded cognitive workflows: classify decisions, generate ADRs, summarize implementation, consolidate memory, and retrieve context.

## Consequences

- Implementers get a concrete target contract.
- Runtime-specific code can be simplified into adapters.
- Memory remains derived from structured evidence rather than raw conversations.

## Sources

- [AGENTS.md](../../../AGENTS.md)
- [README.md](../../../README.md)
- [hooks/memory_hooks.py](../../../hooks/memory_hooks.py)
- [knowledge/org/knowledge-scope-model.md](../../../knowledge/org/knowledge-scope-model.md)

## Acceptance criteria

- The document is runtime-agnostic.
- The document keeps Spec Kit artifacts as the process source of truth.
- The document defines a clear migration or implementation contract.
