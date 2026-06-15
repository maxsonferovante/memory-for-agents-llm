---
id: spec-memory-platform-memory-taxonomy-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---

# Memory taxonomy

## Scope hierarchy

| Scope | Lifetime | Content | Promotion trigger |
| --- | --- | --- | --- |
| Session Memory | Hours or one agent run | Temporary assumptions, commands, active blockers, unresolved questions. | Summarize into Feature Memory when relevant after session end. |
| Feature Memory | Feature lifetime plus maintenance | Requirements, clarifications, plan decisions, tasks, analysis, implementation evidence, review outcomes. | Promote when future work in the same repo needs it. |
| Repository Memory | Repository lifetime | Build conventions, architecture constraints, repo-local exceptions, operational commands. | Promote when multiple repos in a product share it. |
| Product Memory | Product lifetime | Shared architecture, dependency rules, domain behavior, release policy, quality bars. | Promote when cross-product invariant emerges. |
| Organizational Memory | Long-lived | Engineering principles, security constraints, governance, naming, compliance, memory policy. | Rare; requires owner approval. |

## Memory item fields

Each memory item should carry:

- Stable ID.
- Scope and owner.
- Status: `candidate`, `active`, `deprecated`, or `rejected`.
- Summary and detailed body.
- Source events and artifact references.
- Confidence and review timestamp.
- Supersedes and superseded-by links.
- Retrieval tags for spec, repo, product, domain, dependency, and decision.

## Promotion rules

- Promote upward only when the fact is stable beyond the current scope.
- Keep exceptions at the lowest scope that explains them.
- Never silently duplicate higher-scope memory into lower-scope notes.
- Deprecate memory instead of deleting it when a runtime may still retrieve it.
- Require provenance for every active memory item.

## Knowledge Graph edges

The graph should derive edges such as:

- spec `defines` requirement
- requirement `clarified_by` clarification
- plan `selects` dependency
- task `implements` requirement
- ADR `decides` architecture concern
- review `validates` implementation
- lesson `updates` memory
- memory `supersedes` memory
