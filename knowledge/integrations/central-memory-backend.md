---
id: central-memory-backend-integration-v1
type: canonical
scope: integration
status: active
owner: cross-repo-coordinator
source:
  - ../../../knowledge/_proposals/2026-06-10-central-memory-backend/02-central-memory-api-contract.md
  - ../../../knowledge/_proposals/2026-06-10-central-memory-backend/01-central-memory-backend-adr.md
  - ../../../knowledge/org/agent-memory-cycle.md
  - ../../../knowledge/org/context-pack-contract.md
  - ../../../knowledge/org/memory-curation-flow.md
supersedes: null
---

# Central memory backend

## Purpose

Provide a single AWS-hosted read/write surface for published memory snapshots while keeping Git as the authoring source of truth.

## What this backend is for

- Store immutable published snapshots for one repo or one memory namespace.
- Accept full-snapshot uploads produced by hooks or tools.
- Serve the latest published snapshot to memory-oriented agents.
- Preserve provenance through repo, branch, commit, session, and bundle hashes.

## What the agents do

### `context-researcher`

- Reads the latest published snapshot.
- Builds a context pack from the snapshot and canonical docs.
- Never writes to the backend.

### `spec-analyst`, `architect`, `reviewer`

- Read the latest published snapshot when they need background context.
- Do not create or publish memory batches.

### `coordinator`

- Decides whether a run produced durable memory.
- Can create a draft batch when the run generated promotable memory artifacts.
- Keeps the write path short and reviewable.

### `PostToolUse` hook

- Captures memory candidates after a memory-producing action completes.
- Packages the allowlisted files into a draft batch.
- Does not publish directly.

### `memory-curator`

- Validates the batch contents.
- Marks the batch `ready` only after the bundle matches the manifest and the contents are safe.
- Publishes the batch only when the state is already `ready`.

### `Stop` hook

- Finalizes a batch that is already `ready`.
- Refuses to publish anything still marked `draft`.

## Backend usage flow

1. A run produces a durable memory candidate.
2. The hook or coordinator builds a complete snapshot bundle.
3. The client calls `POST /v1/memory-batches` to create a draft batch.
4. The client uploads the tarball to the pre-signed object URL.
5. The curator validates the manifest and file list.
6. The curator marks the batch `ready`.
7. The `Stop` hook or publish step calls `POST /v1/memory-batches/{batch_id}/publish`.
8. Readers fetch `GET /v1/repos/{repo_id}/snapshots/latest`.

## Read contract

- Readers never scrape local workspace state as their primary source.
- Readers always prefer the latest published snapshot when a remote snapshot is available.
- Readers treat Git and canonical docs as the source of truth for authoring, not the backend.

## Write contract

- Writers upload full snapshots only.
- Writers include a manifest and a complete file list.
- Writers keep the bundle immutable after upload.
- Writers avoid secrets, caches, build outputs, and unrelated code.

## Storage model

- Raw bundles live under an append-only bucket prefix.
- Snapshot metadata is published as immutable JSON.
- The latest pointer is a derived reference, not a mutable content store.
- API access is controlled by an API key attached to a usage plan.
- The usage plan provides configurable burst and steady-state rate limits.

## Deployment model

- Terraform owns the backend lifecycle.
- AWS config owns the account, region, and credentials.
- The release package should ship the deployment instructions together with the app-side installer guidance.

## Non-goals

- This backend does not replace Git as the authoring source.
- This backend does not do in-place edits of canonical notes.
- This backend does not require semantic search on day one.
- This backend does not let arbitrary agents write directly without validation.

## Acceptance criteria

- The agent roles are explicit.
- The read path and write path are separated.
- The publish step is gated by a `ready` state.
- The backend is clearly defined as an immutable snapshot store.
- The deployment story references Terraform and AWS config for self-hosting.
- The access path requires an API key and supports configurable throttling.
