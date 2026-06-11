---
id: prop-central-memory-api-contract-v1
type: proposal
scope: product
status: promoted
owner: cross-repo-coordinator
target_path: knowledge/integrations/central-memory-backend.md
supersedes: null
confidence: high
---

# Central memory API and agent contract v1

## Problem

The memory orchestrator needs one stable write path for repo-local memory files, and the agents need one stable read path for the latest published snapshot without scraping local workspace state.

## Proposal

Use a manifest-first full-snapshot contract.

- Hooks or tools build a complete memory package from the allowlisted memory files in the repo.
- The package is uploaded through API Gateway and Lambda to S3 using a pre-signed object URL.
- Lambda validates the manifest, tracks batch state, and publishes immutable snapshots.
- The first version uses full snapshots only, not deltas.
- Git remains the authoring source of truth; the AWS backend stores published snapshots and metadata.

## Contract

### Snapshot shape

- The ingestion unit is one complete memory snapshot for one repo.
- The archive format is `tar.gz`.
- The archive root includes `memory-manifest.json`.
- Every path in the manifest is repo-relative and normalized to POSIX separators.
- The default allowlist is:
  - `knowledge/**`
  - `.claude/**`
  - `hooks/**`
  - `CLAUDE.md`
  - `QUICKSTART.md`
  - `README.md`
- The upload must not include secrets, binaries, build outputs, caches, or unrelated source code.

### API surface

#### `POST /v1/memory-batches`

Creates a draft batch and returns a pre-signed upload URL.

Required headers:

- `Authorization`
- `Idempotency-Key`
- `X-Memory-Client`
- `X-Memory-Session`

Request body:

```json
{
  "schema_version": "1",
  "repo": {
    "name": "memory-for-agents-llm",
    "scope": "repo",
    "branch": "feature/central-memory-backend",
    "commit": "abc123"
  },
  "source": {
    "agent": "memory-curator",
    "trigger": "Stop",
    "session_id": "019eaf54-5f3f-7661-af56-069a23e70287"
  },
  "bundle": {
    "kind": "full",
    "sha256": "bundle-sha256",
    "size_bytes": 48211,
    "file_count": 17
  },
  "files": [
    {
      "path": "knowledge/org/memory-governance.md",
      "kind": "canonical",
      "status": "active",
      "sha256": "file-sha256",
      "size_bytes": 1324
    }
  ]
}
```

Response body:

```json
{
  "batch_id": "mb_01H...",
  "status": "draft",
  "upload": {
    "method": "PUT",
    "url": "https://signed-s3-upload-url",
    "expires_at": "2026-06-10T15:30:00Z"
  }
}
```

#### `PATCH /v1/memory-batches/{batch_id}`

Updates the batch state.

Request body:

```json
{
  "status": "ready",
  "review_note": "Validated by memory-curator"
}
```

- `draft` means uploaded or staged but not yet approved.
- `ready` means the batch passed validation and may be published.
- `rejected` means the batch will not be published in its current form.

#### `POST /v1/memory-batches/{batch_id}/publish`

Publishes a `ready` batch into an immutable snapshot.

If the same bundle hash is published again, the backend should return the same snapshot identifier instead of creating a duplicate record.

Response body:

```json
{
  "snapshot_id": "snap_01H...",
  "status": "published",
  "latest_pointer": "repos/memory-for-agents-llm/latest.json"
}
```

#### `GET /v1/repos/{repo_id}/snapshots/latest`

Returns the latest published snapshot metadata for a repo.

#### `GET /v1/snapshots/{snapshot_id}`

Returns the snapshot manifest and metadata for a published snapshot.

### Storage layout

- `s3://<bucket>/raw/{repo}/{batch_id}/bundle.tar.gz`
- `s3://<bucket>/manifests/{repo}/{snapshot_id}.json`
- `s3://<bucket>/indexes/{repo}/latest.json`
- `s3://<bucket>/indexes/{repo}/{snapshot_id}.json`

The bucket is append-only from the contract point of view. Published content is never overwritten in place.

### Agent usage

| Actor | Read latest snapshot | Create draft batch | Mark ready | Publish |
| --- | --- | --- | --- | --- |
| `context-researcher` | yes | no | no | no |
| `spec-analyst` | yes | no | no | no |
| `architect` | yes | no | no | no |
| `reviewer` | yes | no | no | no |
| `coordinator` | yes | yes | no | no |
| `PostToolUse` hook | yes | yes | no | no |
| `memory-curator` | yes | yes | yes | yes |
| `Stop` hook | yes | no | no | yes, if the batch is already `ready` |

### Agent rules

- `context-researcher` uses the read endpoints to build a context pack from the latest snapshot.
- `spec-analyst`, `architect`, and `reviewer` only read snapshots; they do not publish.
- `PostToolUse` captures a draft batch when a memory-producing action finishes.
- `memory-curator` validates the draft, flips it to `ready`, and only then allows publication.
- `Stop` promotes `ready` batches and refuses to publish anything still marked `draft`.
- The hook and the agent send only memory artifacts, not secrets, binaries, or unrelated code.

## Non-goals

- The backend does not replace Git as the authoring source.
- The backend does not edit canonical note text in place.
- The backend does not auto-merge semantic duplicates in v1.
- The backend does not need a search index to be useful on day one.

## Consequences

- The orchestrator gets one stable place to upload and retrieve memory snapshots.
- The contract stays simple enough to implement with Terraform, API Gateway, Lambda, and S3 only.
- The package may duplicate content that already exists in Git, but the duplication is intentional and immutable.
- Later search, semantic indexing, or graph layers can be derived from the published snapshots instead of being the primary store.

## Sources

- [knowledge/org/context-pack-contract.md](../../../knowledge/org/context-pack-contract.md)
- [knowledge/org/agent-memory-cycle.md](../../../knowledge/org/agent-memory-cycle.md)
- [knowledge/org/memory-curation-flow.md](../../../knowledge/org/memory-curation-flow.md)
- [knowledge/org/cross-repo-sharing-policy.md](../../../knowledge/org/cross-repo-sharing-policy.md)
- [hooks/README.md](../../../hooks/README.md)
- [knowledge/products/claude-code-memory-platform/shared-memory-contract.md](../../../knowledge/products/claude-code-memory-platform/shared-memory-contract.md)
- [knowledge/repos/memory-for-agents-llm/repo-local-memory-overrides.md](../../../knowledge/repos/memory-for-agents-llm/repo-local-memory-overrides.md)

## Acceptance criteria

- The API distinguishes `draft`, `ready`, and `published`.
- The upload is immutable once published.
- The batch includes a manifest and a complete file list.
- The allowed file set is explicit.
- The read path for agents is separate from the write path.
- The contract makes it clear that Git remains the source of truth for authoring.
