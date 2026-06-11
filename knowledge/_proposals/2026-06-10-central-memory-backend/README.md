# Central memory backend package

This package captured the first draft for an AWS-backed central memory ingest path.
It is intentionally split into an architecture decision and an integration contract so each file can be reviewed independently.

## Bundle order

1. Backend architecture decision
2. Central memory API and agent usage contract

## Promotion result

- The architecture choice was promoted into `knowledge/adr/central-memory-backend.md`.
- The API and agent contract was promoted into `knowledge/integrations/central-memory-backend.md`.
- Keep Git as the authoring source and the AWS backend as an immutable snapshot mirror.

## Review rule

- A reviewer should be able to evaluate each file in one pass.
- The package is valid only when the backend contract states the ingestion unit, upload/finalize flow, immutable storage layout, agent write permissions, and non-goals.
