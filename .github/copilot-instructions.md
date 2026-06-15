# GitHub Copilot repository instructions

This repository uses the Spec Memory Platform. Copilot must treat GitHub Spec Kit artifacts as the stable process boundary and must not center durable knowledge on chat history or runtime-specific prompts.

## Mandatory Spec Kit flow

Do not skip, rename, reorder, or replace the official flow:

1. `/speckit.constitution`
2. `/speckit.specify`
3. `/speckit.clarify`
4. `/speckit.checklist`
5. `/speckit.plan`
6. `/speckit.tasks`
7. `/speckit.analyze`
8. `/speckit.implement`

## Copilot responsibilities

- Generate, implement, and review changes against Spec Kit artifacts.
- Prefer `knowledge/products/spec-memory-platform/` for platform architecture and contracts.
- Treat `.github/` Copilot files as runtime adapter guidance, not canonical memory.
- Emit durable learnings through source-backed proposals in `knowledge/_proposals/`.
- Use MCP context when available rather than relying on raw chat history.

## Event and memory rules

- Map work to the shared event taxonomy: specs, requirements, clarifications, plans, tasks, analysis, implementation, review, retrospective, and memory events.
- Never store raw conversation as canonical memory.
- Keep runtime-specific details in adapter metadata.
- If a change creates reusable knowledge, create or update a memory proposal and link it to the source files or PR evidence.

## Validation

For documentation or adapter changes, run the smallest meaningful checks available. For local stack Rust changes, run `cargo check` in the affected crate. For hook or script changes, run Python compilation and focused script tests.
