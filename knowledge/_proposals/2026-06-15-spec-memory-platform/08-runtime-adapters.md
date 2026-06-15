---
id: prop-spec-memory-platform-runtime-adapters-v1
type: proposal
scope: product
status: promoted
owner: spec-memory-platform
target_path: knowledge/products/spec-memory-platform/runtime-adapters.md
supersedes: null
confidence: high
promoted_to: knowledge/products/spec-memory-platform/runtime-adapters.md
promoted_at: 2026-06-15
---


# Runtime adapters

## Problem

The platform needs implementable Spec Kit-first documentation that replaces runtime-centric memory design with artifact, event, memory, and MCP contracts.

## Proposal

## Adapter contract

Every adapter translates runtime-specific signals into the shared event envelope. Adapters are replaceable and must avoid owning memory semantics.

## Claude Code

Claude Code may produce events through hooks, skills, and slash-command wrappers. It handles local generation, implementation, command execution, and hook invocation, not durable storage.

## OpenAI Codex

Codex may produce events through commands, hooks, and repository workflows. It consumes context through MCP and emits events for spec updates, task completion, analysis, implementation summaries, and review evidence.

## GitHub Copilot

Copilot may produce events from agent-mode actions, review comments, pull-request summaries, and implementation assistance after mapping observations to Spec Kit artifacts or review events.

## GitHub Actions and CI/CD

CI/CD adapters emit deterministic events for commits, pull requests, checks, releases, dependency changes, and validation outcomes.

## Pull requests and commits

Git adapters produce events from changed Spec Kit artifacts, ADRs, task files, implementation diffs, and merge metadata. Commit messages are metadata, not memory by themselves.

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
