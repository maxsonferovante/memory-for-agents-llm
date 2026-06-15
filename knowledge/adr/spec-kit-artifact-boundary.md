---
id: prop-adr-spec-kit-artifact-boundary-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---


# ADR: Adopt Spec Kit artifacts as the platform boundary

## Problem

The platform needs implementable Spec Kit-first documentation that replaces runtime-centric memory design with artifact, event, memory, and MCP contracts.

## Proposal

## Status

Proposed

## Context

The existing project supports multiple agent runtimes, but some operating guidance is organized around Claude Code, Codex, and their prompt or agent files. The target platform must survive replacement of any runtime.

## Decision

Use GitHub Spec Kit artifacts as the architectural boundary. Constitution, specs, clarifications, checklists, plans, tasks, analysis, implementation evidence, ADRs, reviews, events, and memory are the durable concepts. Runtime instructions are adapters only.

## Alternatives considered

- Continue centering the platform on Claude and Codex instructions.
- Store raw conversations and summarize them later.

## Consequences

- All extensions must surround the official Spec Kit flow without breaking it.
- Runtimes can be replaced if they can produce and consume the shared artifacts and events.
- Documentation, schemas, hooks, skills, and MCP tools must use Spec Kit language first.

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
