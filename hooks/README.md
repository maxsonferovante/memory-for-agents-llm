# Memory hooks

Hooks are the runtime-neutral event capture and validation layer for the Spec Memory Platform.

## Responsibilities

- Capture runtime, tool, and lifecycle signals as structured Spec Memory events.
- Guard unsafe direct writes to canonical knowledge.
- Validate memory proposals before promotion.
- Promote ready proposals into canonical memory.

Hooks must not contain product business logic. Business meaning belongs in Spec Kit artifacts, events, processors, and memory docs.

## Event capture

`hooks/memory_event_poster.py` reads a runtime hook payload from stdin and emits a Spec Memory Platform envelope to the Memory API. The emitted payload keeps legacy fields for the current local stack while also adding:

- `event_id`
- `schema_version`
- `occurred_at`
- `producer`
- `actor`
- `artifact`
- `correlation`
- `payload`
- `provenance`

The poster infers Spec Kit event types such as `spec.updated`, `plan.created`, `tasks.generated`, `architecture.decision.created`, `implementation.completed`, and `memory.consolidated` from the changed artifact path and content.

## Validation and promotion

`hooks/memory_hooks.py` remains the canonical proposal validation and promotion utility:

- `guard-write --path <path>` blocks direct writes to canonical memory paths.
- `validate-proposal <path>` validates source-backed memory candidates.
- `promote-ready --queue knowledge/_proposals` promotes ready proposals.

## Codex wiring

`.codex/hooks.json` wires Codex lifecycle events to:

- pre-write canonical memory guardrails;
- post-tool Spec Memory event capture;
- proposal validation;
- stop-time session event capture;
- ready proposal promotion.


## GitHub Copilot and GitHub Actions wiring

`.github/copilot-instructions.md`, `.github/instructions/`, `.github/prompts/`, `.github/agents/`, and `.github/skills/` provide Copilot adapter guidance for the Spec Memory Platform. `.github/workflows/spec-memory-copilot-events.yml` runs `scripts/copilot_event_capture.py` on pull request, pull request review, and check-suite events so Copilot-assisted work can be represented as structured Spec Memory events.
