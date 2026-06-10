---
id: context-pack-contract-v1
type: canonical
scope: org
status: active
owner: context-researcher
source:
  - knowledge/_proposals/2026-06-09-memory-foundation/03-context-pack-contract.md
  - .claude/agents/context-researcher.md
supersedes: null
---

# Context Pack contract

`context-researcher` must return context in this exact order.

## Required format

```text
Context Pack
1. Objective
2. Scope
3. Canonical Sources
4. Verified Facts
5. Open Questions
6. Conflicts
7. Relevant Code Paths
8. Memory Candidates
9. Next Agent
```

## Field rules

### Objective

- One short sentence describing the task outcome the pack supports.

### Scope

- Must state `org`, `product`, `domain`, or `repo`.
- Include the repo name when the scope is repo-local.

### Canonical Sources

- List only source-backed references.
- Prefer canonical docs over proposals.
- Each bullet must include a path or URL and one reason it matters.

### Verified Facts

- Each bullet must be a factual statement.
- Every fact must cite at least one source.
- If a fact is uncertain, move it to `Open Questions`.

### Open Questions

- Use this section for anything not yet source-backed.
- Keep questions short and decision-oriented.

### Conflicts

- Show source A versus source B when two sources disagree.
- If there is no conflict, write `None`.

### Relevant Code Paths

- List the files or modules that matter for the task.
- Include a short reason for each path.

### Memory Candidates

- Each item must identify a target canonical path.
- Include the proposed note in one sentence.
- If no durable memory should be written, write `None`.

### Next Agent

- Name the next agent that should handle the result.
- If no handoff is needed, write `None`.

## Output constraints

- Keep the pack minimal.
- Do not add prose outside the required sections.
- Prefer source links over paraphrase.
- Separate shared facts from repo-local facts when they differ.
