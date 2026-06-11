# Central Memory API (portable Rust backend)

This backend exposes the central memory service contract as a normal HTTP API that does not depend on AWS Lambda, API Gateway, or S3. It is intended for local validation and portable deployments where persistence can live in a mounted container volume.

## Runtime model

- HTTP server: Hyper on Tokio.
- Storage: filesystem under `MEMORY_BACKEND_STORAGE_DIR`.
- Upload flow: `POST /v1/memory-batches` returns a local `PUT /v1/uploads/{batch_id}/bundle` target instead of an S3 pre-signed URL.
- Publish flow: uploaded bundles are validated, immutable snapshot records are written, and `repos/{repo}/latest.json` is updated.
- Optional auth: set `MEMORY_BACKEND_AUTH_TOKEN` and send `Authorization: Bearer <token>` on every API request except `/healthz`.

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `MEMORY_BACKEND_BIND` | `0.0.0.0:8080` | Socket address used by the HTTP server. |
| `MEMORY_BACKEND_STORAGE_DIR` | `/data` | Root directory for batches, raw bundles, manifests, snapshots, and indexes. |
| `MEMORY_BACKEND_PUBLIC_URL` | unset | Optional base URL used to make upload URLs absolute. |
| `MEMORY_BACKEND_AUTH_TOKEN` | unset | Optional bearer token required by API routes. |
| `RUST_LOG` | `info` in Docker | Rust tracing filter. |

## Docker usage

Build the image:

```bash
docker build -t central-memory-api backend/central-memory-api
```

Run with a named volume:

```bash
docker run --rm \
  -p 8080:8080 \
  -e MEMORY_BACKEND_AUTH_TOKEN=dev-token \
  -e MEMORY_BACKEND_PUBLIC_URL=http://localhost:8080 \
  -v central-memory-data:/data \
  central-memory-api
```

Check the process:

```bash
curl http://localhost:8080/healthz
```

## API compatibility notes

The route names and JSON payloads match the v1 central memory contract, with one portability adjustment: the upload target is a local API route rather than an S3 pre-signed URL. Clients should use the `upload.method` and `upload.url` fields returned by `POST /v1/memory-batches` instead of assuming a cloud provider.

