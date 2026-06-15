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
- `.claude/agents/` and `.codex/agents/` for specialized subagents.
- `.agents/skills/` for repo-scoped Codex skills.
- `.claude/templates/` for session-ready prompts.
- `.codex/config.toml` for project-scoped Codex model, subagent, and MCP settings.
- `.codex/hooks.json` and `hooks/` for Codex lifecycle enforcement, event capture, and automatic curation.
- `.claude/skills/` and `.agents/skills/` for reusable workflows.
- `.github/workflows/` for repo automation such as auto-opening pull requests.
- `.github/pull_request_template.md` for the default PR body.

## Local bootstrap

- Codex can use the repo-local `.codex/` and `.agents/skills/` layers directly after the project is trusted.
- `scripts/install_codex_assets.py` installs Codex agents, skills, hooks, and MCP config globally into the user-level Codex locations. It requires `--stack-host` so the generated URLs point at the right proxy.
- `scripts/install_copilot_assets.py` installs GitHub Copilot instructions, prompts, agents, skills, and the Spec Memory event workflow into a target repository. It supports `--target-repo`, `--dry-run`, `--force`, and optional `--stack-host` for the workflow ingest fallback.
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

Claude definitions live in `.claude/agents/*.md`. Codex definitions live in `.codex/agents/*.toml` using Codex custom-agent schema.

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

### Useful commands

- `python3 scripts/install_claude_assets.py --dry-run --stack-host 127.0.0.1`
- `python3 scripts/install_claude_assets.py --force --stack-host 127.0.0.1`
- `python3 scripts/install_codex_assets.py --dry-run --stack-host 127.0.0.1`
- `python3 scripts/install_copilot_assets.py --dry-run --target-repo /path/to/repo --stack-host 127.0.0.1`
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
