# Quickstart

This repo is the phase-1 reference for Claude Code memory and agent orchestration. Use it when you want Claude Code to work with a small live context and a durable, source-backed knowledge base.

## Read this first

1. `README.md`
2. `CLAUDE.md`
3. `knowledge/README.md`
4. `knowledge/org/README.md`
5. `knowledge/_proposals/README.md`

## Optional bootstrap

If you want the local Claude Code config to receive the repo agents, skills, and hooks in one pass, run:

```bash
python3 scripts/install_claude_assets.py --dry-run  # macOS/Linux
py -3 scripts/install_claude_assets.py --dry-run     # Windows
python3 scripts/install_claude_assets.py             # macOS/Linux
py -3 scripts/install_claude_assets.py               # Windows
```

The script discovers `~/.claude` automatically or uses `CLAUDE_CONFIG_DIR` when present. Use `--force` only when you intentionally want to overwrite differing local files.

## Public release flow

To build a versioned release artifact and install it from a path or URL:

```bash
python3 scripts/package_release.py --version v0.1.0
python3 scripts/install_public_release.py --source dist/releases/memory-for-agents-llm-v0.1.0.tar.gz --dry-run
python3 scripts/install_public_release.py --source https://example.com/releases/memory-for-agents-llm-v0.1.0.tar.gz
```

Use `--include-knowledge` with the packaging script when you want the full memory reference package instead of the runtime-only package.

## Backend deployment flow

To build and deploy the self-hosted AWS memory backend in one release flow:

```bash
export AWS_PROFILE=your-profile
export AWS_REGION=us-east-1
export API_KEY_VALUE=replace-with-a-secret
python3 scripts/release_central_memory_backend.py --aws-region "${AWS_REGION}" --api-key-value "${API_KEY_VALUE}" --auto-approve
source dist/backend/central-memory-backend/backend.env
echo "$API_BASE_URL"
echo "$API_KEY_HEADER"
python3 scripts/smoke_test_central_memory_backend.py --env-file dist/backend/central-memory-backend/backend.env
```

If you set a `backend_auth_token`, export `BACKEND_AUTH_TOKEN=...` before running the release script. The script writes that value into `dist/backend/central-memory-backend/backend.env` so the local client can reuse the same auth contract.
The hook runtime also loads that same `backend.env` automatically when present.

## Pull request automation

Feature branches can be opened automatically by GitHub Actions when `PR_AUTOMATION_TOKEN` is configured with `pull_requests: write`. Without that secret, the workflow skips PR creation and leaves the branch ready for manual PR opening.

## The mental model

- Git is the source of truth.
- `knowledge/` stores durable memory.
- `knowledge/_proposals/` is the staging area before promotion.
- `CLAUDE.md`, `.claude/rules/`, `.claude/agents/`, `.claude/templates/`, `.claude/skills/`, and `hooks/` define how Claude Code behaves in this repo.
- `.github/workflows/` and `.github/pull_request_template.md` automate pull request creation for `feature/*` branches.

## Standard flow

1. `context-researcher` gathers the minimum source-backed context.
2. `spec-analyst` turns the request into an SDD-ready spec.
3. `architect` decides whether the change needs an ADR.
4. `implementer` applies the code or doc change.
5. `reviewer` checks correctness, consistency, security, and drift.
6. `memory-curator` promotes the durable learning into canonical knowledge.
7. `hooks` block unsafe writes and promote proposals marked `ready`.
8. GitHub Actions opens a pull request automatically for `feature/*` branches and uses the predefined PR template.

## Where knowledge goes

- `knowledge/org/`: org-wide invariants and policies.
- `knowledge/products/`: shared behavior for one product across repos.
- `knowledge/domains/`: domain rules and glossary terms.
- `knowledge/repos/`: repo-local conventions and exceptions.
- `knowledge/specs/`: SDD specs.
- `knowledge/adr/`: architecture decisions.
- `knowledge/incidents/`: incidents and postmortems.
- `knowledge/runbooks/`: operational recovery steps.
- `knowledge/glossary/`: canonical terms.
- `knowledge/integrations/`: external contracts.
- `knowledge/_proposals/`: drafts before promotion.

## What you can ask Claude to do

- Build a `Context Pack` for a task, repo, product, or domain.
- Draft or revise a spec before implementation.
- Check whether a change needs an ADR.
- Review code or docs for drift and inconsistencies.
- Promote repeated learning into canonical knowledge.
- Compare a shared rule across multiple repos.
- Turn incidents into runbooks and durable lessons.

## Useful commands

```bash
python3 hooks/memory_hooks.py validate-proposal knowledge/_proposals/2026-06-09-memory-foundation/01-memory-governance.md
python3 hooks/memory_hooks.py guard-write --path knowledge/org/memory-governance.md
python3 hooks/memory_hooks.py promote-ready --queue knowledge/_proposals
```

## Rules of thumb

- Keep the main conversation small.
- Never promote unverified claims.
- Keep shared facts in the highest applicable scope.
- Link to canonical notes instead of copying them silently.
- If you are unsure where a fact belongs, leave it in `knowledge/_proposals/` until it is resolved.
