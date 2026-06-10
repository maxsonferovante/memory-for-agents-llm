# Claude memory architecture repo

This repository is the phase-1 reference for a Claude Code memory system that works across sessions and across repos. It keeps transient conversation small and turns reusable knowledge into source-backed, versioned Markdown.

## Start here

- [`QUICKSTART.md`](./QUICKSTART.md) for a one-page onboarding path.

## What this project does now

- Capture source-backed context into `Context Pack`s.
- Turn requests into SDD-ready specs.
- Evaluate architectural impact and emit ADR candidates when needed.
- Review changes for correctness, consistency, security, and knowledge drift.
- Promote repeated learnings into canonical knowledge.
- Share invariants across products and repos without duplicating them.
- Enforce the memory lifecycle with hooks.
- Provide copy-paste session templates for repeatable agent runs.

## Operational layers

- `CLAUDE.md` and `.claude/CLAUDE.md` for always-on operating rules.
- `.claude/rules/` for path-aware rules and lifecycle constraints.
- `.claude/agents/` for specialized subagents.
- `.claude/templates/` for session-ready prompts.
- `hooks/` for enforcement and automatic curation.
- `.claude/skills/` for reusable workflows.
- `.github/workflows/` for repo automation such as auto-opening pull requests.
- `.github/pull_request_template.md` for the default PR body.

## Local bootstrap

- `scripts/install_claude_assets.py` installs the repo agents, skills, and hook wiring into the local Claude Code config directory.
- The installer auto-discovers the target path through `CLAUDE_CONFIG_DIR` or `~/.claude`.
- It runs without prompts and supports `--dry-run`, `--force`, and `--config-dir`.
- Recommended first check: run it with your local Python 3 launcher, for example `python3 scripts/install_claude_assets.py --dry-run` on macOS/Linux or `py -3 scripts/install_claude_assets.py --dry-run` on Windows.
- Recommended install: `python3 scripts/install_claude_assets.py` or the equivalent launcher on your platform.

## Available agents

- `coordinator` keeps the main session small and orchestrates the flow.
- `context-researcher` gathers the minimum source-backed context and returns a `Context Pack`.
- `spec-analyst` turns a request into an SDD-ready spec.
- `architect` decides boundary changes and produces ADR candidates when needed.
- `implementer` applies code or doc changes guided by the spec.
- `reviewer` checks correctness, consistency, security, and drift.
- `incident-analyst` converts incidents into postmortems, runbooks, and lessons learned.
- `memory-curator` promotes durable learnings into canonical docs.
- `cross-repo-coordinator` synchronizes shared changes across repositories.

## Session templates

- [`context-researcher-session.md`](./.claude/templates/context-researcher-session.md) for source-backed research handoffs.
- [`spec-analyst-session.md`](./.claude/templates/spec-analyst-session.md) for SDD-ready spec drafting.
- [`architect-session.md`](./.claude/templates/architect-session.md) for architecture decisions and ADR candidates.
- [`reviewer-session.md`](./.claude/templates/reviewer-session.md) for evidence-backed reviews.
- [`memory-curator-session.md`](./.claude/templates/memory-curator-session.md) for durable memory promotion.

## Skills

- `context-pack` compresses sources into the smallest useful context bundle.
- `memory-curation` turns repeated learning into canonical knowledge updates.
- `cross-repo-synthesis` compares the same concept across repositories and produces a shared view.

## Hooks

- `PreToolUse` blocks unsafe direct writes to canonical knowledge.
- `PostToolUse` validates whether new memory artifacts are ready for curation.
- `Stop` promotes proposals marked `ready` into canonical knowledge.
- The hook utility lives at [`hooks/memory_hooks.py`](./hooks/memory_hooks.py).
- The installer copies the hook bundle into the local Claude config and wires it through `settings.json`.

### Useful commands

- `python3 scripts/install_claude_assets.py --dry-run`
- `python3 scripts/install_claude_assets.py --force`
- `python3 hooks/memory_hooks.py guard-write --path knowledge/org/memory-governance.md`
- `python3 hooks/memory_hooks.py validate-proposal knowledge/_proposals/2026-06-09-memory-foundation/01-memory-governance.md`
- `python3 hooks/memory_hooks.py promote-ready --queue knowledge/_proposals`

## Pull request automation

- Branches that start with `feature/` can be opened as pull requests by the workflow in `.github/workflows/auto-open-pr-on-feature-branch.yml`.
- That automation requires a repository secret named `PR_AUTOMATION_TOKEN` with `pull_requests: write` permission.
- If the secret is not configured, the workflow emits a notice and skips PR creation instead of failing.

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
