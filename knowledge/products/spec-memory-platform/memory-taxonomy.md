---
id: prop-spec-memory-platform-memory-taxonomy-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---


# Memory taxonomy

## Problem

The platform needs implementable Spec Kit-first documentation that replaces runtime-centric memory design with artifact, event, memory, and MCP contracts.

## Proposal

## Session Memory

Short-term memory for one working session. It captures active assumptions, local command results, and unresolved questions, then expires or summarizes into Feature Memory.

## Feature Memory

Memory for one Spec Kit feature. It links requirements, clarifications, plan decisions, task outcomes, implementation evidence, review outcomes, and lessons.

## Repository Memory

Repository-specific conventions, architecture constraints, build/test commands, and exceptions to product or organization rules.

## Product Memory

Knowledge shared across repositories in one product, including product architecture, dependency policy, domain constraints, release rules, and quality bars.

## Organizational Memory

Organization-wide engineering principles, security constraints, architecture standards, memory governance, naming conventions, and cross-product invariants.

## Promotion rules

Promote upward only when a fact is stable beyond its current scope. Keep exceptions at the lowest explanatory scope. Deprecate rather than delete when old context may still be retrieved.

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
