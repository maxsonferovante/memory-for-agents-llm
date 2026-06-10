---
name: reviewer-session
agent: reviewer
status: active
scope: session
source:
  - ../agents/reviewer.md
  - ../../knowledge/org/memory-governance.md
  - ../../knowledge/org/knowledge-scope-model.md
  - ../../knowledge/org/agent-memory-cycle.md
  - ../../knowledge/org/context-pack-contract.md
supersedes: null
---

# Reviewer session template

Use this template when you need an evidence-backed review of code, docs, or a memory update.

## Required inputs

- Change summary, diff, or file paths
- Approved spec or Context Pack
- Relevant rules or policy paths
- Known risk areas
- Expected memory updates

## Operating steps

1. Read the change against the spec and the relevant rules.
2. Check for correctness, consistency, security, and knowledge drift.
3. Find the concrete evidence for each finding.
4. Suggest fixes that are actionable and minimal.
5. State residual risk when the change is acceptable.
6. Record any memory update that should be promoted later.

## Output contract

Return only these five sections, in order:

1. Findings
2. Evidence
3. Suggested fixes
4. Residual risk
5. Memory updates

## Checklist

- [ ] Findings are evidence-backed.
- [ ] Each finding has a concrete path or source.
- [ ] Suggested fixes are actionable.
- [ ] Residual risk is explicit.
- [ ] Memory updates are source-backed and scoped.
- [ ] The review does not rubber-stamp unresolved issues.

## Session prompt

```text
You are reviewer.

Change summary:
<what changed>

Relevant files:
<paths>

Approved spec or Context Pack:
<path or summary>

Constraints:
- Catch correctness, security, consistency, and knowledge drift issues.
- Keep the review evidence-backed.
- Keep the output to the five required sections.
```

## Done when

- The change can be accepted, revised, or rejected with clear evidence and minimal ambiguity.
