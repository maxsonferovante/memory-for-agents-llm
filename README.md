# Agent memory architecture repo

This repository is the reference for a coding-agent memory system that works across sessions, across repos, and across agent runtimes. It keeps transient conversation small and turns reusable knowledge into source-backed, versioned Markdown. Claude Code and Codex are both first-class clients of the same canonical memory, ingestion hooks, and MCP read surface.

## Start here

- [`AGENTS.md`](./AGENTS.md) for contributor guidance and repo-specific workflow notes.
- [`QUICKSTART.md`](./QUICKSTART.md) for a one-page onboarding path.
- [`local_stack/README.md`](./local_stack/README.md) for the minimal local Docker Compose implementation.
- [`.codex/README.md`](./.codex/README.md) for Codex agents, hooks, MCP, and project config.

## What this project does now

- Capture source-backed context into `Context Pack`s.
- Turn requests into SDD-ready specs.
- Evaluate architectural impact and emit ADR candidates when needed.
- Review changes for correctness, consistency, security, and knowledge drift.
- Promote repeated learnings into canonical knowledge.
- Share invariants across products and repos without duplicating them.
- Enforce the memory lifecycle with hooks.
- Provide copy-paste session templates for repeatable agent runs.
- Provide a minimal fully-local ingest/index/MCP stack under `local_stack/`.

## Operational layers

- `AGENTS.md` for Codex and generic agent guidance.
- `CLAUDE.md` and `.claude/CLAUDE.md` for Claude Code operating rules.
- `.claude/rules/` for Claude path-aware rules and lifecycle constraints.
- `runtime_sources/claude/subagents/` and `.codex/agents/` for specialized subagents.
- `.agents/skills/` for repo-scoped Codex skills.
- `.claude/templates/` for session-ready prompts.
- `.codex/config.toml` for project-scoped Codex model, subagent, and MCP settings.
- `.codex/hooks.json` and `hooks/` for Codex lifecycle enforcement, event capture, and automatic curation.
- `.claude/skills/` and `.agents/skills/` for reusable workflows.
- `.github/hooks/` for Copilot cloud-agent lifecycle hooks that send session and tool events to the ingestion API.
- `.github/workflows/` for repo automation such as auto-opening pull requests.
- `.github/pull_request_template.md` for the default PR body.

## Local bootstrap

- Codex can use the repo-local `.codex/` and `.agents/skills/` layers directly after the project is trusted.
- `scripts/install_codex_assets.py` installs Codex agents, skills, hooks, and MCP config globally into the user-level Codex locations. It requires `--stack-host` so the generated URLs point at the right proxy.
- `scripts/install_copilot_assets.py` installs GitHub Copilot instructions, prompts, agents, skills, cloud-agent hooks, the Spec Memory event workflow, the workflow helper scripts, and a workspace `.vscode/mcp.json` entry for `localMemory` into a target repository. It supports `--target-repo`, `--dry-run`, `--force`, and optional `--stack-host` for the workflow ingest fallback and MCP URL rendering.
- `scripts/install_claude_assets.py` installs the repo agents, skills, hook wiring, and the project-scoped `localMemory` MCP registration into the local Claude Code config. It also requires `--stack-host`.
- The installer auto-discovers the target path through `CLAUDE_CONFIG_DIR` or `~/.claude`.
- The installers run without prompts and support `--dry-run`, `--force`, `--config-dir`, and `--stack-host` when you need to target a remote stack.
- Recommended first check: run the Claude installer with your local Python 3 launcher, for example `python3 scripts/install_claude_assets.py --dry-run --stack-host 127.0.0.1` on macOS/Linux or `py -3 scripts/install_claude_assets.py --dry-run --stack-host 127.0.0.1` on Windows.
- Recommended install: `python3 scripts/install_claude_assets.py --stack-host 127.0.0.1` or the equivalent launcher on your platform.
- Claude hook settings are written to `~/.claude/settings.json`; Claude project MCP registration is written to `~/.claude.json` under the current repo path.
- `docker compose up --build` starts the local mini stack with API, worker, and MCP server. The base compose file points at Docker Hub images and `docker-compose.override.yml` restores local builds.
- `python3 scripts/smoke_test_local_memory_stack.py` brings the stack up, posts a hook event, and verifies the indexed item plus stored chunk embedding.

## Runtime layout

- `local_stack/api/` is the active Rust ingestion API used by the local stack.
- `local_stack/worker/` is the async indexer.
- `local_stack/mcp-server/` is the Rust MCP read surface.

## Available agents

### Shared specialist roles

- `coordinator` keeps the main session small and orchestrates the flow.
- `context-researcher` gathers the minimum source-backed context and returns a `Context Pack`.
- `spec-analyst` turns a request into an SDD-ready spec.
- `architect` decides boundary changes and produces ADR candidates when needed.
- `implementer` applies code or doc changes guided by the spec.
- `reviewer` checks correctness, consistency, security, and drift.
- `incident-analyst` converts incidents into postmortems, runbooks, and lessons learned.
- `memory-curator` promotes durable learnings into canonical docs.
- `cross-repo-coordinator` synchronizes shared changes across repositories.

Claude source definitions live in `runtime_sources/claude/subagents/*.md` and are installed into Claude's `agents/` directory by `scripts/install_claude_assets.py`. Codex definitions live in `.codex/agents/*.toml` using Codex custom-agent schema.

## Session templates

- [`context-researcher-session.md`](./.claude/templates/context-researcher-session.md) for source-backed research handoffs.
- [`spec-analyst-session.md`](./.claude/templates/spec-analyst-session.md) for SDD-ready spec drafting.
- [`architect-session.md`](./.claude/templates/architect-session.md) for architecture decisions and ADR candidates.
- [`reviewer-session.md`](./.claude/templates/reviewer-session.md) for evidence-backed reviews.
- [`memory-curator-session.md`](./.claude/templates/memory-curator-session.md) for durable memory promotion.

## Skills

- `context-pack` compresses sources into the smallest useful context bundle.
- `memory-curation` turns repeated learning into canonical knowledge updates and promotes ready proposals immediately in the same session.
- `cross-repo-synthesis` compares the same concept across repositories and produces a shared view.

## Hooks

- `PreToolUse` blocks unsafe direct writes to canonical knowledge.
- `PostToolUse` validates whether new memory artifacts are ready for curation.
- `Stop` promotes proposals marked `ready` into canonical knowledge.
- The shared hook utility lives at [`hooks/memory_hooks.py`](./hooks/memory_hooks.py).
- Claude uses an installed hook runner in the local Claude config; Codex uses repo-local `.codex/hooks.json` plus [`hooks/codex_hook_runner.py`](./hooks/codex_hook_runner.py).

## Codex support

- `.codex/config.toml` enables hooks, limits subagent fan-out, and registers both `localMemory` and `openaiDeveloperDocs` MCP servers.
- `.codex/hooks.json` maps Codex lifecycle events to canonical-write guards, proposal validation, ready-proposal promotion, and ingestion events with `source = codex-code-hook`.
- `.codex/agents/*.toml` defines focused custom agents: coordinator, context researcher, spec analyst, architect, implementer, reviewer, curator, and cross-repo coordinator.
- `.agents/skills/` exposes the reusable workflows so Codex can load context-pack, memory-curation, and cross-repo-synthesis instructions from the correct repo-scoped skill path.
- `scripts/install_codex_assets.py` can also copy those skills into the user-level `~/.agents/skills` directory for global use.
- The local memory MCP server remains the shared read layer and is consumed through the Docker-exposed proxy endpoint `http://127.0.0.1:8080/mcp`; remote installs derive the same path from `--stack-host`. Markdown remains the source of truth.

## Local mini stack

- `local_stack/api/` is the Rust ingestion API that receives hook events and writes raw payloads plus metadata.
- `local_stack/worker/` derives structured memory and vector-friendly chunks from raw Markdown.
- `local_stack/mcp-server/` exposes search and resource reads over the official Rust MCP SDK.
- `docker-compose.yml` wires the services together around a shared `/data` volume and a local PostgreSQL metadata store.

## Data transformation pipeline

The local stack does not index raw events directly for search. It first converts them into a staged data model with three distinct layers:

- `ingest_events`: the immutable intake log. This preserves the original event envelope, key metadata, the resolved `content_hash`, and filesystem pointers to the raw files written under `/data/raw`.
- `memory_items`: the document-level projection. One event becomes one normalized memory record with stable metadata such as `repo`, `scope`, `kind`, `title`, `summary`, `status`, `source_file`, and serialized provenance.
- `memory_chunks`: the retrieval-level projection. A single `memory_item` is split into many smaller units optimized for search, ranking, and embedding similarity.

That separation is intentional:

- the API is optimized for durable intake
- the worker is optimized for transformation
- the MCP layer is optimized for retrieval

### Step 1: intake and raw persistence

The transformation starts when a hook, Copilot adapter, Codex hook, Claude hook, or GitHub workflow submits an event to `POST /api/v1/events`.

At ingest time, the Rust API:

- resolves `event_id`, `event_type`, `scope`, and `created_at`
- computes `content_hash` if the producer did not provide one
- creates `/data/raw/<repo>/<event-id>/`
- writes the normalized JSON envelope to `payload.json`
- writes Markdown content to a sanitized filename when `content` exists

This means the system preserves both:

- the structured transport payload
- the text body that will later be transformed into memory

The API then writes:

- one row to `ingest_events`
- one row to `job_queue`

At this point the event is durable, but not yet searchable.

### Step 2: queue handoff to the worker

The worker is a separate async process. It continuously polls `job_queue`, claims the oldest pending runnable job, marks it as `processing`, and loads the matching event from `ingest_events`.

This queue boundary is important because it decouples:

- event capture latency
- indexing latency
- future retries on failed transformations

So the API can stay fast and append-only, while the worker can do heavier parsing and projection work.

### Step 3: reconstruct the text body to transform

The worker does not assume that the producer always sent the text in the same field. It reconstructs the best available source in this order:

1. `event.content`
2. `raw_markdown_path`
3. `raw_payload_path`

If no Markdown-like body can be reconstructed, the worker skips memory derivation and only marks the event as processed. This is how the pipeline avoids generating low-quality vectors from empty or purely structural events.

### Step 4: derive the document-level memory item

Once the worker has text, it builds the document projection.

The worker:

- parses frontmatter when the content starts with a YAML header
- separates frontmatter from body
- derives a title from frontmatter, event fields, or the first H1 heading
- derives a summary from the first sentence or first meaningful body excerpt
- infers `kind` from file path and event type
- infers `status` from event type, for example `canonical` for promoted or canonical sync events and `proposal` otherwise
- carries forward provenance such as `source`, `session_id`, `event_type`, `branch`, `created_at`, and `file_path`

This becomes one row in `memory_items`.

In practice, `memory_items` is the human-readable, document-shaped representation of the event after normalization. It is where the system decides what the event *means* as memory, not just what bytes arrived.

### Step 5: derive sections from Markdown structure

The worker then converts the body into retrieval-oriented structure.

It uses heading-aware parsing:

- Markdown headings `#` through `######` are interpreted as section boundaries
- nested headings become a `heading_path`
- each section retains only the text content that belongs to that heading subtree

If no headings exist, the whole document falls back to a single logical section named `document`.

This step matters because the system does not embed the entire Markdown file as one monolithic vector. It preserves some document hierarchy before chunking.

### Step 6: split sections into bounded chunks

For each derived section, the worker runs a chunker with a maximum character budget.

The chunker:

- normalizes excessive blank lines
- splits primarily on paragraph boundaries
- merges adjacent paragraphs while the chunk stays under the limit
- falls back to raw slicing only when one paragraph alone exceeds the maximum

The result is a list of compact text fragments that are much better suited for retrieval than the original full document.

Each chunk receives:

- `memory_item_id`
- `repo`
- `scope`
- `kind`
- `heading_path`
- `chunk_index`
- `chunk_text`
- `token_count`
- `source_file`
- serialized provenance

This is the real transformation boundary where one event becomes many retrieval units.

### Step 7: generate vectors

For every chunk, the worker computes an embedding and stores it in `memory_chunks.embedding`.

Today the embedding is deterministic and local:

- tokenize text into normalized words
- hash each word with SHA-256
- map each word into one of 48 dimensions
- apply a signed weighted accumulation
- L2-normalize the final vector

This is not meant to be a high-quality semantic model forever. It is a cheap local embedding strategy that preserves the full storage contract:

- one vector per chunk
- fixed dimensionality
- cosine-similarity-friendly normalization
- compatibility with `pgvector`

That lets the retrieval system work now without requiring an external embedding service.

### Step 8: replace the retrieval projection

After chunk generation, the worker replaces all existing chunks for the current `memory_item_id`.

The replacement strategy is:

- delete old `memory_chunks` rows for the item
- insert the new chunk set

This means the chunk projection is treated as a rebuildable derivative, not as the source of truth. The stable source remains:

- the canonical Markdown in the repo
- the raw ingest payload under `/data/raw`
- the normalized memory item metadata in `memory_items`

### Step 9: finalize processing state

When transformation succeeds:

- `job_queue.status` becomes `done`
- `ingest_events.status` becomes `processed`
- `processed_at` is set
- `error` is cleared

When transformation fails:

- `job_queue.status` becomes `failed`
- `ingest_events.status` becomes `failed`
- the error text is persisted

This gives the stack a basic replay and debugging surface without losing the raw evidence.

## Vector and database layout

The PostgreSQL schema separates intake, transformation control, document projection, and vector projection:

- `ingest_events`
  - one row per accepted event
  - stores transport metadata and raw file pointers
  - acts as the append-only intake ledger
- `job_queue`
  - one row per event scheduled for transformation
  - tracks pending, processing, done, and failed states
  - is the coordination point between API and worker
- `memory_items`
  - one row per derived memory object
  - stores the normalized semantic identity of the event as memory
  - is the document-level projection consumed by listing and item reads
- `memory_chunks`
  - many rows per memory item
  - stores retrieval fragments and vectors
  - is the query surface for semantic similarity and chunk-level recall

### Important columns

- `ingest_events.raw_payload_path`: where the preserved JSON envelope lives on disk
- `ingest_events.raw_markdown_path`: where the preserved Markdown body lives on disk
- `memory_items.provenance_json`: serialized source and lineage metadata
- `memory_chunks.heading_path`: structural position of the chunk inside the document
- `memory_chunks.embedding`: `vector(48)` value used for similarity search
- `memory_chunks.token_count`: cheap size hint for retrieval and budgeting

### Vector storage

Vector storage lives in `memory_chunks.embedding` as `vector(48)` via `pgvector`. The schema also creates an `ivfflat` cosine index so similarity search can scale beyond sequential scans.

The current worker does not call an external embedding model. Instead, it uses a deterministic hashed embedding from the chunk text:

- tokenize text into normalized words
- hash each word with SHA-256
- map each word into one of 48 dimensions
- accumulate signed weighted values per dimension
- normalize the final vector to unit length

This keeps the pipeline local, reproducible, and cheap. It is intentionally a placeholder embedding strategy, but the storage contract is already the same shape expected by a stronger embedding backend later.

### Why the worker exists

The worker's main transformation responsibility is not just "save Markdown". It converts one raw event into:

- one canonical memory item for metadata and provenance
- zero or more derived sections
- many retrieval chunks for semantic search
- one vector per chunk for similarity queries

That is why the save path is split between the API and the worker:

- the API is responsible for durable intake
- the worker is responsible for semantic transformation
- the MCP server is responsible for read-time access

In other words, the worker is the projection engine of the local memory stack.

### Useful commands

- `python3 scripts/install_claude_assets.py --dry-run --stack-host 127.0.0.1`
- `python3 scripts/install_claude_assets.py --force --stack-host 127.0.0.1`
- `python3 scripts/install_codex_assets.py --dry-run --stack-host 127.0.0.1`
- `python3 scripts/install_copilot_assets.py --dry-run --target-repo /path/to/repo --stack-host 127.0.0.1`
- `python3 scripts/install_copilot_assets.py --force --target-repo /path/to/repo --stack-host 127.0.0.1`
- `python3 scripts/install_codex_assets.py --force --stack-host 127.0.0.1`
- `python3 scripts/publish_local_stack_images.py --version v0.1.0 --dry-run`
- `python3 scripts/package_release.py --version v0.1.0`
- `python3 scripts/package_release.py --version v0.1.0 --include-knowledge`
- `python3 scripts/install_public_release.py --source dist/releases/memory-for-agents-llm-v0.1.0.tar.gz --dry-run --stack-host 127.0.0.1`
- `python3 hooks/memory_hooks.py guard-write --path knowledge/org/memory-governance.md`
- `python3 hooks/memory_hooks.py validate-proposal knowledge/_proposals/2026-06-09-memory-foundation/01-memory-governance.md`
- `python3 hooks/memory_hooks.py promote-ready --queue knowledge/_proposals`

## Pull request automation

- Branches that start with `feature/` can be opened as pull requests by the workflow in `.github/workflows/auto-open-pr-on-feature-branch.yml`.
- That automation requires a repository secret named `PR_AUTOMATION_TOKEN` with `pull_requests: write` permission.
- If the secret is not configured, the workflow emits a notice and skips PR creation instead of failing.

## Docker Hub publish

- The workflow in `.github/workflows/publish-local-stack-images.yml` publishes the API, worker, and MCP images on `v*` tags and through manual dispatch.
- It requires a repository secret named `DOCKERHUB_TOKEN` with push access to the `maxsonferovante` namespace.

## Knowledge model

- `knowledge/org/` holds organization-wide invariants and policies.
- `knowledge/products/` holds product-wide shared behavior.
- `knowledge/domains/` holds business-domain rules and glossary terms.
- `knowledge/repos/` holds repo-specific conventions and local deltas.
- `knowledge/specs/` holds SDD specs and historical specs.
- `knowledge/adr/` holds architecture decision records.
- `knowledge/incidents/` holds incidents and postmortems.
- `knowledge/runbooks/` holds operational runbooks.
- `knowledge/glossary/` holds canonical domain terms.
- `knowledge/integrations/` holds external systems and contracts.
- `knowledge/_proposals/` holds draft memory updates, ADR candidates, and cross-repo notes.

## What is already documented here

- [`knowledge/org/`](./knowledge/org/) contains the canonical phase-1 memory contracts.
- [`knowledge/products/claude-code-memory-platform/`](./knowledge/products/claude-code-memory-platform/) shows a shared product memory contract.
- [`knowledge/repos/memory-for-agents-llm/`](./knowledge/repos/memory-for-agents-llm/) shows repo-local overrides.
- [`knowledge/_proposals/2026-06-09-memory-foundation/`](./knowledge/_proposals/2026-06-09-memory-foundation/) is the first proposal package.
- [`knowledge/_proposals/2026-06-09-memory-foundation/06-context-pack-example.md`](./knowledge/_proposals/2026-06-09-memory-foundation/06-context-pack-example.md) is a concrete Context Pack example.
- [`knowledge/org/memory-curator-promotion-example.md`](./knowledge/org/memory-curator-promotion-example.md) is a concrete promotion record.

## Supported flows

- Research flow: source docs -> context pack -> task work -> memory delta -> canonical docs -> next session.
- SDD flow: request -> spec -> architecture decision if needed -> implementation -> review -> memory promotion.
- Memory flow: proposal -> validation -> ready -> promotion -> canonical.
- Cross-repo flow: shared invariant -> product note -> repo delta -> sync plan.
- Incident flow: incident -> postmortem -> runbook -> lessons learned -> canonical promotion.

## What you can ask the system to do now

- Build a source-backed context pack for a task, repo, product, or domain.
- Draft or revise an SDD spec from a problem statement.
- Decide whether a change needs an ADR.
- Implement code or docs from an approved spec.
- Review a diff or document for correctness and drift.
- Promote a repeated learning into canonical knowledge.
- Compare the same rule across multiple repos and decide the canonical home.
- Turn an incident into a runbook, a postmortem, or a durable lesson.
- Prepare a repo handoff for another session or another repo.
- Open a pull request automatically when a `feature/*` branch is created or pushed, using the predefined PR template.

## Typical workflow

1. Read `CLAUDE.md` and `.claude/CLAUDE.md`.
2. Use `context-researcher` to gather the minimum source-backed context.
3. Use `spec-analyst` to turn the request into a testable spec.
4. Use `architect` when the change affects boundaries, dependencies, or persistence.
5. Use `implementer` to apply the change.
6. Use `reviewer` to validate correctness and drift.
7. Use `memory-curator` to promote the durable learning.
8. Let the hooks block unsafe writes and promote `ready` proposals automatically.
9. Create a `feature/*` branch and let GitHub Actions open the PR with the default template.

## Memory contract

- A proposal is not canonical until it is reviewed.
- A canonical note must always show scope, provenance, and ownership.
- A replacement note must explicitly say what it supersedes.
- Stable shared knowledge belongs in the highest applicable scope.
- Repo-local exceptions should link back to the shared canonical note instead of copying it silently.

## Goal of the repo

The goal is not to store everything in prompt context. The goal is to keep the prompt small and make the durable knowledge explicit, source-backed, and versioned.
