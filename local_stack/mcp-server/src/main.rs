use std::{
    collections::{HashMap, HashSet},
    env,
    io::stderr,
    net::SocketAddr,
    num::ParseFloatError,
    sync::Arc,
};

use anyhow::{Context, Result};
use axum::{routing::get, Router};
use rmcp::{
    handler::server::{router::tool::ToolRouter, wrapper::Parameters},
    model::*,
    schemars::JsonSchema,
    service::RequestContext,
    tool, tool_handler, tool_router,
    transport::streamable_http_server::{
        session::local::LocalSessionManager, StreamableHttpServerConfig, StreamableHttpService,
    },
    ErrorData as McpError, RoleServer, ServerHandler,
};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use sqlx::{FromRow, PgPool};
use tokio::task;
use tracing_subscriber::EnvFilter;

const EMBEDDING_DIMENSIONS: usize = 48;
const DEFAULT_LIMIT: usize = 10;
const DEFAULT_MCP_BIND: &str = "0.0.0.0:8082";
const LOCAL_MCP_PUBLIC_BASE_URL: &str = "http://127.0.0.1:8080";
const OAUTH_AUTHORIZATION_ENDPOINT: &str = "http://127.0.0.1:8080/oauth/authorize";
const OAUTH_TOKEN_ENDPOINT: &str = "http://127.0.0.1:8080/oauth/token";

#[derive(Serialize)]
struct OAuthAuthorizationServerMetadata {
    issuer: &'static str,
    authorization_endpoint: &'static str,
    token_endpoint: &'static str,
    response_types_supported: [&'static str; 1],
    grant_types_supported: [&'static str; 2],
    code_challenge_methods_supported: [&'static str; 2],
    token_endpoint_auth_methods_supported: [&'static str; 3],
    scopes_supported: [&'static str; 3],
    introspection_endpoint: &'static str,
    revocation_endpoint: &'static str,
    registration_endpoint: &'static str,
}

#[derive(Serialize)]
struct OAuthResourceMetadata {
    resource: &'static str,
    authorization_servers: [&'static str; 1],
    scopes_supported: [&'static str; 3],
}

#[derive(Serialize)]
struct OAuthErrorResponse {
    error: &'static str,
    error_description: &'static str,
}

fn oauth_authorization_server_metadata() -> OAuthAuthorizationServerMetadata {
    OAuthAuthorizationServerMetadata {
        issuer: LOCAL_MCP_PUBLIC_BASE_URL,
        authorization_endpoint: OAUTH_AUTHORIZATION_ENDPOINT,
        token_endpoint: OAUTH_TOKEN_ENDPOINT,
        response_types_supported: ["code"],
        grant_types_supported: ["authorization_code", "refresh_token"],
        code_challenge_methods_supported: ["S256", "plain"],
        token_endpoint_auth_methods_supported: [
            "none",
            "client_secret_post",
            "client_secret_basic",
        ],
        scopes_supported: ["openid", "profile", "offline_access"],
        introspection_endpoint: "http://127.0.0.1:8080/oauth/introspect",
        revocation_endpoint: "http://127.0.0.1:8080/oauth/revoke",
        registration_endpoint: "http://127.0.0.1:8080/oauth/register",
    }
}

fn oauth_resource_metadata() -> OAuthResourceMetadata {
    OAuthResourceMetadata {
        resource: "http://127.0.0.1:8080/mcp",
        authorization_servers: [LOCAL_MCP_PUBLIC_BASE_URL],
        scopes_supported: ["openid", "profile", "offline_access"],
    }
}

#[derive(Clone)]
struct MemoryServer {
    pool: Arc<PgPool>,
    tool_router: ToolRouter<Self>,
}

impl MemoryServer {
    fn new(pool: PgPool) -> Self {
        Self {
            pool: Arc::new(pool),
            tool_router: Self::tool_router(),
        }
    }

    fn run_db<F, T>(&self, future: F) -> Result<T, McpError>
    where
        F: std::future::Future<Output = Result<T, sqlx::Error>>,
    {
        task::block_in_place(|| tokio::runtime::Handle::current().block_on(future))
            .map_err(database_error)
    }
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct MemoryItem {
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
    provenance: Value,
    created_at: String,
    updated_at: String,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct MemoryChunk {
    id: String,
    memory_item_id: String,
    repo: String,
    scope: String,
    kind: String,
    heading_path: String,
    chunk_index: i64,
    chunk_text: String,
    embedding: Vec<f64>,
    token_count: i64,
    source_file: String,
    provenance: Value,
    created_at: String,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct SearchArgs {
    query: String,
    repo: Option<String>,
    scope: Option<String>,
    kind: Option<String>,
    limit: Option<u32>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct ItemArgs {
    id: String,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct ResourceArgs {
    repo: String,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct ContextPackArgs {
    task: String,
    repo: Option<String>,
    scope: Option<String>,
    budget: Option<u32>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct SpecContextArgs {
    spec_id: String,
    repo: Option<String>,
    limit: Option<u32>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct RecentEventsArgs {
    repo: Option<String>,
    scope: Option<String>,
    event_types: Option<Vec<String>>,
    limit: Option<u32>,
}

#[derive(Debug, FromRow)]
struct MemoryItemRow {
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
    provenance: Value,
    created_at: String,
    updated_at: String,
}

#[derive(Debug, FromRow)]
struct MemoryChunkRow {
    id: String,
    memory_item_id: String,
    repo: String,
    scope: String,
    kind: String,
    heading_path: String,
    chunk_index: i64,
    chunk_text: String,
    embedding_text: String,
    token_count: i64,
    source_file: String,
    provenance: Value,
    created_at: String,
}

#[derive(Debug, Serialize, FromRow)]
struct EventRow {
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
    status: String,
}

#[derive(Debug, FromRow)]
struct SearchCandidateRow {
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
    provenance: Value,
    created_at: String,
    updated_at: String,
    distance: f64,
}

fn normalize_words(text: &str) -> Vec<String> {
    let mut words = Vec::new();
    let mut current = String::new();
    for ch in text.chars() {
        if ch.is_alphanumeric() || ch == '_' {
            current.push(ch.to_ascii_lowercase());
        } else if !current.is_empty() {
            words.push(current.clone());
            current.clear();
        }
    }
    if !current.is_empty() {
        words.push(current);
    }
    words
}

fn hash_embedding(text: &str, dimensions: usize) -> Vec<f64> {
    let mut vector = vec![0.0_f64; dimensions];
    for word in normalize_words(text) {
        let mut hasher = Sha256::new();
        hasher.update(word.as_bytes());
        let digest = hasher.finalize();
        let index =
            u32::from_be_bytes([digest[0], digest[1], digest[2], digest[3]]) as usize % dimensions;
        let sign = if digest[4] & 1 == 1 { -1.0 } else { 1.0 };
        let weight = 1.0 + (digest[5] as f64 / 255.0);
        vector[index] += sign * weight;
    }
    let norm = vector.iter().map(|value| value * value).sum::<f64>().sqrt();
    if norm > 0.0 {
        for value in &mut vector {
            *value /= norm;
        }
    }
    vector
}

fn lexical_score(item: &MemoryItem, query: &str) -> f64 {
    let query_words: HashSet<String> = normalize_words(query).into_iter().collect();
    let lexical_source = format!("{} {} {}", item.title, item.summary, item.source_file);
    let lexical_words = normalize_words(&lexical_source);
    let overlap = lexical_words
        .iter()
        .filter(|word| query_words.contains(*word))
        .count() as f64;
    overlap / (query_words.len().max(1) as f64)
}

fn vector_literal(values: &[f64]) -> String {
    let body = values
        .iter()
        .map(|value| value.to_string())
        .collect::<Vec<_>>()
        .join(",");
    format!("[{body}]")
}

fn parse_vector(text: &str) -> std::result::Result<Vec<f64>, ParseFloatError> {
    let trimmed = text.trim().trim_start_matches('[').trim_end_matches(']');
    if trimmed.is_empty() {
        return Ok(Vec::new());
    }
    trimmed
        .split(',')
        .map(|entry| entry.trim().parse::<f64>())
        .collect()
}

fn database_error(error: sqlx::Error) -> McpError {
    McpError::internal_error(
        "database_error",
        Some(serde_json::json!({
            "message": error.to_string(),
        })),
    )
}

fn memory_item_from_row(row: MemoryItemRow) -> MemoryItem {
    MemoryItem {
        id: row.id,
        event_id: row.event_id,
        repo: row.repo,
        scope: row.scope,
        kind: row.kind,
        title: row.title,
        summary: row.summary,
        source_file: row.source_file,
        commit_sha: row.commit_sha,
        content_hash: row.content_hash,
        status: row.status,
        supersedes_id: row.supersedes_id,
        provenance: row.provenance,
        created_at: row.created_at,
        updated_at: row.updated_at,
    }
}

fn memory_chunk_from_row(row: MemoryChunkRow) -> std::result::Result<MemoryChunk, ParseFloatError> {
    Ok(MemoryChunk {
        id: row.id,
        memory_item_id: row.memory_item_id,
        repo: row.repo,
        scope: row.scope,
        kind: row.kind,
        heading_path: row.heading_path,
        chunk_index: row.chunk_index,
        chunk_text: row.chunk_text,
        embedding: parse_vector(&row.embedding_text)?,
        token_count: row.token_count,
        source_file: row.source_file,
        provenance: row.provenance,
        created_at: row.created_at,
    })
}

async fn fetch_item(pool: &PgPool, item_id: &str) -> Result<Option<MemoryItem>, sqlx::Error> {
    let row = sqlx::query_as::<_, MemoryItemRow>(
        r#"
        SELECT
            id,
            event_id,
            repo,
            scope,
            kind,
            title,
            summary,
            source_file,
            commit_sha,
            content_hash,
            status,
            supersedes_id,
            provenance_json::jsonb AS provenance,
            created_at,
            updated_at
        FROM memory_items
        WHERE id = $1
        "#,
    )
    .bind(item_id)
    .fetch_optional(pool)
    .await?;
    Ok(row.map(memory_item_from_row))
}

async fn fetch_item_chunks(pool: &PgPool, item_id: &str) -> Result<Vec<MemoryChunk>, sqlx::Error> {
    let rows = sqlx::query_as::<_, MemoryChunkRow>(
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
            embedding::text AS embedding_text,
            token_count::bigint AS token_count,
            source_file,
            provenance_json::jsonb AS provenance,
            created_at
        FROM memory_chunks
        WHERE memory_item_id = $1
        ORDER BY chunk_index ASC
        "#,
    )
    .bind(item_id)
    .fetch_all(pool)
    .await?;
    rows.into_iter()
        .map(|row| memory_chunk_from_row(row).map_err(|error| sqlx::Error::Decode(Box::new(error))))
        .collect()
}

async fn fetch_items_for_repo(pool: &PgPool, repo: &str) -> Result<Vec<MemoryItem>, sqlx::Error> {
    let rows = sqlx::query_as::<_, MemoryItemRow>(
        r#"
        SELECT
            id,
            event_id,
            repo,
            scope,
            kind,
            title,
            summary,
            source_file,
            commit_sha,
            content_hash,
            status,
            supersedes_id,
            provenance_json::jsonb AS provenance,
            created_at,
            updated_at
        FROM memory_items
        WHERE repo = $1
        ORDER BY updated_at DESC
        "#,
    )
    .bind(repo)
    .fetch_all(pool)
    .await?;
    Ok(rows.into_iter().map(memory_item_from_row).collect())
}

async fn fetch_recent_events(
    pool: &PgPool,
    repo: Option<String>,
    scope: Option<String>,
    event_types: Option<Vec<String>>,
    limit: i64,
) -> Result<Vec<EventRow>, sqlx::Error> {
    sqlx::query_as::<_, EventRow>(
        r#"
        SELECT
            id,
            event_type,
            repo,
            branch,
            commit_sha,
            file_path,
            scope,
            source,
            session_id,
            created_at,
            content_hash,
            status
        FROM ingest_events
        WHERE ($1::text IS NULL OR repo = $1)
          AND ($2::text IS NULL OR scope = $2)
          AND ($3::text[] IS NULL OR event_type = ANY($3))
        ORDER BY created_at DESC
        LIMIT $4
        "#,
    )
    .bind(repo)
    .bind(scope)
    .bind(event_types)
    .bind(limit)
    .fetch_all(pool)
    .await
}

async fn oauth_authorization_server() -> axum::Json<OAuthAuthorizationServerMetadata> {
    axum::Json(oauth_authorization_server_metadata())
}

async fn oauth_resource_server() -> axum::Json<OAuthResourceMetadata> {
    axum::Json(oauth_resource_metadata())
}

async fn oauth_authorize() -> (axum::http::StatusCode, axum::Json<OAuthErrorResponse>) {
    (
        axum::http::StatusCode::OK,
        axum::Json(OAuthErrorResponse {
            error: "authorization_not_implemented",
            error_description:
                "This local stack exposes OAuth discovery metadata but does not implement an interactive authorization screen.",
        }),
    )
}

async fn oauth_token() -> (axum::http::StatusCode, axum::Json<OAuthErrorResponse>) {
    (
        axum::http::StatusCode::OK,
        axum::Json(OAuthErrorResponse {
            error: "token_exchange_not_implemented",
            error_description:
                "This local stack exposes OAuth discovery metadata but does not issue tokens.",
        }),
    )
}

#[tool_router]
impl MemoryServer {
    #[tool(description = "Search the local memory index by query, repo, scope, and kind")]
    fn search_memory(&self, Parameters(args): Parameters<SearchArgs>) -> Result<String, McpError> {
        tracing::info!(
            query = %args.query,
            repo = ?args.repo,
            scope = ?args.scope,
            kind = ?args.kind,
            limit = args.limit.unwrap_or(DEFAULT_LIMIT as u32),
            "mcp search_memory called"
        );

        let limit = args.limit.unwrap_or(DEFAULT_LIMIT as u32).max(1) as usize;
        let query_embedding = vector_literal(&hash_embedding(&args.query, EMBEDDING_DIMENSIONS));
        let candidate_limit = ((limit * 8).max(20)) as i64;
        let pool = Arc::clone(&self.pool);
        let repo = args.repo.clone();
        let scope = args.scope.clone();
        let kind = args.kind.clone();

        let rows = self.run_db(async move {
            sqlx::query_as::<_, SearchCandidateRow>(
                r#"
                SELECT
                    i.id,
                    i.event_id,
                    i.repo,
                    i.scope,
                    i.kind,
                    i.title,
                    i.summary,
                    i.source_file,
                    i.commit_sha,
                    i.content_hash,
                    i.status,
                    i.supersedes_id,
                    i.provenance_json::jsonb AS provenance,
                    i.created_at,
                    i.updated_at,
                    c.embedding <=> CAST($1 AS vector) AS distance
                FROM memory_chunks c
                JOIN memory_items i ON i.id = c.memory_item_id
                WHERE ($2::text IS NULL OR i.repo = $2)
                  AND ($3::text IS NULL OR i.scope = $3)
                  AND ($4::text IS NULL OR i.kind = $4)
                ORDER BY c.embedding <=> CAST($1 AS vector), i.updated_at DESC
                LIMIT $5
                "#,
            )
            .bind(query_embedding)
            .bind(repo)
            .bind(scope)
            .bind(kind)
            .bind(candidate_limit)
            .fetch_all(&*pool)
            .await
        })?;

        let mut aggregated: HashMap<String, (MemoryItem, f64)> = HashMap::new();
        for row in rows {
            let vector_score = (1.0_f64 - row.distance).max(0.0);
            let item = memory_item_from_row(MemoryItemRow {
                id: row.id,
                event_id: row.event_id,
                repo: row.repo,
                scope: row.scope,
                kind: row.kind,
                title: row.title,
                summary: row.summary,
                source_file: row.source_file,
                commit_sha: row.commit_sha,
                content_hash: row.content_hash,
                status: row.status,
                supersedes_id: row.supersedes_id,
                provenance: row.provenance,
                created_at: row.created_at,
                updated_at: row.updated_at,
            });
            aggregated
                .entry(item.id.clone())
                .and_modify(|(_, best_score)| {
                    if vector_score > *best_score {
                        *best_score = vector_score;
                    }
                })
                .or_insert((item, vector_score));
        }

        let mut results: Vec<_> = aggregated
            .into_values()
            .map(|(item, vector_score)| {
                let score = (lexical_score(&item, &args.query) * 0.6) + (vector_score * 0.4);
                serde_json::json!({
                    "id": item.id,
                    "repo": item.repo,
                    "scope": item.scope,
                    "kind": item.kind,
                    "title": item.title,
                    "summary": item.summary,
                    "source_file": item.source_file,
                    "status": item.status,
                    "score": score,
                    "resource": format!("memory://items/{}", item.id),
                })
            })
            .collect();

        results.sort_by(|left, right| {
            right["score"]
                .as_f64()
                .partial_cmp(&left["score"].as_f64())
                .unwrap_or(std::cmp::Ordering::Equal)
        });
        results.truncate(limit);

        tracing::info!(count = results.len(), "mcp search_memory completed");
        Ok(serde_json::json!({
            "query": args.query,
            "count": results.len(),
            "results": results,
        })
        .to_string())
    }

    #[tool(description = "Get one structured memory item and its chunks by id")]
    fn get_memory_item(&self, Parameters(args): Parameters<ItemArgs>) -> Result<String, McpError> {
        tracing::info!(item_id = %args.id, "mcp get_memory_item called");
        let pool = Arc::clone(&self.pool);
        let item = self.run_db(fetch_item(&pool, &args.id))?.ok_or_else(|| {
            McpError::resource_not_found(
                "memory_item_not_found",
                Some(serde_json::json!({ "id": args.id })),
            )
        })?;
        let chunks = self.run_db(fetch_item_chunks(&pool, &item.id))?;
        tracing::info!(item_id = %item.id, chunk_count = chunks.len(), "mcp get_memory_item completed");
        Ok(serde_json::json!({
            "item": item,
            "chunks": chunks,
        })
        .to_string())
    }

    #[tool(description = "Get the latest context pack for one repo")]
    fn get_repo_context_pack(
        &self,
        Parameters(args): Parameters<ResourceArgs>,
    ) -> Result<String, McpError> {
        tracing::info!(repo = %args.repo, "mcp get_repo_context_pack called");
        let pool = Arc::clone(&self.pool);
        let items = self.run_db(fetch_items_for_repo(&pool, &args.repo))?;
        let generated_at = items
            .first()
            .map(|item| item.updated_at.clone())
            .unwrap_or_else(|| "1970-01-01T00:00:00Z".to_string());
        tracing::info!(repo = %args.repo, item_count = items.len(), "mcp get_repo_context_pack completed");
        Ok(serde_json::json!({
            "repo": args.repo,
            "generated_at": generated_at,
            "items": items,
        })
        .to_string())
    }

    #[tool(description = "Build a Spec Memory context pack for a task, scope, and token budget")]
    fn build_context_pack(
        &self,
        Parameters(args): Parameters<ContextPackArgs>,
    ) -> Result<String, McpError> {
        let limit = args.budget.unwrap_or(DEFAULT_LIMIT as u32).clamp(1, 50);
        let query = format!("{} spec plan tasks adr decision lesson", args.task);
        let search_args = SearchArgs {
            query,
            repo: args.repo.clone(),
            scope: args.scope.clone(),
            kind: None,
            limit: Some(limit),
        };
        let search = self.search_memory(Parameters(search_args))?;
        Ok(serde_json::json!({
            "task": args.task,
            "repo": args.repo,
            "scope": args.scope,
            "budget": limit,
            "context": serde_json::from_str::<Value>(&search).unwrap_or_else(|_| Value::String(search)),
            "contract": {
                "write_path": "emit structured events through the Memory API",
                "read_path": "consume this context through MCP",
                "runtime_rule": "runtimes are adapters, not memory stores"
            }
        })
        .to_string())
    }

    #[tool(description = "Get Spec Kit context by spec id from indexed memory and recent events")]
    fn get_spec_context(
        &self,
        Parameters(args): Parameters<SpecContextArgs>,
    ) -> Result<String, McpError> {
        let limit = args.limit.unwrap_or(DEFAULT_LIMIT as u32).clamp(1, 50);
        let search_args = SearchArgs {
            query: format!(
                "{} requirements clarifications plan tasks analysis implementation",
                args.spec_id
            ),
            repo: args.repo.clone(),
            scope: Some("feature".to_string()),
            kind: None,
            limit: Some(limit),
        };
        let search = self.search_memory(Parameters(search_args))?;
        let pool = Arc::clone(&self.pool);
        let events = self.run_db(fetch_recent_events(
            &pool,
            args.repo.clone(),
            None,
            Some(vec![
                "spec.created".to_string(),
                "spec.updated".to_string(),
                "requirement.created".to_string(),
                "requirement.updated".to_string(),
                "plan.created".to_string(),
                "tasks.generated".to_string(),
                "analysis.completed".to_string(),
                "implementation.completed".to_string(),
            ]),
            limit as i64,
        ))?;
        Ok(serde_json::json!({
            "spec_id": args.spec_id,
            "repo": args.repo,
            "memory": serde_json::from_str::<Value>(&search).unwrap_or_else(|_| Value::String(search)),
            "recent_events": events,
        })
        .to_string())
    }

    #[tool(description = "List recent Spec Memory events by repo, scope, and event type")]
    fn list_recent_events(
        &self,
        Parameters(args): Parameters<RecentEventsArgs>,
    ) -> Result<String, McpError> {
        let limit = args.limit.unwrap_or(DEFAULT_LIMIT as u32).clamp(1, 100) as i64;
        let pool = Arc::clone(&self.pool);
        let events = self.run_db(fetch_recent_events(
            &pool,
            args.repo.clone(),
            args.scope.clone(),
            args.event_types.clone(),
            limit,
        ))?;
        Ok(serde_json::json!({
            "count": events.len(),
            "events": events,
        })
        .to_string())
    }

    #[tool(description = "Explain one memory item with provenance and supersession data")]
    fn explain_memory(&self, Parameters(args): Parameters<ItemArgs>) -> Result<String, McpError> {
        let pool = Arc::clone(&self.pool);
        let item = self.run_db(fetch_item(&pool, &args.id))?.ok_or_else(|| {
            McpError::resource_not_found(
                "memory_item_not_found",
                Some(serde_json::json!({ "id": args.id })),
            )
        })?;
        let chunks = self.run_db(fetch_item_chunks(&pool, &item.id))?;
        Ok(serde_json::json!({
            "memory_id": item.id,
            "status": item.status,
            "scope": item.scope,
            "kind": item.kind,
            "title": item.title,
            "summary": item.summary,
            "source_file": item.source_file,
            "event_id": item.event_id,
            "supersedes_id": item.supersedes_id,
            "provenance": item.provenance,
            "chunk_count": chunks.len(),
            "retrieval_guidance": "Prefer active memory; follow supersession links before applying deprecated knowledge."
        })
        .to_string())
    }
}

#[tool_handler(router = self.tool_router)]
impl ServerHandler for MemoryServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo {
            instructions: Some(
                "Search the local memory index and read structured resources.".into(),
            ),
            capabilities: ServerCapabilities::builder()
                .enable_tools()
                .enable_resources()
                .build(),
            ..Default::default()
        }
    }

    async fn list_resources(
        &self,
        _request: Option<PaginatedRequestParams>,
        _context: RequestContext<RoleServer>,
    ) -> Result<ListResourcesResult, McpError> {
        tracing::debug!("mcp list_resources called");
        let items = sqlx::query_as::<_, MemoryItemRow>(
            r#"
            SELECT
                id,
                event_id,
                repo,
                scope,
                kind,
                title,
                summary,
                source_file,
                commit_sha,
                content_hash,
                status,
                supersedes_id,
                provenance_json::jsonb AS provenance,
                created_at,
                updated_at
            FROM memory_items
            ORDER BY updated_at DESC
            LIMIT 100
            "#,
        )
        .fetch_all(&*self.pool)
        .await
        .map_err(database_error)?;

        let mut resources =
            vec![RawResource::new("memory://org/invariants", "org invariants").no_annotation()];
        for item in items.into_iter().map(memory_item_from_row) {
            resources.push(
                RawResource::new(format!("memory://items/{}", item.id), item.title).no_annotation(),
            );
        }
        tracing::info!(
            resource_count = resources.len(),
            "mcp list_resources completed"
        );
        Ok(ListResourcesResult {
            resources,
            next_cursor: None,
            meta: None,
        })
    }

    async fn read_resource(
        &self,
        request: ReadResourceRequestParams,
        _context: RequestContext<RoleServer>,
    ) -> Result<ReadResourceResult, McpError> {
        tracing::info!(uri = %request.uri, "mcp read_resource called");
        match request.uri.as_str() {
            "memory://org/invariants" => {
                let items = sqlx::query_as::<_, MemoryItemRow>(
                    r#"
                    SELECT
                        id,
                        event_id,
                        repo,
                        scope,
                        kind,
                        title,
                        summary,
                        source_file,
                        commit_sha,
                        content_hash,
                        status,
                        supersedes_id,
                        provenance_json::jsonb AS provenance,
                        created_at,
                        updated_at
                    FROM memory_items
                    WHERE scope = 'org' OR kind = 'lesson'
                    ORDER BY updated_at DESC
                    "#,
                )
                .fetch_all(&*self.pool)
                .await
                .map_err(database_error)?
                .into_iter()
                .map(memory_item_from_row)
                .collect::<Vec<_>>();
                let generated_at = items
                    .first()
                    .map(|item| item.updated_at.clone())
                    .unwrap_or_else(|| "1970-01-01T00:00:00Z".to_string());
                Ok(ReadResourceResult {
                    contents: vec![ResourceContents::text(
                        serde_json::json!({
                            "uri": request.uri,
                            "generated_at": generated_at,
                            "items": items,
                        })
                        .to_string(),
                        &request.uri,
                    )],
                })
            }
            uri if uri.starts_with("memory://items/") => {
                let item_id = uri.trim_start_matches("memory://items/");
                let item = fetch_item(&self.pool, item_id)
                    .await
                    .map_err(database_error)?
                    .ok_or_else(|| {
                        McpError::resource_not_found(
                            "memory_item_not_found",
                            Some(serde_json::json!({ "uri": request.uri })),
                        )
                    })?;
                let chunks = fetch_item_chunks(&self.pool, &item.id)
                    .await
                    .map_err(database_error)?;
                tracing::info!(uri = %request.uri, chunk_count = chunks.len(), "mcp read_resource item resolved");
                Ok(ReadResourceResult {
                    contents: vec![ResourceContents::text(
                        serde_json::json!({
                            "item": item,
                            "chunks": chunks,
                        })
                        .to_string(),
                        &request.uri,
                    )],
                })
            }
            _ => Err(McpError::resource_not_found(
                "resource_not_found",
                Some(serde_json::json!({
                    "uri": request.uri,
                })),
            )),
        }
    }

    async fn list_resource_templates(
        &self,
        _request: Option<PaginatedRequestParams>,
        _context: RequestContext<RoleServer>,
    ) -> Result<ListResourceTemplatesResult, McpError> {
        Ok(ListResourceTemplatesResult {
            resource_templates: vec![
                RawResourceTemplate {
                    uri_template: "memory://org/{org_id}".to_string(),
                    name: "organization memory".to_string(),
                    title: None,
                    description: Some("Organization-wide active memory and governance".to_string()),
                    mime_type: Some("application/json".to_string()),
                    icons: None,
                }
                .no_annotation(),
                RawResourceTemplate {
                    uri_template: "memory://product/{product_id}".to_string(),
                    name: "product memory".to_string(),
                    title: None,
                    description: Some(
                        "Product architecture, policies, and cross-repo knowledge".to_string(),
                    ),
                    mime_type: Some("application/json".to_string()),
                    icons: None,
                }
                .no_annotation(),
                RawResourceTemplate {
                    uri_template: "memory://repo/{repo_id}".to_string(),
                    name: "repository memory".to_string(),
                    title: None,
                    description: Some(
                        "Repository conventions, local exceptions, and active specs".to_string(),
                    ),
                    mime_type: Some("application/json".to_string()),
                    icons: None,
                }
                .no_annotation(),
                RawResourceTemplate {
                    uri_template: "memory://spec/{spec_id}".to_string(),
                    name: "spec memory".to_string(),
                    title: None,
                    description: Some(
                        "Feature memory, requirements, clarifications, tasks, and evidence"
                            .to_string(),
                    ),
                    mime_type: Some("application/json".to_string()),
                    icons: None,
                }
                .no_annotation(),
                RawResourceTemplate {
                    uri_template: "memory://adr/{adr_id}".to_string(),
                    name: "architecture decision".to_string(),
                    title: None,
                    description: Some(
                        "Architecture decision, alternatives, consequences, and linked events"
                            .to_string(),
                    ),
                    mime_type: Some("application/json".to_string()),
                    icons: None,
                }
                .no_annotation(),
            ],
            next_cursor: None,
            meta: None,
        })
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| EnvFilter::new("info,rmcp=warn,sqlx=warn")),
        )
        .json()
        .with_current_span(false)
        .with_writer(stderr)
        .init();

    let database_url = env::var("MEMORY_DATABASE_URL")
        .unwrap_or_else(|_| panic!("MEMORY_DATABASE_URL is required"));
    let bind_addr = env::var("MEMORY_MCP_BIND").unwrap_or_else(|_| DEFAULT_MCP_BIND.to_string());
    let sanitized_database_url = if let Some((prefix, _)) = database_url.rsplit_once('@') {
        format!("{prefix}@<redacted>")
    } else {
        "<redacted>".to_string()
    };
    tracing::info!(database_url = %sanitized_database_url, %bind_addr, "starting memory mcp server");

    let pool = sqlx::postgres::PgPoolOptions::new()
        .max_connections(5)
        .connect(&database_url)
        .await?;
    tracing::info!("memory mcp database connection established");

    let session_manager = Arc::new(LocalSessionManager::default());
    let service = StreamableHttpService::new(
        {
            let pool = pool.clone();
            move || Ok(MemoryServer::new(pool.clone()))
        },
        session_manager,
        StreamableHttpServerConfig::default(),
    );
    let app = Router::new()
        .route("/healthz", get(|| async { "ok" }))
        .route(
            "/.well-known/oauth-authorization-server",
            get(oauth_authorization_server),
        )
        .route(
            "/.well-known/oauth-authorization-server/mcp",
            get(oauth_authorization_server),
        )
        .route(
            "/mcp/.well-known/oauth-authorization-server",
            get(oauth_authorization_server),
        )
        .route(
            "/.well-known/oauth-protected-resource",
            get(oauth_resource_server),
        )
        .route(
            "/mcp/.well-known/oauth-protected-resource",
            get(oauth_resource_server),
        )
        .route("/oauth/authorize", get(oauth_authorize))
        .route("/oauth/token", get(oauth_token))
        .nest_service("/mcp", service);
    let addr: SocketAddr = bind_addr
        .parse()
        .with_context(|| format!("invalid MEMORY_MCP_BIND: {bind_addr}"))?;
    let listener = tokio::net::TcpListener::bind(addr).await?;

    tracing::info!(%addr, "memory mcp server ready");
    axum::serve(listener, app).await?;
    Ok(())
}
