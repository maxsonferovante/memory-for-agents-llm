---
id: knowledge-scope-model-v1
type: canonical
scope: org
status: active
owner: cross-repo-coordinator
source:
  - knowledge/_proposals/2026-06-09-memory-foundation/02-knowledge-scope-model.md
  - .claude/rules/10-cross-repo-context.md
supersedes: null
---

# Knowledge scope model

## Scope levels

| Scope | Meaning | Typical content |
| --- | --- | --- |
| `org` | Applies to the whole organization | policies, global invariants, promotion rules |
| `product` | Applies to all repos in one product | shared product behavior, common contracts |
| `domain` | Applies to one business domain | rules, events, glossary terms, workflows |
| `repo` | Applies to one repository only | local conventions, implementation notes, repo-specific variants |

## Placement rules

- Shared invariants belong in the highest scope that truly owns them.
- Repo-local exceptions belong in `knowledge/repos/`.
- If the same rule appears in more than one repo, evaluate whether it should be promoted to `product` or `org`.
- Do not duplicate a shared rule silently when a local delta is enough.
- If a note cannot be classified yet, keep it in `knowledge/_proposals/` until the owner resolves it.

## Cross-scope behavior

- Shared knowledge should be linked, not copied.
- Local variants should point back to the shared canonical note.
- Cross-repo coordination is a metadata and ownership problem, not an oral-history problem.
