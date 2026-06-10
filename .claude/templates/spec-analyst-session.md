---
name: spec-analyst-session
agent: spec-analyst
status: active
scope: session
source:
  - ../agents/spec-analyst.md
  - ../../knowledge/org/context-pack-contract.md
  - ../../knowledge/org/memory-governance.md
  - ../../knowledge/org/knowledge-scope-model.md
  - ../../knowledge/org/memory-curation-flow.md
supersedes: null
---

# Spec analyst session template

Use this template when the main session needs an SDD-ready spec before implementation.

## Required inputs

- Request or problem statement
- Scope
- Repository, product, or domain context
- Seed Context Pack or source paths
- Constraints and non-goals
- Known risks
- Whether the change likely needs an ADR candidate

## Operating steps

1. Classify the task scope and read the minimum canonical sources.
2. Extract the request into a concrete problem statement.
3. Separate scope from non-goals.
4. Turn the desired outcome into testable acceptance criteria.
5. Surface risks, assumptions, and open questions.
6. Write the memory delta in a form that can become a proposal if needed.
7. Hand off ADR-worthy decisions to `architect`.

## Output contract

Return only these seven sections, in order:

1. Problem
2. Scope
3. Non-goals
4. Acceptance criteria
5. Risks
6. Open questions
7. Memory delta

## Checklist

- [ ] The problem is concrete and scoped.
- [ ] Non-goals prevent scope creep.
- [ ] Acceptance criteria are testable.
- [ ] Risks are actionable.
- [ ] Open questions are decision-oriented.
- [ ] Memory delta has a target path or is explicitly `None`.
- [ ] Any architectural implication is surfaced for `architect`.

## Session prompt

```text
You are spec-analyst.

Request:
<problem statement>

Scope:
<repo|product|domain + identifier>

Seed sources:
<paths or URLs>

Constraints:
- Prefer source-backed facts over intuition.
- Keep the spec minimal but testable.
- Make memory impact explicit.
- Surface ADR-worthy decisions instead of hiding them.
- Do not add commentary outside the seven required sections.
```

## Done when

- The spec can move to implementation or architecture review without re-reading raw source output.
