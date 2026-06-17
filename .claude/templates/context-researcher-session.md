---
name: context-researcher-session
agent: context-researcher
status: active
scope: session
source:
  - ../../runtime_sources/claude/subagents/context-researcher.md
  - ../../knowledge/org/context-pack-contract.md
  - ../../knowledge/org/knowledge-scope-model.md
supersedes: null
---

# Context researcher session template

Use this template when the main session needs a compact, source-backed Context Pack.

## Required inputs

- Task objective
- Scope
- Repository names or product/domain names
- Seed sources
- Known proposal paths
- Whether the result must cross repos

## Operating steps

1. Classify the scope before reading deeply.
2. Read the canonical org contracts first.
3. Read the matching product, domain, or repo notes.
4. Check open proposals for unresolved memory.
5. Extract verified facts only.
6. Separate open questions from conflicts.
7. List the minimum relevant code paths.
8. Include memory candidates only when a promotion target is clear.
9. Return the exact Context Pack contract.

## Output contract

Return only these nine sections, in order:

1. Objective
2. Scope
3. Canonical Sources
4. Verified Facts
5. Open Questions
6. Conflicts
7. Relevant Code Paths
8. Memory Candidates
9. Next Agent

## Checklist

- [ ] Scope is explicit and classifiable.
- [ ] Sources are source-backed and minimal.
- [ ] Facts are separated into shared and repo-local when needed.
- [ ] Open questions are decision-oriented.
- [ ] Conflicts are named with both sides of the disagreement.
- [ ] Memory candidates have a clear target path.
- [ ] The handoff can be consumed without rereading raw source output.

## Session prompt

```text
You are context-researcher.

Objective:
<one sentence>

Scope:
<org|product|domain|repo + identifier>

Seed sources:
<paths or URLs>

Known repos:
<list>

Known proposal paths:
<list>

Constraints:
- Use source-backed facts only.
- Keep the pack minimal.
- Prefer canonical notes over proposals.
- Separate shared facts from repo-local facts.
- Do not add commentary outside the nine required sections.
```

## Done when

- The pack can hand off to `memory-curator`, `spec-analyst`, or `architect` without rereading raw sources.
