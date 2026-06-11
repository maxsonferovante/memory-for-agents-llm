use std::{collections::HashSet, env, io::Read, sync::Arc, time::Duration};

use aws_sdk_s3::{presigning::PresigningConfig, Client};
use flate2::read::GzDecoder;
use http::{Method, StatusCode};
use lambda_http::{run, service_fn, Body, Error, Request, Response};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use tar::Archive;
use thiserror::Error;
use time::OffsetDateTime;
use tracing_subscriber::EnvFilter;
use uuid::Uuid;

#[derive(Clone)]
struct AppState {
    s3: Client,
    bucket: String,
    stage_name: String,
    auth_token: Option<String>,
}

#[derive(Debug, Deserialize)]
struct CreateBatchRequest {
    schema_version: String,
    repo: RepoRef,
    source: SourceRef,
    bundle: BundleRef,
    files: Vec<FileRef>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct RepoRef {
    name: String,
    scope: String,
    branch: String,
    commit: String,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct SourceRef {
    agent: String,
    trigger: String,
    session_id: String,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct BundleRef {
    kind: String,
    sha256: String,
    size_bytes: u64,
    file_count: usize,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct FileRef {
    path: String,
    kind: String,
    status: String,
    sha256: String,
    size_bytes: u64,
}

#[derive(Debug, Deserialize, Serialize, Clone, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
enum BatchStatus {
    Draft,
    Ready,
    Rejected,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct BatchRecord {
    batch_id: String,
    schema_version: String,
    repo: RepoRef,
    source: SourceRef,
    bundle: BundleRef,
    files: Vec<FileRef>,
    status: BatchStatus,
    review_note: Option<String>,
    created_at: String,
    updated_at: String,
    bundle_key: String,
    latest_pointer_key: String,
}

#[derive(Debug, Deserialize)]
struct UpdateBatchRequest {
    status: BatchStatus,
    review_note: Option<String>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct SnapshotRecord {
    snapshot_id: String,
    batch_id: String,
    repo: RepoRef,
    source: SourceRef,
    bundle: BundleRef,
    files: Vec<FileRef>,
    status: String,
    published_at: String,
    bundle_key: String,
    manifest_key: String,
    latest_pointer_key: String,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct MemoryManifest {
    schema_version: String,
    repo: RepoRef,
    source: SourceRef,
    bundle: BundleRef,
    files: Vec<FileRef>,
}

#[derive(Debug, Deserialize, Serialize)]
struct LatestPointer {
    repo: String,
    snapshot_id: String,
    snapshot_key: String,
    updated_at: String,
}

#[derive(Debug, Serialize)]
struct UploadResponse {
    batch_id: String,
    status: String,
    upload: PresignedUpload,
}

#[derive(Debug, Serialize)]
struct PresignedUpload {
    method: String,
    url: String,
    expires_at: String,
}

#[derive(Debug, Serialize)]
struct PublishResponse {
    snapshot_id: String,
    status: String,
    latest_pointer: String,
}

#[derive(Debug, Serialize)]
struct ErrorResponse {
    error: String,
    message: String,
}

#[derive(Debug, Error)]
enum AppError {
    #[error("{0}")]
    BadRequest(String),
    #[error("not found: {0}")]
    NotFound(String),
    #[error("forbidden: {0}")]
    Forbidden(String),
    #[error("internal error: {0}")]
    Internal(String),
}

type AppResult<T> = Result<T, AppError>;

#[tokio::main]
async fn main() -> Result<(), Error> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env())
        .json()
        .with_current_span(false)
        .without_time()
        .init();

    let config = aws_config::load_defaults(aws_config::BehaviorVersion::latest()).await;
    let bucket = env::var("MEMORY_BACKEND_BUCKET")
        .map_err(|_| AppError::Internal("MEMORY_BACKEND_BUCKET is required".into()))?;
    let stage_name = env::var("API_GATEWAY_STAGE_NAME").unwrap_or_else(|_| "prod".into());
    let auth_token = env::var("MEMORY_BACKEND_AUTH_TOKEN").ok();

    let state = Arc::new(AppState {
        s3: Client::new(&config),
        bucket,
        stage_name,
        auth_token,
    });

    run(service_fn(move |request| {
        let state = state.clone();
        async move { handle_request(request, state).await }
    }))
    .await
}

async fn handle_request(request: Request, state: Arc<AppState>) -> Result<Response<Body>, Error> {
    let response = match route_request(&request, state).await {
        Ok(value) => value,
        Err(err) => error_response(err),
    };
    Ok(response)
}

async fn route_request(request: &Request, state: Arc<AppState>) -> AppResult<Response<Body>> {
    if let Some(expected) = &state.auth_token {
        let provided = request
            .headers()
            .get("authorization")
            .and_then(|value| value.to_str().ok())
            .unwrap_or_default();
        let expected_value = format!("Bearer {expected}");
        if provided != expected_value {
            return Err(AppError::Forbidden(
                "missing or invalid authorization token".into(),
            ));
        }
    }

    let method = request.method().clone();
    let path = normalize_path(request.uri().path(), &state.stage_name);
    let segments: Vec<&str> = path
        .trim_matches('/')
        .split('/')
        .filter(|segment| !segment.is_empty())
        .collect();

    match (method, segments.as_slice()) {
        (Method::POST, ["v1", "memory-batches"]) => create_batch(request, state).await,
        (Method::PATCH, ["v1", "memory-batches", batch_id]) => {
            update_batch(request, state, batch_id).await
        }
        (Method::POST, ["v1", "memory-batches", batch_id, "publish"]) => {
            publish_batch(state, batch_id).await
        }
        (Method::GET, ["v1", "repos", repo_id, "snapshots", "latest"]) => {
            get_latest_snapshot(state, repo_id).await
        }
        (Method::GET, ["v1", "snapshots", snapshot_id]) => get_snapshot(state, snapshot_id).await,
        _ => Err(AppError::NotFound(format!("route not found: {path}"))),
    }
}

async fn create_batch(request: &Request, state: Arc<AppState>) -> AppResult<Response<Body>> {
    let body = read_json::<CreateBatchRequest>(request)?;
    validate_schema_version(&body.schema_version)?;

    let batch_id = format!("mb_{}", Uuid::new_v4().simple());
    let now = now_rfc3339();
    let bundle_key = format!("raw/{}/{}/bundle.tar.gz", body.repo.name, batch_id);
    let latest_pointer_key = format!("repos/{}/latest.json", body.repo.name);

    let record = BatchRecord {
        batch_id: batch_id.clone(),
        schema_version: body.schema_version,
        repo: body.repo,
        source: body.source,
        bundle: body.bundle,
        files: body.files,
        status: BatchStatus::Draft,
        review_note: None,
        created_at: now.clone(),
        updated_at: now,
        bundle_key: bundle_key.clone(),
        latest_pointer_key,
    };

    put_json(&state, &batch_record_key(&batch_id), &record).await?;

    let upload = state
        .s3
        .put_object()
        .bucket(&state.bucket)
        .key(&bundle_key)
        .presigned(
            PresigningConfig::expires_in(Duration::from_secs(3600))
                .map_err(|err| AppError::Internal(err.to_string()))?,
        )
        .await
        .map_err(|err| AppError::Internal(err.to_string()))?;

    let response = UploadResponse {
        batch_id,
        status: "draft".into(),
        upload: PresignedUpload {
            method: upload.method().to_string(),
            url: upload.uri().to_string(),
            expires_at: expires_at_rfc3339(3600),
        },
    };

    json_response(StatusCode::CREATED, &response)
}

async fn update_batch(
    request: &Request,
    state: Arc<AppState>,
    batch_id: &str,
) -> AppResult<Response<Body>> {
    let mut record = get_json::<BatchRecord>(&state, &batch_record_key(batch_id)).await?;
    let body = read_json::<UpdateBatchRequest>(request)?;
    record.status = body.status;
    record.review_note = body.review_note;
    record.updated_at = now_rfc3339();
    put_json(&state, &batch_record_key(batch_id), &record).await?;

    json_response(StatusCode::OK, &record)
}

async fn publish_batch(state: Arc<AppState>, batch_id: &str) -> AppResult<Response<Body>> {
    let record = get_json::<BatchRecord>(&state, &batch_record_key(batch_id)).await?;
    if record.status != BatchStatus::Ready {
        return Err(AppError::BadRequest(
            "batch must be marked ready before publish".into(),
        ));
    }

    let bundle_key = record.bundle_key.clone();
    let bundle_bytes = get_s3_object_bytes(&state, &bundle_key).await?;
    if bundle_bytes.len() as u64 != record.bundle.size_bytes {
        return Err(AppError::BadRequest(
            "bundle size does not match the manifest".into(),
        ));
    }

    let bundle_sha256 = hex_sha256(&bundle_bytes);
    if bundle_sha256 != record.bundle.sha256 {
        return Err(AppError::BadRequest(
            "bundle sha256 does not match the manifest".into(),
        ));
    }

    let manifest = validate_bundle(&bundle_bytes, &record)?;
    let snapshot_id = format!("snap_{}", &bundle_sha256[..16]);
    let snapshot_key = snapshot_record_key(&snapshot_id);
    let manifest_key = format!("manifests/{}/{}.json", record.repo.name, snapshot_id);

    put_json(&state, &manifest_key, &manifest.manifest).await?;

    let snapshot_record = SnapshotRecord {
        snapshot_id: snapshot_id.clone(),
        batch_id: batch_id.to_string(),
        repo: record.repo.clone(),
        source: record.source.clone(),
        bundle: record.bundle.clone(),
        files: record.files.clone(),
        status: "published".into(),
        published_at: now_rfc3339(),
        bundle_key,
        manifest_key,
        latest_pointer_key: record.latest_pointer_key.clone(),
    };

    if !object_exists(&state, &snapshot_key).await? {
        put_json(&state, &snapshot_key, &snapshot_record).await?;
        put_json(
            &state,
            &format!(
                "repos/{}/snapshots/{}.json",
                snapshot_record.repo.name, snapshot_id
            ),
            &snapshot_record,
        )
        .await?;
    }

    let latest = LatestPointer {
        repo: snapshot_record.repo.name.clone(),
        snapshot_id: snapshot_id.clone(),
        snapshot_key: snapshot_key.clone(),
        updated_at: now_rfc3339(),
    };
    put_json(&state, &record.latest_pointer_key, &latest).await?;

    let response = PublishResponse {
        snapshot_id,
        status: "published".into(),
        latest_pointer: record.latest_pointer_key,
    };
    json_response(StatusCode::OK, &response)
}

async fn get_latest_snapshot(state: Arc<AppState>, repo_id: &str) -> AppResult<Response<Body>> {
    let latest: LatestPointer = get_json(&state, &format!("repos/{repo_id}/latest.json")).await?;
    let snapshot: SnapshotRecord = get_json(&state, &latest.snapshot_key).await?;
    json_response(StatusCode::OK, &snapshot)
}

async fn get_snapshot(state: Arc<AppState>, snapshot_id: &str) -> AppResult<Response<Body>> {
    let snapshot: SnapshotRecord = get_json(&state, &snapshot_record_key(snapshot_id)).await?;
    json_response(StatusCode::OK, &snapshot)
}

struct ValidationResult {
    manifest: MemoryManifest,
}

fn validate_bundle(bundle_bytes: &[u8], record: &BatchRecord) -> AppResult<ValidationResult> {
    let cursor = std::io::Cursor::new(bundle_bytes);
    let gz = GzDecoder::new(cursor);
    let mut archive = Archive::new(gz);
    let mut manifest: Option<MemoryManifest> = None;
    let mut present_paths = HashSet::new();
    let mut buffer = Vec::new();

    let entries = archive
        .entries()
        .map_err(|err| AppError::BadRequest(err.to_string()))?;
    for entry in entries {
        let mut entry = entry.map_err(|err| AppError::BadRequest(err.to_string()))?;
        let path = entry
            .path()
            .map_err(|err| AppError::BadRequest(err.to_string()))?
            .to_string_lossy()
            .to_string();
        buffer.clear();
        entry
            .read_to_end(&mut buffer)
            .map_err(|err| AppError::BadRequest(err.to_string()))?;
        if path == "memory-manifest.json" {
            manifest = Some(
                serde_json::from_slice(&buffer)
                    .map_err(|err| AppError::BadRequest(err.to_string()))?,
            );
        }
        present_paths.insert(path);
    }

    let manifest = manifest
        .ok_or_else(|| AppError::BadRequest("bundle is missing memory-manifest.json".into()))?;

    if manifest.schema_version != record.schema_version {
        return Err(AppError::BadRequest(
            "manifest schema version does not match the batch".into(),
        ));
    }
    if manifest.repo.name != record.repo.name || manifest.repo.commit != record.repo.commit {
        return Err(AppError::BadRequest(
            "manifest repo metadata does not match the batch".into(),
        ));
    }
    if manifest.files.len() != record.files.len() {
        return Err(AppError::BadRequest(
            "manifest file count does not match the batch".into(),
        ));
    }

    for file in &record.files {
        if !present_paths.contains(&file.path) {
            return Err(AppError::BadRequest(format!(
                "bundle is missing required file {}",
                file.path
            )));
        }
    }

    Ok(ValidationResult { manifest })
}

fn validate_schema_version(version: &str) -> AppResult<()> {
    if version != "1" {
        return Err(AppError::BadRequest(
            "schema_version must be exactly \"1\"".into(),
        ));
    }
    Ok(())
}

fn normalize_path(path: &str, stage_name: &str) -> String {
    let trimmed = path.trim_start_matches('/');
    if trimmed == stage_name {
        return String::new();
    }

    let stage_prefix = format!("{stage_name}/");
    if let Some(rest) = trimmed.strip_prefix(&stage_prefix) {
        return rest.to_string();
    }

    trimmed.to_string()
}

fn read_json<T: for<'de> Deserialize<'de>>(request: &Request) -> AppResult<T> {
    let bytes = request.body().as_ref();
    serde_json::from_slice(bytes).map_err(|err| AppError::BadRequest(err.to_string()))
}

fn now_rfc3339() -> String {
    OffsetDateTime::now_utc()
        .format(&time::format_description::well_known::Rfc3339)
        .unwrap_or_else(|_| "1970-01-01T00:00:00Z".into())
}

fn expires_at_rfc3339(seconds: u64) -> String {
    (OffsetDateTime::now_utc() + time::Duration::seconds(seconds as i64))
        .format(&time::format_description::well_known::Rfc3339)
        .unwrap_or_else(|_| "1970-01-01T00:00:00Z".into())
}

fn batch_record_key(batch_id: &str) -> String {
    format!("batches/{batch_id}.json")
}

fn snapshot_record_key(snapshot_id: &str) -> String {
    format!("snapshots/{snapshot_id}.json")
}

fn hex_sha256(data: &[u8]) -> String {
    let digest = Sha256::digest(data);
    hex::encode(digest)
}

async fn put_json<T: Serialize>(state: &AppState, key: &str, value: &T) -> AppResult<()> {
    let body =
        serde_json::to_vec_pretty(value).map_err(|err| AppError::Internal(err.to_string()))?;
    state
        .s3
        .put_object()
        .bucket(&state.bucket)
        .key(key)
        .body(body.into())
        .content_type("application/json")
        .send()
        .await
        .map_err(|err| AppError::Internal(err.to_string()))?;
    Ok(())
}

async fn get_json<T: for<'de> Deserialize<'de>>(state: &AppState, key: &str) -> AppResult<T> {
    let bytes = get_s3_object_bytes(state, key).await?;
    serde_json::from_slice(&bytes).map_err(|err| AppError::Internal(err.to_string()))
}

async fn get_s3_object_bytes(state: &AppState, key: &str) -> AppResult<Vec<u8>> {
    let object = state
        .s3
        .get_object()
        .bucket(&state.bucket)
        .key(key)
        .send()
        .await
        .map_err(|err| {
            let message = err.to_string();
            if message.contains("NoSuchKey") || message.contains("NotFound") {
                AppError::NotFound(key.to_string())
            } else {
                AppError::Internal(message)
            }
        })?;
    let data = object
        .body
        .collect()
        .await
        .map_err(|err| AppError::Internal(err.to_string()))?;
    Ok(data.into_bytes().to_vec())
}

async fn object_exists(state: &AppState, key: &str) -> AppResult<bool> {
    match state
        .s3
        .head_object()
        .bucket(&state.bucket)
        .key(key)
        .send()
        .await
    {
        Ok(_) => Ok(true),
        Err(err) => {
            let message = err.to_string();
            if message.contains("NotFound") || message.contains("404") {
                Ok(false)
            } else {
                Err(AppError::Internal(message))
            }
        }
    }
}

fn error_response(err: AppError) -> Response<Body> {
    let status = match err {
        AppError::BadRequest(_) => StatusCode::BAD_REQUEST,
        AppError::NotFound(_) => StatusCode::NOT_FOUND,
        AppError::Forbidden(_) => StatusCode::FORBIDDEN,
        AppError::Internal(_) => StatusCode::INTERNAL_SERVER_ERROR,
    };
    json_response(
        status,
        &ErrorResponse {
            error: status.as_u16().to_string(),
            message: err.to_string(),
        },
    )
    .unwrap_or_else(|_| {
        Response::builder()
            .status(StatusCode::INTERNAL_SERVER_ERROR)
            .body(Body::from("internal error"))
            .expect("response")
    })
}

fn json_response<T: Serialize>(status: StatusCode, value: &T) -> AppResult<Response<Body>> {
    let body =
        serde_json::to_vec_pretty(value).map_err(|err| AppError::Internal(err.to_string()))?;
    Response::builder()
        .status(status)
        .header("content-type", "application/json")
        .body(Body::from(body))
        .map_err(|err| AppError::Internal(err.to_string()))
}
