# Operating contract

This repo is the phase-1 reference for Claude Code memory and agent orchestration.

## What this repo does now

- Capture source-backed context into `Context Pack`s.
- Turn requests into SDD-ready specs.
- Evaluate architectural impact and emit ADR candidates when needed.
- Review changes for correctness, consistency, security, and knowledge drift.
- Promote repeated learnings into canonical knowledge.
- Share invariants across products and repos without duplicating them.
- Enforce the memory lifecycle with hooks.
- Provide copy-paste session templates for repeatable agent runs.

## Canonical order

1. Canonical docs in `knowledge/`
2. Repo instructions in `.claude/CLAUDE.md`
3. Rules in `.claude/rules/`
4. Templates in `.claude/templates/`
5. Skills in `.claude/skills/`
6. Subagents in `.claude/agents/`
7. Live conversation

## Operating rules

- Keep the main conversation small.
- Use `context-researcher` before synthesizing new facts.
- Use `spec-analyst` before implementation work.
- Use `architect` when the change affects boundaries, dependencies, or persistence.
- Use `reviewer` before accepting changes.
- Use `memory-curator` when a durable learning should become canonical.
- Use `cross-repo-coordinator` when the same concept appears in more than one repo.
- Use the session templates in `.claude/templates/` when you need a copy-paste prompt for a repeatable agent run.
- Start with [`QUICKSTART.md`](./QUICKSTART.md) if you are new to the repo.
- Use [`scripts/install_claude_assets.py`](./scripts/install_claude_assets.py) to bootstrap the local Claude config with the repo agents, skills, and hook wiring.

## Memory rules

- Do not promote an unverified claim into canonical knowledge.
- If a fact is stable and reusable, write a proposal into `knowledge/_proposals/`.
- If a decision changes architecture, create an ADR candidate.
- If a workflow repeats, extract it into a skill.
- If a rule must apply every time, put it in `CLAUDE.md` or `.claude/rules/`.
- Use hooks to block direct canonical writes and to promote ready proposals automatically.
- End every user-facing answer with a short offer to convert the reusable outcome into durable knowledge.

## Standard outputs

Use these output blocks when possible:

- `Context Pack`: the smallest useful bundle of authoritative facts.
- `Memory Delta`: a proposed canonical update with source links.
- `ADR Candidate`: a decision record with context, options, and consequences.
- `Repo Handoff`: a short summary that another repo or session can consume.
