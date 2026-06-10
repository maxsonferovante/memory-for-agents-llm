# Operating contract

This repo is a reference implementation for Claude Code memory and agent orchestration.

## Canonical order

1. Canonical docs in `knowledge/`
2. Repo instructions in `.claude/CLAUDE.md`
3. Rules in `.claude/rules/`
4. Skills in `.claude/skills/`
5. Subagents in `.claude/agents/`
6. Live conversation

## Operating rules

- Keep the main conversation small.
- Use `context-researcher` before synthesizing new facts.
- Use `spec-analyst` before implementation work.
- Use `architect` when the change affects boundaries, dependencies, or persistence.
- Use `reviewer` before accepting changes.
- Use `memory-curator` when a durable learning should become canonical.
- Use `cross-repo-coordinator` when the same concept appears in more than one repo.
- Use the session templates in `.claude/templates/` when you need a copy-paste prompt for a repeatable agent run.

## Memory rules

- Do not promote an unverified claim into canonical knowledge.
- If a fact is stable and reusable, write a proposal into `knowledge/_proposals/`.
- If a decision changes architecture, create an ADR candidate.
- If a workflow repeats, extract it into a skill.
- If a rule must apply every time, put it in CLAUDE.md or `.claude/rules/`.
- Use hooks to block direct canonical writes and to promote ready proposals automatically.

## Standard outputs

Use these output blocks when possible:

- `Context Pack`: the smallest useful bundle of authoritative facts
- `Memory Delta`: a proposed canonical update with source links
- `ADR Candidate`: a decision record with context, options, and consequences
- `Repo Handoff`: a short summary that another repo or session can consume
