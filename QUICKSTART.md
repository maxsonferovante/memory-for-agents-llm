# Quickstart

This repo is the phase-1 reference for Claude Code memory and agent orchestration. Use it when you want Claude Code to work with a small live context and a durable, source-backed knowledge base.

## Read this first

1. `README.md`
2. `CLAUDE.md`
3. `knowledge/README.md`
4. `knowledge/org/README.md`
5. `knowledge/_proposals/README.md`

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
