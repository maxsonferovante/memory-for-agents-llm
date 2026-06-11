---
id: claude-code-memory-platform-backend-deployment-tutorial-v1
type: canonical
scope: product
status: active
owner: cross-repo-coordinator
source:
  - ../../../knowledge/integrations/central-memory-backend.md
  - ../../../knowledge/products/claude-code-memory-platform/distribution-plan.md
  - ../../../knowledge/products/claude-code-memory-platform/installation-contract.md
  - ../../../knowledge/products/claude-code-memory-platform/release-checklist.md
supersedes: null
---

# Backend deployment tutorial

## Goal

Show a third party how to deploy the central memory backend into their own AWS account and point the local agents at that backend.

## Audience

- A developer who wants a private self-hosted memory backend.
- A team that wants the repo plus backend as a reproducible install.

## Prerequisites

- An AWS account with permission to create S3, Lambda, API Gateway, IAM, and logging resources.
- `aws` CLI configured with a profile and region.
- `terraform` installed.
- Rust toolchain installed.
- `cargo lambda` installed with `cargo install cargo-lambda`, or Docker installed so the build script can compile inside a Linux container.
- The release artifact for this repo or the backend bundle generated from the tagged release.

## Deployment steps

1. Download the versioned release artifact.
2. Inspect the release manifest and confirm the version/tag.
3. Configure AWS credentials and region for the target account, for example `export AWS_PROFILE=your-profile` and `export AWS_REGION=us-east-1`.
4. Choose an API key value and rate limits for the usage plan.
5. Run the one-step release script that builds the Rust Lambda zip artifact and applies the Terraform stack.
6. Capture the generated `backend.env` file and source it in the local shell.
7. Configure the local Claude environment to point to the backend base URL and `x-api-key` value.
8. Run the smoke test helper to prove the write path end to end.
9. Run the memory install flow in dry-run mode before enabling publication.
10. Publish one test snapshot and verify the latest-read path.

## Terraform contract

- The stack must be reproducible from the release artifact and its manifest.
- The stack must name the bucket, API, Lambda, and IAM resources explicitly.
- The stack must surface outputs for the API base URL, bucket name, and region.
- The stack must accept an API key value and usage-plan rate limits as inputs.
- The stack must not require hidden manual console steps after apply.

## API key contract

- The API key is supplied as `api_key_value` during Terraform apply.
- The release script writes a sourceable `backend.env` file with `API_BASE_URL`, `API_KEY_VALUE`, and `API_KEY_HEADER=x-api-key`.
- The local client must send the key in the `x-api-key` header on every request.
- The usage plan controls the steady-state and burst limits for that key.
- The hook runtime loads `backend.env` automatically when it exists, so the same environment is available to write and read helpers.

## AWS config contract

- Credentials should come from the normal AWS shared config chain.
- The tutorial should document the exact profile name or environment variables to use.
- The user should be able to target a separate account for test and production.

## Agent wiring contract

- The local installer should know where the backend base URL lives.
- The memory curator should know when to create a batch and when to publish it.
- The reader agents should know how to fetch the latest published snapshot.
- The tutorial should show one smoke test for read and one smoke test for write.

## Smoke test

1. Create a tiny memory bundle with one canonical markdown file.
2. Upload it through the batch creation endpoint.
3. Mark the batch `ready`.
4. Publish the batch.
5. Fetch the latest snapshot and confirm the file is present.

## Command sequence

```bash
export AWS_PROFILE=your-profile
export AWS_REGION=us-east-1
export API_KEY_VALUE=replace-with-a-secret
python3 scripts/release_central_memory_backend.py \
  --aws-region "${AWS_REGION}" \
  --api-key-value "${API_KEY_VALUE}" \
  --usage-plan-rate-limit 10 \
  --usage-plan-burst-limit 20 \
  --auto-approve
source dist/backend/central-memory-backend/backend.env
echo "$API_BASE_URL"
echo "$API_KEY_HEADER"
python3 scripts/smoke_test_central_memory_backend.py --env-file dist/backend/central-memory-backend/backend.env
```

If you want bearer-token protection on the Lambda, export `BACKEND_AUTH_TOKEN=change-me` before running the release script. That is optional and separate from the API key.

## Example write smoke test

```bash
curl -X POST "$API_BASE_URL/v1/memory-batches" \
  -H "content-type: application/json" \
  -H "x-api-key: $API_KEY_VALUE" \
  -H "idempotency-key: test-001" \
  -H "x-memory-client: tutorial" \
  -H "x-memory-session: session-001" \
  -d @batch-request.json
```

## Outcome

After this tutorial is complete, a non-author should be able to run the backend in their own AWS account and use it as the central memory store for the agents.

## Portable Docker backend preview

A provider-agnostic Rust API is available under `backend/central-memory-api` for local validation and non-AWS deployments. It keeps the same v1 batch, upload, publish, latest, and snapshot routes, but writes all objects to `MEMORY_BACKEND_STORAGE_DIR` and returns a local `PUT /v1/uploads/{batch_id}/bundle` upload target instead of an S3 pre-signed URL.

```bash
docker build -t central-memory-api backend/central-memory-api
docker run --rm \
  -p 8080:8080 \
  -e MEMORY_BACKEND_AUTH_TOKEN=dev-token \
  -e MEMORY_BACKEND_PUBLIC_URL=http://localhost:8080 \
  -v central-memory-data:/data \
  central-memory-api
curl http://localhost:8080/healthz
```

Use this backend when the goal is to validate the memory API contract in a portable container before choosing a production object store or cloud-specific deployment target.
