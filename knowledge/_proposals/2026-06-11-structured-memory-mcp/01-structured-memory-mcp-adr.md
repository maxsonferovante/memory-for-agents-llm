---
id: prop-structured-memory-mcp-adr-v1
type: proposal
scope: product
status: promoted
owner: cross-repo-coordinator
target_path: knowledge/adr/structured-memory-mcp-roadmap.md
supersedes: null
confidence: high
---

# Structured memory and MCP roadmap ADR candidate

## Problem

The central memory backend currently gives agents a durable snapshot store, but the next evolution needs search, structured retrieval, and cross-repo consumption without replacing the reviewed Markdown knowledge base with an opaque vector database.

## Proposal

Adopt a three-layer evolution:

1. Capture reliable memory events from Claude Code hooks into raw storage and metadata.
2. Process published memory into structured records and vector chunks as derived indexes.
3. Expose retrieval through an MCP server with tools, resources, and prompts.

Markdown in `knowledge/` remains the versioned source of truth. Structured stores and vector stores are derived retrieval layers that can be rebuilt from raw snapshots and canonical files.

## Target architecture

```txt
Claude Code hooks
   ↓
Memory Backend API
   ↓
Raw Storage + Metadata DB
   ↓
Processor/Indexer
   ↓
Structured Memory DB + Vector DB
   ↓
MCP Server
   ↓
Claude Code / Agents
```

## Rationale

- The repository already organizes durable memory by org, product, domain, repo, spec, ADR, runbook, glossary, and proposal scope.
- Raw event capture is the safest first step because it preserves provenance before semantic extraction is introduced.
- Structured memory records make governance, supersession, status, and ownership queryable without relying on embeddings.
- Vector chunks improve recall, but they should not be the official memory record.
- MCP is the consumption boundary for agents; it should not be treated as the database.

## Alternatives considered

- Move directly to RAG as the primary store.
  - Rejected because it would weaken reviewability and make Markdown governance secondary.
- Use only immutable snapshots with no derived index.
  - Rejected because retrieval across repos, decisions, and lessons would remain too manual.
- Put MCP directly on raw files without a structured index.
  - Rejected because tools need stable filters such as repo, scope, type, status, and provenance.

## Consequences

- The decision records a staged evolution rather than a one-step RAG migration.
- The backend roadmap stays incremental: capture first, index later, expose through MCP after the retrieval contract is stable.
- Raw storage and canonical Markdown provide rebuildability if a vector provider or schema changes.
- The system can run locally with FastAPI plus filesystem plus SQLite/Postgres, or in AWS with API Gateway plus Lambda plus S3 plus DynamoDB.
- Search providers such as OpenSearch Serverless Vector Search or Bedrock Knowledge Bases are implementation options, not architectural sources of truth.

## Sources

- [knowledge/README.md](../../../knowledge/README.md)
- [knowledge/integrations/central-memory-backend.md](../../../knowledge/integrations/central-memory-backend.md)
- [knowledge/adr/central-memory-backend.md](../../../knowledge/adr/central-memory-backend.md)
- [knowledge/org/memory-governance.md](../../../knowledge/org/memory-governance.md)
- [knowledge/org/context-pack-contract.md](../../../knowledge/org/context-pack-contract.md)
- [knowledge/products/claude-code-memory-platform/shared-memory-contract.md](../../../knowledge/products/claude-code-memory-platform/shared-memory-contract.md)
- [AWS OpenSearch Serverless vector search documentation](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless-vector-search.html)
- [Model Context Protocol specification](https://modelcontextprotocol.io/specification/2025-03-26)

## Acceptance criteria

- The decision explicitly keeps Markdown as canonical memory.
- The roadmap separates capture, processing, indexing, and MCP consumption.
- Structured memory and vector memory are defined as derived stores.
- The MCP boundary exposes retrieval capabilities without becoming the persistence layer.
- The design supports both local and AWS deployments.
