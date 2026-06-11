use std::{
    collections::HashSet,
    convert::Infallible,
    env,
    io::Read,
    net::SocketAddr,
    path::{Component, Path, PathBuf},
    sync::Arc,
};

use bytes::Bytes;
use flate2::read::GzDecoder;
use http::{HeaderMap, Method, Request, Response, StatusCode};
use http_body_util::{BodyExt, Full};
use hyper::body::Incoming;
use hyper::service::service_fn;
use hyper_util::{rt::TokioIo, server::conn::auto::Builder as ServerBuilder};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use tar::Archive;
use thiserror::Error;
use time::OffsetDateTime;
use tracing_subscriber::EnvFilter;
use uuid::Uuid;

#[derive(Clone)]
struct AppState {
    storage_dir: PathBuf,
    auth_token: Option<String>,
    public_base_url: Option<String>,
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
    upload: UploadTarget,
}

#[derive(Debug, Serialize)]
struct UploadTarget {
    method: String,
    url: String,
    expires_at: Option<String>,
}

#[derive(Debug, Serialize)]
struct PublishResponse {
    snapshot_id: String,
    status: String,
    latest_pointer: String,
}

#[derive(Debug, Serialize)]
struct HealthResponse {
    status: String,
    storage_dir: String,
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
type ResponseBody = Full<Bytes>;

#[tokio::main]
async fn main() -> AppResult<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env())
        .json()
        .with_current_span(false)
        .init();

    let storage_dir = env::var("MEMORY_BACKEND_STORAGE_DIR").unwrap_or_else(|_| "/data".into());
    let bind = env::var("MEMORY_BACKEND_BIND").unwrap_or_else(|_| "0.0.0.0:8080".into());
    let auth_token = env::var("MEMORY_BACKEND_AUTH_TOKEN").ok();
    let public_base_url = env::var("MEMORY_BACKEND_PUBLIC_URL")
        .ok()
        .map(|value| value.trim_end_matches('/').to_string());

    let state = Arc::new(AppState {
        storage_dir: PathBuf::from(storage_dir),
        auth_token,
        public_base_url,
    });
    tokio::fs::create_dir_all(&state.storage_dir)
        .await
        .map_err(|err| AppError::Internal(err.to_string()))?;

    let addr: SocketAddr = bind
        .parse()
        .map_err(|err| AppError::BadRequest(format!("invalid bind address: {err}")))?;
    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .map_err(|err| AppError::Internal(err.to_string()))?;
    tracing::info!(%addr, "central memory api listening");

    loop {
        let (stream, peer_addr) = listener
            .accept()
            .await
            .map_err(|err| AppError::Internal(err.to_string()))?;
        let state = state.clone();
        tokio::spawn(async move {
            let io = TokioIo::new(stream);
            let service = service_fn(move |request| {
                let state = state.clone();
                async move { Ok::<_, Infallible>(handle_request(request, state).await) }
            });
            if let Err(err) = ServerBuilder::new(hyper_util::rt::TokioExecutor::new())
                .serve_connection(io, service)
                .await
            {
                tracing::error!(%peer_addr, error = %err, "connection failed");
            }
        });
    }
}

async fn handle_request(
    request: Request<Incoming>,
    state: Arc<AppState>,
) -> Response<ResponseBody> {
    let response = match route_request(request, state).await {
        Ok(response) => response,
        Err(err) => error_response(err),
    };
    response
}

async fn route_request(
    request: Request<Incoming>,
    state: Arc<AppState>,
) -> AppResult<Response<ResponseBody>> {
    let method = request.method().clone();
    let path = request.uri().path().trim_matches('/').to_string();
    let segments: Vec<&str> = path
        .split('/')
        .filter(|segment| !segment.is_empty())
        .collect();

    match (method, segments.as_slice()) {
        (Method::GET, ["healthz"]) => json_response(
            StatusCode::OK,
            &HealthResponse {
                status: "ok".into(),
                storage_dir: state.storage_dir.display().to_string(),
            },
        ),
        (Method::POST, ["v1", "memory-batches"]) => create_batch(request, state).await,
        (Method::PUT, ["v1", "uploads", batch_id, "bundle"]) => {
            upload_bundle(request, state, batch_id).await
        }
        (Method::PATCH, ["v1", "memory-batches", batch_id]) => {
            update_batch(request, state, batch_id).await
        }
        (Method::POST, ["v1", "memory-batches", batch_id, "publish"]) => {
            publish_batch(&request.headers().clone(), state, batch_id).await
        }
        (Method::GET, ["v1", "repos", repo_id, "snapshots", "latest"]) => {
            get_latest_snapshot(&request.headers().clone(), state, repo_id).await
        }
        (Method::GET, ["v1", "snapshots", snapshot_id]) => {
            get_snapshot(&request.headers().clone(), state, snapshot_id).await
        }
        _ => Err(AppError::NotFound(format!("route not found: /{path}"))),
    }
}

async fn create_batch(
    request: Request<Incoming>,
    state: Arc<AppState>,
) -> AppResult<Response<ResponseBody>> {
    authorize(request.headers(), &state)?;
    let body = read_json::<CreateBatchRequest>(request).await?;
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
        bundle_key,
        latest_pointer_key,
    };

    put_json(&state, &batch_record_key(&batch_id), &record).await?;

    let relative_upload_url = format!("/v1/uploads/{batch_id}/bundle");
    let upload_url = state
        .public_base_url
        .as_ref()
        .map(|base_url| format!("{base_url}{relative_upload_url}"))
        .unwrap_or(relative_upload_url);

    json_response(
        StatusCode::CREATED,
        &UploadResponse {
            batch_id,
            status: "draft".into(),
            upload: UploadTarget {
                method: "PUT".into(),
                url: upload_url,
                expires_at: None,
            },
        },
    )
}

async fn upload_bundle(
    request: Request<Incoming>,
    state: Arc<AppState>,
    batch_id: &str,
) -> AppResult<Response<ResponseBody>> {
    authorize(request.headers(), &state)?;
    let record: BatchRecord = get_json(&state, &batch_record_key(batch_id)).await?;
    if record.status != BatchStatus::Draft {
        return Err(AppError::BadRequest(
            "bundle uploads are only accepted while the batch is draft".into(),
        ));
    }

    let body = read_body_bytes(request).await?;
    if body.len() as u64 != record.bundle.size_bytes {
        return Err(AppError::BadRequest(
            "bundle size does not match the batch metadata".into(),
        ));
    }
    let bundle_sha256 = hex_sha256(&body);
    if bundle_sha256 != record.bundle.sha256 {
        return Err(AppError::BadRequest(
            "bundle sha256 does not match the batch metadata".into(),
        ));
    }
    validate_bundle(&body, &record)?;
    put_bytes(&state, &record.bundle_key, &body).await?;
    empty_response(StatusCode::NO_CONTENT)
}

async fn update_batch(
    request: Request<Incoming>,
    state: Arc<AppState>,
    batch_id: &str,
) -> AppResult<Response<ResponseBody>> {
    authorize(request.headers(), &state)?;
    let body = read_json::<UpdateBatchRequest>(request).await?;
    let mut record = get_json::<BatchRecord>(&state, &batch_record_key(batch_id)).await?;
    if body.status == BatchStatus::Ready && !object_exists(&state, &record.bundle_key).await? {
        return Err(AppError::BadRequest(
            "batch cannot be marked ready before the bundle is uploaded".into(),
        ));
    }
    record.status = body.status;
    record.review_note = body.review_note;
    record.updated_at = now_rfc3339();
    put_json(&state, &batch_record_key(batch_id), &record).await?;

    json_response(StatusCode::OK, &record)
}

async fn publish_batch(
    headers: &HeaderMap,
    state: Arc<AppState>,
    batch_id: &str,
) -> AppResult<Response<ResponseBody>> {
    authorize(headers, &state)?;
    let record = get_json::<BatchRecord>(&state, &batch_record_key(batch_id)).await?;
    if record.status != BatchStatus::Ready {
        return Err(AppError::BadRequest(
            "batch must be marked ready before publish".into(),
        ));
    }

    let bundle_bytes = get_bytes(&state, &record.bundle_key).await?;
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

    if !object_exists(&state, &manifest_key).await? {
        put_json(&state, &manifest_key, &manifest.manifest).await?;
    }

    let snapshot_record = SnapshotRecord {
        snapshot_id: snapshot_id.clone(),
        batch_id: batch_id.to_string(),
        repo: record.repo.clone(),
        source: record.source.clone(),
        bundle: record.bundle.clone(),
        files: record.files.clone(),
        status: "published".into(),
        published_at: now_rfc3339(),
        bundle_key: record.bundle_key.clone(),
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
        snapshot_key,
        updated_at: now_rfc3339(),
    };
    put_json(&state, &record.latest_pointer_key, &latest).await?;

    json_response(
        StatusCode::OK,
        &PublishResponse {
            snapshot_id,
            status: "published".into(),
            latest_pointer: record.latest_pointer_key,
        },
    )
}

async fn get_latest_snapshot(
    headers: &HeaderMap,
    state: Arc<AppState>,
    repo_id: &str,
) -> AppResult<Response<ResponseBody>> {
    authorize(headers, &state)?;
    let latest: LatestPointer = get_json(&state, &format!("repos/{repo_id}/latest.json")).await?;
    let snapshot: SnapshotRecord = get_json(&state, &latest.snapshot_key).await?;
    json_response(StatusCode::OK, &snapshot)
}

async fn get_snapshot(
    headers: &HeaderMap,
    state: Arc<AppState>,
    snapshot_id: &str,
) -> AppResult<Response<ResponseBody>> {
    authorize(headers, &state)?;
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
        if path.starts_with('/') || path.contains("../") || path == ".." {
            return Err(AppError::BadRequest(format!(
                "bundle contains unsafe path {path}"
            )));
        }
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
        if file.path.starts_with('/') || file.path.contains("../") || file.path == ".." {
            return Err(AppError::BadRequest(format!(
                "manifest contains unsafe file path {}",
                file.path
            )));
        }
        if !present_paths.contains(&file.path) {
            return Err(AppError::BadRequest(format!(
                "bundle is missing required file {}",
                file.path
            )));
        }
    }

    Ok(ValidationResult { manifest })
}

fn authorize(headers: &HeaderMap, state: &AppState) -> AppResult<()> {
    if let Some(expected) = &state.auth_token {
        let provided = headers
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
    Ok(())
}

fn validate_schema_version(version: &str) -> AppResult<()> {
    if version != "1" {
        return Err(AppError::BadRequest(
            "schema_version must be exactly \"1\"".into(),
        ));
    }
    Ok(())
}

async fn read_json<T: for<'de> Deserialize<'de>>(request: Request<Incoming>) -> AppResult<T> {
    let bytes = read_body_bytes(request).await?;
    serde_json::from_slice(&bytes).map_err(|err| AppError::BadRequest(err.to_string()))
}

async fn read_body_bytes(request: Request<Incoming>) -> AppResult<Bytes> {
    request
        .into_body()
        .collect()
        .await
        .map(|collected| collected.to_bytes())
        .map_err(|err| AppError::BadRequest(err.to_string()))
}

fn now_rfc3339() -> String {
    OffsetDateTime::now_utc()
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
    put_bytes(state, key, &body).await
}

async fn get_json<T: for<'de> Deserialize<'de>>(state: &AppState, key: &str) -> AppResult<T> {
    let bytes = get_bytes(state, key).await?;
    serde_json::from_slice(&bytes).map_err(|err| AppError::Internal(err.to_string()))
}

async fn put_bytes(state: &AppState, key: &str, bytes: &[u8]) -> AppResult<()> {
    let path = storage_path(state, key)?;
    if let Some(parent) = path.parent() {
        tokio::fs::create_dir_all(parent)
            .await
            .map_err(|err| AppError::Internal(err.to_string()))?;
    }
    tokio::fs::write(path, bytes)
        .await
        .map_err(|err| AppError::Internal(err.to_string()))
}

async fn get_bytes(state: &AppState, key: &str) -> AppResult<Vec<u8>> {
    let path = storage_path(state, key)?;
    tokio::fs::read(path).await.map_err(|err| {
        if err.kind() == std::io::ErrorKind::NotFound {
            AppError::NotFound(key.to_string())
        } else {
            AppError::Internal(err.to_string())
        }
    })
}

async fn object_exists(state: &AppState, key: &str) -> AppResult<bool> {
    let path = storage_path(state, key)?;
    match tokio::fs::metadata(path).await {
        Ok(_) => Ok(true),
        Err(err) if err.kind() == std::io::ErrorKind::NotFound => Ok(false),
        Err(err) => Err(AppError::Internal(err.to_string())),
    }
}

fn storage_path(state: &AppState, key: &str) -> AppResult<PathBuf> {
    let mut path = state.storage_dir.clone();
    for component in Path::new(key).components() {
        match component {
            Component::Normal(segment) => path.push(segment),
            _ => return Err(AppError::BadRequest(format!("invalid storage key: {key}"))),
        }
    }
    Ok(path)
}

fn json_response<T: Serialize>(status: StatusCode, value: &T) -> AppResult<Response<ResponseBody>> {
    let body =
        serde_json::to_vec_pretty(value).map_err(|err| AppError::Internal(err.to_string()))?;
    Response::builder()
        .status(status)
        .header("content-type", "application/json")
        .body(Full::new(Bytes::from(body)))
        .map_err(|err| AppError::Internal(err.to_string()))
}

fn empty_response(status: StatusCode) -> AppResult<Response<ResponseBody>> {
    Response::builder()
        .status(status)
        .body(Full::new(Bytes::new()))
        .map_err(|err| AppError::Internal(err.to_string()))
}

fn error_response(err: AppError) -> Response<ResponseBody> {
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
            .body(Full::new(Bytes::from_static(b"internal error")))
            .expect("response")
    })
}
