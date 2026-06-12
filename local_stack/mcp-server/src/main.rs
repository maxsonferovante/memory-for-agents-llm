use std::{
    collections::HashSet,
    env,
    fs,
    io::stderr,
    path::{Path, PathBuf},
    sync::Arc,
};

use anyhow::{Context, Result};
use rmcp::{
    handler::server::{router::tool::ToolRouter, wrapper::Parameters},
    model::*,
    schemars::JsonSchema,
    service::RequestContext,
    tool, tool_handler, tool_router, ErrorData as McpError, RoleServer, ServerHandler,
    ServiceExt,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use tokio::io::stdin;
use tracing_subscriber::EnvFilter;

#[derive(Clone)]
struct MemoryServer {
    index_path: Arc<PathBuf>,
    tool_router: ToolRouter<Self>,
}

impl MemoryServer {
    fn new(index_path: PathBuf) -> Self {
        Self {
            index_path: Arc::new(index_path),
            tool_router: Self::tool_router(),
        }
    }
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct MemoryIndex {
    generated_at: String,
    items: Vec<MemoryItem>,
    chunks: Vec<MemoryChunk>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct MemoryItem {
    id: String,
    event_id: String,
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
    provenance: serde_json::Value,
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
    provenance: serde_json::Value,
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
        let index = u32::from_be_bytes([digest[0], digest[1], digest[2], digest[3]]) as usize % dimensions;
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

fn cosine_similarity(left: &[f64], right: &[f64]) -> f64 {
    left.iter()
        .zip(right.iter())
        .map(|(a, b)| a * b)
        .sum::<f64>()
}

fn load_index(path: &Path) -> Result<MemoryIndex> {
    tracing::debug!(index_path = %path.display(), "loading memory index");
    let raw = fs::read_to_string(path)
        .with_context(|| format!("failed to read index file {}", path.display()))?;
    let index: MemoryIndex = serde_json::from_str(&raw)
        .with_context(|| format!("failed to parse index file {}", path.display()))?;
    tracing::debug!(
        index_path = %path.display(),
        items = index.items.len(),
        chunks = index.chunks.len(),
        generated_at = %index.generated_at,
        "memory index loaded"
    );
    Ok(index)
}

fn filter_items<'a>(
    index: &'a MemoryIndex,
    repo: Option<&str>,
    scope: Option<&str>,
    kind: Option<&str>,
) -> Vec<&'a MemoryItem> {
    index
        .items
        .iter()
        .filter(move |item| {
        repo.map(|value| item.repo == value).unwrap_or(true)
            && scope.map(|value| item.scope == value).unwrap_or(true)
            && kind.map(|value| item.kind == value).unwrap_or(true)
        })
        .collect()
}

fn score_item(index: &MemoryIndex, item: &MemoryItem, query: &str) -> f64 {
    let query_words: HashSet<String> = normalize_words(query).into_iter().collect();
    let lexical_source = format!("{} {} {}", item.title, item.summary, item.source_file);
    let lexical_words = normalize_words(&lexical_source);
    let overlap = lexical_words
        .iter()
        .filter(|word| query_words.contains(*word))
        .count() as f64;
    let query_embedding = hash_embedding(query, 48);
    let mut vector_score = 0.0_f64;
    for chunk in index.chunks.iter().filter(|chunk| chunk.memory_item_id == item.id) {
        vector_score = vector_score.max(cosine_similarity(&query_embedding, &chunk.embedding));
    }
    let lexical_score = overlap / (query_words.len().max(1) as f64);
    (lexical_score * 0.6) + (vector_score.max(0.0) * 0.4)
}

fn item_chunks<'a>(index: &'a MemoryIndex, item_id: &str) -> Vec<&'a MemoryChunk> {
    index
        .chunks
        .iter()
        .filter(|chunk| chunk.memory_item_id == item_id)
        .collect()
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
            limit = args.limit.unwrap_or(10),
            "mcp search_memory called"
        );
        let index = load_index(&self.index_path)
            .map_err(|error| McpError::internal_error("index_load_error", Some(serde_json::json!({
                "message": error.to_string(),
            }))))?;
        let limit = args.limit.unwrap_or(10).max(1) as usize;
        let mut results: Vec<_> = filter_items(
            &index,
            args.repo.as_deref(),
            args.scope.as_deref(),
            args.kind.as_deref(),
        )
        .into_iter()
        .map(|item| {
            let score = score_item(&index, item, &args.query);
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
        let index = load_index(&self.index_path)
            .map_err(|error| McpError::internal_error("index_load_error", Some(serde_json::json!({
                "message": error.to_string(),
            }))))?;
        let item = index
            .items
            .iter()
            .find(|candidate| candidate.id == args.id)
            .ok_or_else(|| McpError::resource_not_found("memory_item_not_found", Some(serde_json::json!({
                "id": args.id,
            }))))?;
        let chunks = item_chunks(&index, &item.id);
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
        let index = load_index(&self.index_path)
            .map_err(|error| McpError::internal_error("index_load_error", Some(serde_json::json!({
                "message": error.to_string(),
            }))))?;
        let items: Vec<_> = index
            .items
            .iter()
            .filter(|item| item.repo == args.repo)
            .collect();
        tracing::info!(repo = %args.repo, item_count = items.len(), "mcp get_repo_context_pack completed");
        Ok(serde_json::json!({
            "repo": args.repo,
            "generated_at": index.generated_at,
            "items": items,
        })
        .to_string())
    }
}

#[tool_handler(router = self.tool_router)]
impl ServerHandler for MemoryServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo {
            instructions: Some("Search the local memory index and read structured resources.".into()),
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
        let index = load_index(&self.index_path)
            .map_err(|error| McpError::internal_error("index_load_error", Some(serde_json::json!({
                "message": error.to_string(),
            }))))?;
        let mut resources = vec![
            RawResource::new("memory://org/invariants", "org invariants").no_annotation(),
        ];
        for item in index.items.iter().take(100) {
            resources.push(
                RawResource::new(format!("memory://items/{}", item.id), item.title.clone())
                    .no_annotation(),
            );
        }
        tracing::info!(resource_count = resources.len(), "mcp list_resources completed");
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
        let index = load_index(&self.index_path)
            .map_err(|error| McpError::internal_error("index_load_error", Some(serde_json::json!({
                "message": error.to_string(),
            }))))?;
        match request.uri.as_str() {
            "memory://org/invariants" => {
                let items: Vec<_> = index
                    .items
                    .iter()
                    .filter(|item| item.scope == "org" || item.kind == "lesson")
                    .collect();
                Ok(ReadResourceResult {
                    contents: vec![ResourceContents::text(
                        serde_json::json!({
                            "uri": request.uri,
                            "generated_at": index.generated_at,
                            "items": items,
                        })
                        .to_string(),
                        &request.uri,
                    )],
                })
            }
            uri if uri.starts_with("memory://items/") => {
                let item_id = uri.trim_start_matches("memory://items/");
                let item = index
                    .items
                    .iter()
                    .find(|candidate| candidate.id == item_id)
                    .ok_or_else(|| {
                        McpError::resource_not_found(
                            "memory_item_not_found",
                            Some(serde_json::json!({
                                "uri": request.uri,
                            })),
                        )
                    })?;
                let chunks = item_chunks(&index, &item.id);
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
            resource_templates: vec![],
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
                .unwrap_or_else(|_| EnvFilter::new("info,rmcp=warn")),
        )
        .json()
        .with_current_span(false)
        .with_writer(stderr)
        .init();

    let index_path = env::var("MEMORY_INDEX_PATH").unwrap_or_else(|_| "/data/derived/index.json".into());
    tracing::info!(index_path = %index_path, "starting memory mcp server");
    let server = MemoryServer::new(PathBuf::from(index_path));

    let service = server.serve((stdin(), tokio::io::stdout())).await?;
    tracing::info!("memory mcp server ready");
    service.waiting().await?;
    Ok(())
}
