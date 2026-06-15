# Skills

Skills here are reusable workflows that Claude can load on demand.

## Spec Memory Platform skills

- `spec-memory-platform`: execute the Spec Kit-first memory workflow with event mapping and MCP retrieval.
- `context-pack`: compress sources into the smallest useful context bundle.
- `memory-curation`: turn repeated learning into canonical knowledge updates.
- `cross-repo-synthesis`: compare the same concept across repositories and produce a shared view.

## Rule of thumb

- Use a document, workflow, hook, skill, or MCP tool before creating a specialized agent.
- Use a skill when the workflow repeats.
- Use a subagent only when the task needs its own context window and has clear ROI.
- Use a rule when the behavior must always apply.
