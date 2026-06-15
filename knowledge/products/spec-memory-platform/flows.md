---
id: spec-memory-platform-flows-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---

# Spec Memory Platform flows

## Official feature flow

Every feature starts and ends in the GitHub Spec Kit lifecycle:

1. `/speckit.constitution` records non-negotiable principles, quality bars, and governance.
2. `/speckit.specify` creates the user-visible specification and requirements.
3. `/speckit.clarify` records questions, answers, assumptions, and scope decisions.
4. `/speckit.checklist` verifies specification readiness.
5. `/speckit.plan` defines implementation strategy, architecture impact, and dependencies.
6. `/speckit.tasks` decomposes the plan into executable work.
7. `/speckit.analyze` checks consistency, risk, security, and drift.
8. `/speckit.implement` executes tasks and records completion evidence.

## Event capture flow

| Step | Producer | Event examples | Output |
| --- | --- | --- | --- |
| Artifact authored | Runtime or human | `spec.created`, `plan.created` | Stored event with artifact version. |
| Artifact updated | Runtime, human, PR | `spec.updated`, `requirement.updated` | Changed sections and provenance. |
| Validation runs | Hook or CI | `analysis.completed`, `inconsistency.detected` | Check evidence and failures. |
| Implementation starts | Runtime or task runner | `implementation.started`, `task.completed` | Task linkage and command evidence. |
| Review completes | PR or review agent | `review.completed` | Findings, approvals, and required fixes. |
| Learning emerges | Retrospective or curator | `lesson.learned`, `improvement.suggested` | Candidate memory. |

## Memory consolidation flow

1. Session Memory captures short-lived context during one run.
2. Feature Memory aggregates events by Spec Kit feature and spec ID.
3. Repository Memory is proposed when a fact affects future work in one repository.
4. Product Memory is proposed when the fact applies across repositories in one product.
5. Organizational Memory is proposed when the fact becomes a cross-product invariant.
6. Deprecated memory remains retrievable with replacement guidance.

## Retrieval flow

1. Runtime asks MCP for context by task, spec, repo, product, or question.
2. MCP resolves scope and calls Context Retrieval API.
3. Retrieval selects active memory, related ADRs, relevant events, and artifact snippets.
4. MCP returns a compact context pack with citations, confidence, and known gaps.
5. Runtime uses the context but does not persist memory directly.

## Feedback flow

1. Implementation and review outcomes emit events.
2. Processing detects repeated patterns, inconsistencies, or durable lessons.
3. A memory candidate is created with provenance.
4. Curators approve, reject, narrow, or deprecate memory.
5. New memory becomes available through MCP.
