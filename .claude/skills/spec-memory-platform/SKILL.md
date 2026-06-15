---
name: spec-memory-platform
description: Execute the Spec Memory Platform workflow by mapping Spec Kit artifacts into structured events, memory candidates, and MCP retrieval requests
---

# Spec Memory Platform skill

Use this skill when work must follow the Spec Kit-first memory platform instead of runtime-specific prompts, agents, or chat history.

## Core rule

The official flow is mandatory and must not be skipped or renamed:

1. `/speckit.constitution`
2. `/speckit.specify`
3. `/speckit.clarify`
4. `/speckit.checklist`
5. `/speckit.plan`
6. `/speckit.tasks`
7. `/speckit.analyze`
8. `/speckit.implement`

## Runtime-neutral workflow

1. Identify the active Spec Kit artifact: constitution, spec, clarification, checklist, plan, tasks, analysis, implementation, review, ADR, or memory.
2. Retrieve context through MCP first when available:
   - `build_context_pack(task, scope, budget)` for implementation or review work.
   - `get_spec_context(spec_id)` for feature work.
   - `search_memory(query, scope, limit)` for targeted memory lookup.
3. Produce or update the Spec Kit artifact in the repository.
4. Ensure the work can be represented as a structured event from the shared taxonomy.
5. If the work creates durable knowledge, create a proposal under `knowledge/_proposals/` and promote it with `python3 hooks/memory_hooks.py promote-ready --queue knowledge/_proposals`.
6. Keep runtime-specific notes out of canonical memory unless they describe an adapter contract.

## Event mapping quick reference

- Constitution changes: `constitution.created` or `constitution.updated`.
- Spec changes: `spec.created`, `spec.updated`, `requirement.created`, or `requirement.updated`.
- Clarification work: `clarification.requested` or `clarification.resolved`.
- Planning work: `plan.created`, `architecture.decision.created`, or `dependency.selected`.
- Task work: `tasks.generated`, `task.created`, or `task.completed`.
- Analysis work: `analysis.completed` or `inconsistency.detected`.
- Implementation work: `implementation.started` or `implementation.completed`.
- Review work: `review.completed`.
- Retrospective work: `lesson.learned` or `improvement.suggested`.
- Memory work: `memory.created`, `memory.updated`, `memory.deprecated`, or `memory.consolidated`.

## Output checklist

- Spec Kit artifact path.
- Event type that represents the change.
- Scope: session, feature, repo, product, or org.
- MCP context used or reason MCP was unavailable.
- Memory proposal path, if durable knowledge was produced.
- Validation command run.
