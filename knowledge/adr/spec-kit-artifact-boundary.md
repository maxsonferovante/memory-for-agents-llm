---
id: adr-spec-kit-artifact-boundary-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---

# ADR: Adopt Spec Kit artifacts as the platform boundary

## Status

Accepted

## Context

The project supports multiple agent runtimes, but runtime-specific instruction files, prompts, and custom agents are not stable architectural boundaries. The target platform must survive replacement of Claude Code, Codex, Copilot, or any future agent runtime.

## Decision

Use GitHub Spec Kit artifacts as the platform boundary. Constitution, specs, clarifications, checklists, plans, tasks, analysis, implementation evidence, ADRs, reviews, events, and memory are the durable concepts. Runtime instructions are adapter configuration only.

## Consequences

- All extensions must surround the official Spec Kit flow without breaking it.
- Runtimes can be replaced if they can produce shared events and consume MCP context.
- Documentation, schemas, hooks, skills, and MCP tools must use Spec Kit language first.
- Runtime-specific files may remain for setup, but they cannot become canonical memory.

## Alternatives considered

- Continue centering architecture on Claude and Codex instructions. This preserves current ergonomics but makes runtime replacement expensive.
- Store raw conversations and summarize later. This captures more material but weakens provenance, governance, and replayability.
