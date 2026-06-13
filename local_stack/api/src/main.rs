use std::{env, net::SocketAddr, path::PathBuf, sync::Arc};

use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use sqlx::{FromRow, PgPool};
use time::OffsetDateTime;
use tokio::fs;
use tracing_subscriber::EnvFilter;
use uuid::Uuid;

#[derive(Clone)]
struct AppState {
    pool: PgPool,
    raw_dir: PathBuf,
    data_dir: PathBuf,
}

#[derive(Debug, Deserialize, Serialize)]
struct IngestEventRequest {
    id: Option<String>,
    event_type: Option<String>,
    repo: String,
    branch: Option<String>,
    commit_sha: Option<String>,
    file_path: Option<String>,
    scope: Option<String>,
    source: Option<String>,
    session_id: Option<String>,
    created_at: Option<String>,
    content_hash: Option<String>,
    content: Option<String>,
    tool_name: Option<String>,
}

#[derive(Debug, Deserialize, Serialize, FromRow, Clone)]
struct IngestEventRecord {
    id: String,
    event_type: String,
    repo: String,
    branch: Option<String>,
    commit_sha: Option<String>,
    file_path: Option<String>,
    scope: Option<String>,
    source: Option<String>,
    session_id: Option<String>,
    created_at: String,
    content_hash: String,
    raw_payload_path: String,
    raw_markdown_path: Option<String>,
    content: Option<String>,
    status: String,
    processed_at: Option<String>,
    error: Option<String>,
}

#[derive(Debug, Deserialize, Serialize, FromRow, Clone)]
struct MemoryItemRecord {
    id: String,
    event_id: Option<String>,
    repo: String,
    scope: String,
    kind: String,
    title: String,
    summary: String,
    source_file: String,
    commit_sha: Option<String>,
    content_hash: String,
    status: String,
    supersedes_id: Option<String>,
    provenance_json: String,
    created_at: String,
    updated_at: String,
}

#[derive(Debug, Deserialize, Serialize, FromRow, Clone)]
struct MemoryChunkRecord {
    id: String,
    memory_item_id: String,
    repo: String,
    scope: String,
    kind: String,
    heading_path: String,
    chunk_index: i64,
    chunk_text: String,
    embedding: String,
    token_count: i64,
    source_file: String,
    provenance_json: String,
    created_at: String,
}

#[derive(Debug, Serialize)]
struct HealthResponse {
    status: String,
    service: String,
    data_dir: String,
}

#[derive(Debug, Serialize)]
struct SimpleResponse {
    id: String,
    status: String,
    raw_payload_path: String,
    raw_markdown_path: Option<String>,
}

#[derive(Debug, Serialize)]
struct ItemsResponse<T> {
    items: Vec<T>,
}

async fn initialize_schema(pool: &PgPool) -> Result<(), sqlx::Error> {
    let statements = [
        r#"CREATE EXTENSION IF NOT EXISTS vector"#,
        r#"
        CREATE TABLE IF NOT EXISTS ingest_events (
            id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            repo TEXT NOT NULL,
            branch TEXT,
            commit_sha TEXT,
            file_path TEXT,
            scope TEXT,
            source TEXT,
            session_id TEXT,
            created_at TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            raw_payload_path TEXT NOT NULL,
            raw_markdown_path TEXT,
            content TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            processed_at TEXT,
            error TEXT
        )
        "#,
        r#"
        CREATE TABLE IF NOT EXISTS job_queue (
            id TEXT PRIMARY KEY,
            event_id TEXT NOT NULL REFERENCES ingest_events(id) ON DELETE CASCADE,
            status TEXT NOT NULL DEFAULT 'pending',
            attempts INTEGER NOT NULL DEFAULT 0,
            next_run_at TEXT NOT NULL,
            last_error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        "#,
        r#"
        CREATE TABLE IF NOT EXISTS memory_items (
            id TEXT PRIMARY KEY,
            event_id TEXT UNIQUE REFERENCES ingest_events(id) ON DELETE CASCADE,
            repo TEXT NOT NULL,
            scope TEXT NOT NULL,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            source_file TEXT NOT NULL,
            commit_sha TEXT,
            content_hash TEXT NOT NULL,
            status TEXT NOT NULL,
            supersedes_id TEXT,
            provenance_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        "#,
        r#"
        CREATE TABLE IF NOT EXISTS memory_chunks (
            id TEXT PRIMARY KEY,
            memory_item_id TEXT NOT NULL REFERENCES memory_items(id) ON DELETE CASCADE,
            repo TEXT NOT NULL,
            scope TEXT NOT NULL,
            kind TEXT NOT NULL,
            heading_path TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            chunk_text TEXT NOT NULL,
            embedding vector(48),
            token_count INTEGER NOT NULL,
            source_file TEXT NOT NULL,
            provenance_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        "#,
        r#"ALTER TABLE memory_chunks ADD COLUMN IF NOT EXISTS embedding vector(48)"#,
        r#"
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'memory_chunks' AND column_name = 'embedding_json'
            ) THEN
                UPDATE memory_chunks
                SET embedding = CAST(embedding_json AS vector(48))
                WHERE embedding IS NULL AND embedding_json IS NOT NULL;
            END IF;
        END
        $$;
        "#,
        r#"ALTER TABLE memory_chunks ALTER COLUMN embedding SET NOT NULL"#,
        r#"
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'memory_chunks' AND column_name = 'embedding_json'
            ) THEN
                ALTER TABLE memory_chunks DROP COLUMN embedding_json;
            END IF;
        END
        $$;
        "#,
        r#"CREATE INDEX IF NOT EXISTS idx_job_queue_status_next_run ON job_queue(status, next_run_at)"#,
        r#"CREATE INDEX IF NOT EXISTS idx_memory_items_repo_scope ON memory_items(repo, scope)"#,
        r#"CREATE INDEX IF NOT EXISTS idx_memory_chunks_item ON memory_chunks(memory_item_id)"#,
        r#"
        CREATE INDEX IF NOT EXISTS idx_memory_chunks_embedding_cosine
        ON memory_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
        "#,
    ];

    for statement in statements {
        sqlx::query(statement).execute(pool).await?;
    }

    Ok(())
}

fn utc_now() -> String {
    OffsetDateTime::now_utc()
        .format(&time::format_description::well_known::Rfc3339)
        .unwrap_or_else(|_| "1970-01-01T00:00:00Z".to_string())
}

fn sanitize_filename(path_text: &str) -> String {
    let path = PathBuf::from(path_text);
    let candidate = path
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("document.md");
    candidate
        .chars()
        .map(|ch| if ch.is_alphanumeric() || matches!(ch, '-' | '_' | '.') { ch } else { '_' })
        .collect()
}

fn event_type_from_payload(payload: &IngestEventRequest, content: Option<&str>) -> String {
    if let Some(value) = &payload.event_type {
        return value.clone();
    }
    if let Some(path) = &payload.file_path {
        if PathBuf::from(path).extension().and_then(|ext| ext.to_str()) == Some("md") {
            return if content.map(|text| text.contains("status: ready")).unwrap_or(false) {
                "proposal_ready".to_string()
            } else {
                "repo_handoff".to_string()
            };
        }
    }
    "session_stop".to_string()
}

fn inferred_scope(payload: &IngestEventRequest) -> String {
    payload
        .scope
        .clone()
        .unwrap_or_else(|| "repo".to_string())
}

async fn health(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    tracing::debug!(data_dir = %state.data_dir.display(), "health check");
    Json(HealthResponse {
        status: "ok".to_string(),
        service: "local-memory-api".to_string(),
        data_dir: state.data_dir.display().to_string(),
    })
}

async fn ingest_event(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<IngestEventRequest>,
) -> Result<(StatusCode, Json<SimpleResponse>), (StatusCode, String)> {
    let event_id = payload
        .id
        .clone()
        .unwrap_or_else(|| format!("evt_{}", Uuid::new_v4().simple()));
    let created_at = payload.created_at.clone().unwrap_or_else(utc_now);
    let content = payload.content.clone();
    let event_type = event_type_from_payload(&payload, content.as_deref());
    let scope = inferred_scope(&payload);
    let content_hash = payload.content_hash.clone().unwrap_or_else(|| {
        let mut hasher = Sha256::new();
        hasher.update(content.as_deref().unwrap_or(payload.file_path.as_deref().unwrap_or(&event_id)).as_bytes());
        hex::encode(hasher.finalize())
    });
    let content_len = content.as_ref().map(|text| text.len()).unwrap_or(0);

    tracing::info!(
        event_id = %event_id,
        event_type = %event_type,
        repo = %payload.repo,
        scope = %scope,
        source = ?payload.source,
        session_id = ?payload.session_id,
        file_path = ?payload.file_path,
        content_len,
        "ingest request received"
    );

    let event_dir = state.raw_dir.join(payload.repo.clone()).join(&event_id);
    fs::create_dir_all(&event_dir)
        .await
        .map_err(|err| (StatusCode::INTERNAL_SERVER_ERROR, err.to_string()))?;

    let raw_payload_path = event_dir.join("payload.json");
    let payload_json = serde_json::to_vec_pretty(&payload)
        .map_err(|err| (StatusCode::BAD_REQUEST, err.to_string()))?;
    fs::write(&raw_payload_path, payload_json)
        .await
        .map_err(|err| (StatusCode::INTERNAL_SERVER_ERROR, err.to_string()))?;

    let raw_markdown_path = content.as_deref().map(|_| {
        let file_name = payload
            .file_path
            .as_deref()
            .map(sanitize_filename)
            .unwrap_or_else(|| "document.md".to_string());
        event_dir.join(file_name)
    });

    if let (Some(path), Some(markdown)) = (&raw_markdown_path, &content) {
        fs::write(path, format!("{}\n", markdown.trim_end()))
            .await
            .map_err(|err| (StatusCode::INTERNAL_SERVER_ERROR, err.to_string()))?;
    }

    let raw_payload_path_text = raw_payload_path.display().to_string();
    let raw_markdown_path_text = raw_markdown_path.as_ref().map(|path| path.display().to_string());

    let mut tx = state
        .pool
        .begin()
        .await
        .map_err(|err| (StatusCode::INTERNAL_SERVER_ERROR, err.to_string()))?;

    sqlx::query(
        r#"
        INSERT INTO ingest_events (
            id, event_type, repo, branch, commit_sha, file_path, scope, source, session_id,
            created_at, content_hash, raw_payload_path, raw_markdown_path, content, status
        )
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,'pending')
        ON CONFLICT (id) DO NOTHING
        "#,
    )
    .bind(&event_id)
    .bind(&event_type)
    .bind(&payload.repo)
    .bind(&payload.branch)
    .bind(&payload.commit_sha)
    .bind(&payload.file_path)
    .bind(&scope)
    .bind(&payload.source)
    .bind(&payload.session_id)
    .bind(&created_at)
    .bind(&content_hash)
    .bind(&raw_payload_path_text)
    .bind(&raw_markdown_path_text)
    .bind(&content)
    .execute(&mut *tx)
    .await
    .map_err(|err| (StatusCode::INTERNAL_SERVER_ERROR, err.to_string()))?;
    let ingest_rows = sqlx::query(
        r#"
        SELECT 1 FROM ingest_events WHERE id = $1
        "#,
    )
    .bind(&event_id)
    .fetch_all(&mut *tx)
    .await
    .map_err(|err| (StatusCode::INTERNAL_SERVER_ERROR, err.to_string()))?;

    if ingest_rows.len() != 1 {
        return Err((
            StatusCode::INTERNAL_SERVER_ERROR,
            format!("unexpected ingest row count for event_id={event_id}: {}", ingest_rows.len()),
        ));
    }

    if sqlx::query(
        r#"
        SELECT status FROM job_queue WHERE id = $1
        "#,
    )
    .bind(&event_id)
    .fetch_optional(&mut *tx)
    .await
    .map_err(|err| (StatusCode::INTERNAL_SERVER_ERROR, err.to_string()))?
    .is_some()
    {
        tx.rollback()
            .await
            .map_err(|err| (StatusCode::INTERNAL_SERVER_ERROR, err.to_string()))?;
        tracing::info!(event_id = %event_id, "duplicate ingest request ignored");
        return Ok((
            StatusCode::ACCEPTED,
            Json(SimpleResponse {
                id: event_id,
                status: "duplicate".to_string(),
                raw_payload_path: raw_payload_path_text,
                raw_markdown_path: raw_markdown_path_text,
            }),
        ));
    }

    sqlx::query(
        r#"
        INSERT INTO job_queue (id, event_id, status, attempts, next_run_at, created_at, updated_at)
        VALUES ($1, $2, 'pending', 0, $3, $4, $4)
        "#,
    )
    .bind(&event_id)
    .bind(&event_id)
    .bind(&created_at)
    .bind(&created_at)
    .execute(&mut *tx)
    .await
    .map_err(|err| (StatusCode::INTERNAL_SERVER_ERROR, err.to_string()))?;

    tx.commit()
        .await
        .map_err(|err| (StatusCode::INTERNAL_SERVER_ERROR, err.to_string()))?;

    tracing::info!(
        event_id = %event_id,
        raw_payload_path = %raw_payload_path_text,
        raw_markdown_path = ?raw_markdown_path_text,
        "ingest request queued"
    );

    Ok((
        StatusCode::ACCEPTED,
        Json(SimpleResponse {
            id: event_id,
            status: "queued".to_string(),
            raw_payload_path: raw_payload_path_text,
            raw_markdown_path: raw_markdown_path_text,
        }),
    ))
}

async fn list_events(State(state): State<Arc<AppState>>) -> Result<Json<ItemsResponse<IngestEventRecord>>, (StatusCode, String)> {
    let items = sqlx::query_as::<_, IngestEventRecord>(
        r#"SELECT * FROM ingest_events ORDER BY created_at DESC"#,
    )
    .fetch_all(&state.pool)
    .await
    .map_err(|err| (StatusCode::INTERNAL_SERVER_ERROR, err.to_string()))?;
    tracing::info!(count = items.len(), "listed ingest events");
    Ok(Json(ItemsResponse { items }))
}

async fn list_items(State(state): State<Arc<AppState>>) -> Result<Json<ItemsResponse<MemoryItemRecord>>, (StatusCode, String)> {
    let items = sqlx::query_as::<_, MemoryItemRecord>(
        r#"SELECT * FROM memory_items ORDER BY updated_at DESC"#,
    )
    .fetch_all(&state.pool)
    .await
    .map_err(|err| (StatusCode::INTERNAL_SERVER_ERROR, err.to_string()))?;
    tracing::info!(count = items.len(), "listed memory items");
    Ok(Json(ItemsResponse { items }))
}

async fn list_chunks(State(state): State<Arc<AppState>>) -> Result<Json<ItemsResponse<MemoryChunkRecord>>, (StatusCode, String)> {
    let items = sqlx::query_as::<_, MemoryChunkRecord>(
        r#"
        SELECT
            id,
            memory_item_id,
            repo,
            scope,
            kind,
            heading_path,
            chunk_index::bigint AS chunk_index,
            chunk_text,
            embedding::text AS embedding,
            token_count::bigint AS token_count,
            source_file,
            provenance_json,
            created_at
        FROM memory_chunks
        ORDER BY created_at DESC
        "#,
    )
    .fetch_all(&state.pool)
    .await
    .map_err(|err| (StatusCode::INTERNAL_SERVER_ERROR, err.to_string()))?;
    tracing::info!(count = items.len(), "listed memory chunks");
    Ok(Json(ItemsResponse { items }))
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| EnvFilter::new("info,sqlx=warn,tower_http=warn")),
        )
        .json()
        .with_current_span(false)
        .init();

    let bind = env::var("MEMORY_API_BIND").unwrap_or_else(|_| "0.0.0.0:8081".into());
    let data_dir = PathBuf::from(env::var("MEMORY_DATA_DIR").unwrap_or_else(|_| "/data".into()));
    let raw_dir = PathBuf::from(env::var("MEMORY_RAW_DIR").unwrap_or_else(|_| data_dir.join("raw").display().to_string()));
    let database_url = env::var("MEMORY_DATABASE_URL")
        .unwrap_or_else(|_| panic!("MEMORY_DATABASE_URL is required"));
    let sanitized_database_url = if let Some((prefix, _)) = database_url.rsplit_once('@') {
        format!("{prefix}@<redacted>")
    } else {
        "<redacted>".to_string()
    };

    tracing::info!(
        bind = %bind,
        data_dir = %data_dir.display(),
        raw_dir = %raw_dir.display(),
        database_url = %sanitized_database_url,
        "starting local memory api"
    );

    let pool = sqlx::postgres::PgPoolOptions::new()
        .max_connections(5)
        .connect(&database_url)
        .await
        .unwrap_or_else(|err| panic!("failed to connect to database: {err}"));

    tracing::info!("database connection established");

    initialize_schema(&pool)
        .await
        .unwrap_or_else(|err| panic!("failed to initialize schema: {err}"));
    tracing::info!("database schema initialized");

    fs::create_dir_all(&raw_dir)
        .await
        .unwrap_or_else(|err| panic!("failed to create raw dir: {err}"));
    tracing::info!("filesystem directories ensured");

    let state = Arc::new(AppState {
        pool,
        raw_dir,
        data_dir: data_dir.clone(),
    });

    let app = Router::new()
        .route("/healthz", get(health))
        .route("/v1/events", post(ingest_event).get(list_events))
        .route("/v1/items", get(list_items))
        .route("/v1/chunks", get(list_chunks))
        .with_state(state);

    let addr: SocketAddr = bind
        .parse()
        .unwrap_or_else(|err| panic!("invalid bind address: {err}"));
    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .unwrap_or_else(|err| panic!("failed to bind {addr}: {err}"));
    tracing::info!(%addr, "local memory api listening");

    axum::serve(listener, app)
        .await
        .unwrap_or_else(|err| panic!("server error: {err}"));
}
