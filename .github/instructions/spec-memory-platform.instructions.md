---
applyTo: "**/*"
---

# Spec Memory Platform instructions

Use these instructions for Copilot Chat, Copilot coding agent, and Copilot code review when working in this repository.

## Default behavior

- Start from Spec Kit artifacts, not from an agent persona.
- Preserve the official Spec Kit flow exactly.
- Keep durable memory source-backed, scoped, and reviewable.
- Prefer hooks, skills, workflows, and MCP tools before proposing a new custom agent.

## Artifact mapping

- Constitution files map to `constitution.created` or `constitution.updated`.
- Spec files map to `spec.created`, `spec.updated`, `requirement.created`, or `requirement.updated`.
- Plan files map to `plan.created`, `architecture.decision.created`, or `dependency.selected`.
- Task files map to `tasks.generated`, `task.created`, or `task.completed`.
- Analysis files map to `analysis.completed` or `inconsistency.detected`.
- Review work maps to `review.completed`.
- Durable lessons map to `lesson.learned`, `improvement.suggested`, or memory events.

## Pull request review behavior

When reviewing a PR, check whether the change:

1. Preserves the official Spec Kit flow.
2. Emits or can be represented by a structured event.
3. Uses MCP as the read surface instead of direct database access by runtimes.
4. Keeps Copilot-specific guidance inside `.github/` adapter files.
5. Avoids adding agents when a hook, skill, workflow, MCP tool, or document is sufficient.
