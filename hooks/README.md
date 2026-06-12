# Hooks contract

This repo uses hooks as enforcement and curation points, not as business logic.

## Hook map

- `PreToolUse` -> `python3 hooks/memory_hooks.py guard-write`
- `PostToolUse` -> `python3 hooks/memory_hooks.py validate-promotion`
- `PostToolUse` -> `python3 hooks/memory_event_poster.py`
- `Stop` -> `python3 hooks/memory_event_poster.py`
- `Stop` -> `python3 hooks/memory_hooks.py promote-ready --queue knowledge/_proposals`

The same utility also exposes `validate-proposal` when you want to check a draft proposal directly.

## Promotion contract

- `knowledge/_proposals/` is the staging area for draft knowledge updates.
- `status: draft` means the note is still being edited or reviewed.
- `status: ready` means the note has passed validation and is eligible for hook-driven promotion.
- `status: promoted` means the canonical copy exists at the target path.
- A ready proposal must already contain the final source-backed note content and a `target_path`.
- The hook promotes the note by copying it into the canonical bucket and then marking the draft as promoted.

## Hook policy

- Hooks should enforce invariants.
- Hooks should not decide architecture.
- Hooks should not invent knowledge.
- Hooks should only move source-backed information from transient work into the proposal queue or reject it.
- Hooks must not silently overwrite a canonical note with a different body.
- Hooks must fail closed if a proposal is missing a target path, source trail, or required metadata.

## Local ingestion wiring

- `hooks/memory_event_poster.py` posts hook payloads to `MEMORY_INGEST_API_URL`.
- The default target is `http://127.0.0.1:8081/v1/events`.
- The poster extracts repo, branch, commit, path, scope, session, and content when available.
- When the payload includes a Markdown file path, the poster reads the file body and forwards it as event content.
