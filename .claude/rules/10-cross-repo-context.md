---
paths:
  - "knowledge/repos/**/*.md"
  - "knowledge/products/**/*.md"
  - "knowledge/domains/**/*.md"
---

# Cross-repo context

- Classify every fact as `org`, `product`, `domain`, or `repo`.
- Shared behavior belongs in `org` or `product`.
- Domain rules that apply to one business capability belong in `domain`.
- Implementation detail that changes per codebase belongs in `repo`.
- When the same concept appears in multiple repos, store the shared invariant once and record the repo-specific variation separately.
- When a repo imports a shared rule, link back to the canonical note instead of copying it silently.
- If you cannot decide the scope, keep the fact in `knowledge/_proposals/` until the owner resolves it.
