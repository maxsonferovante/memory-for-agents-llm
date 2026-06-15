---
name: spec-memory-platform
description: Copilot reusable workflow for Spec Kit-first memory, event capture, and MCP context retrieval
---

# Spec Memory Platform Copilot skill

Use this skill when Copilot is asked to implement, review, or summarize work that affects memory, context, hooks, agents, skills, MCP, or Spec Kit artifacts.

## Workflow

1. Identify the Spec Kit phase.
2. Load repository instructions from `.github/copilot-instructions.md`.
3. Use MCP context if available: `build_context_pack`, `get_spec_context`, or `search_memory`.
4. Map the work to one or more shared event types.
5. Keep Copilot-specific guidance in `.github/` adapter files.
6. If durable memory changes, create a proposal under `knowledge/_proposals/`.
7. Run the smallest meaningful validation command.

## Event output

Report the event type, scope, artifact path, provenance, and validation evidence in the final response or PR summary.
