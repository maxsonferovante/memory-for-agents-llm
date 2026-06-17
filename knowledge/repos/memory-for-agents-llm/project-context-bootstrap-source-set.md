---
id: prop-project-context-bootstrap-source-set-v1
type: canonical
scope: repo
status: active
owner: memory-curator
source:
  - ../../../hooks/memory_event_poster.py
  - ../../../DOCUMENTACAO.md
  - ../../../hooks/README.md
supersedes: null
confidence: high
reviewed_at: 2026-06-16
---


# Project context bootstrap source set

## Problem

The session bootstrap behavior now reads a fixed set of project operating documents, but that source set and its delivery semantics are easy to misunderstand. A reader may assume every file is posted as a separate event, when the implementation actually builds one consolidated bootstrap snapshot and sends canonical `knowledge/` files through a separate sync path.

## Proposal

Define the repo-local meaning of `PROJECT_CONTEXT_FILES`.

### Source set rule

- `PROJECT_CONTEXT_FILES` is the list of repository operating documents used to assemble the session bootstrap context.
- The list is intentionally biased toward instructions, repo overview, hook behavior, and local stack behavior rather than arbitrary project files.

### Delivery rule

- The bootstrap source-set files are read and concatenated into one synthetic context document.
- That synthetic document is sent as a `repo_handoff` event.
- The files in `PROJECT_CONTEXT_FILES` are not emitted as separate bootstrap events by default.

### Separation rule

- Canonical notes under `knowledge/` are re-sent through `canonical_sync`, not through the bootstrap source-set contract.
- Session work summaries and edit outcomes are captured through lifecycle events such as `session_stop` and `subagent_stop`.

## Consequences

- The bootstrap event remains compact and semantically clear.
- Canonical memory refresh stays independent from session-understanding context.
- The repo has an explicit explanation for what the startup context list means and does not mean.

## Sources

- [hooks/memory_event_poster.py](../../../hooks/memory_event_poster.py)
- [DOCUMENTACAO.md](../../../DOCUMENTACAO.md)
- [hooks/README.md](../../../hooks/README.md)

## Acceptance criteria

- The proposal states that `PROJECT_CONTEXT_FILES` feeds one synthetic bootstrap document.
- It states that the files are not emitted individually by default.
- It separates bootstrap context from canonical-memory sync.
