# Memory hooks

Hooks are the runtime-neutral event capture and validation layer for the Spec Memory Platform.

## Responsibilities

- `PreToolUse` -> `python3 hooks/memory_event_poster.py --bootstrap-once --sync-canonical`
- `PreToolUse` -> `python3 hooks/memory_hooks.py guard-write`
- `PostToolUse` -> `python3 hooks/memory_hooks.py validate-promotion`
- `PostToolUse` -> `python3 hooks/memory_event_poster.py --source <agent-hook-source> --ignore-errors`
- `SubagentStop` -> `python3 hooks/memory_event_poster.py --source codex-subagent-hook --event-type subagent_stop --ignore-errors`
- `Stop` -> `python3 hooks/memory_event_poster.py --source <agent-hook-source> --event-type session_stop --ignore-errors`
- `Stop` -> `python3 hooks/memory_hooks.py promote-ready --queue knowledge/_proposals`

Hooks must not contain product business logic. Business meaning belongs in Spec Kit artifacts, events, processors, and memory docs.

## Event capture

- The first hook event in a session should bootstrap repo understanding by posting a project-context snapshot and re-sending canonical `knowledge/` notes to the ingest API.
- Codex uses `PreToolUse` and `PostToolUse` on `.*`, with the runner suppressing no-op cases when no path exists.
- Claude Code uses the same broad `.*` matcher after installation, with the runner also suppressing no-op cases when no path exists.
- `Stop` remains the safety net for session handoff and promotion.

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

- `hooks/memory_event_poster.py` posts hook payloads to `MEMORY_INGEST_API_URL`.
- The default target is `http://127.0.0.1:8080/api/v1/events`.
- The Codex and Claude installers now pass the same endpoint explicitly with `--url` after deriving it from `--stack-host`.
- Use `--source claude-code-hook`, `--source codex-code-hook`, or another explicit source to preserve provenance.
- Use `--event-type` for lifecycle hooks whose payload does not include a path or event type.
- Use `--ignore-errors` for global hooks so Codex is not blocked when the local memory API is offline.
- The poster extracts repo, branch, commit, path, scope, session, and content when available.
- When the payload includes a Markdown file path, the poster reads the file body and forwards it as event content.
- When a session stops without an explicit file payload, the poster synthesizes a work summary from the current repository state.
- When ready proposals are promoted, the canonical target must be posted back to the ingest API as `memory_promoted`.
- The Stop hook remains a safety net, but `memory-curation` sessions are expected to run promotion immediately instead of waiting for a separate user confirmation.
