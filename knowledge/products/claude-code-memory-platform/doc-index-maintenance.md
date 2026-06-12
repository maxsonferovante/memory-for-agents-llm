---
id: prop-claude-product-doc-index-maintenance-v1
type: canonical
scope: product
status: active
owner: cross-repo-coordinator
source:
  - knowledge/products/claude-code-memory-platform/README.md
  - knowledge/products/claude-code-memory-platform/claude-project-mcp-registration.md
supersedes: null
confidence: high
reviewed_at: 2026-06-12
---


# Product doc index maintenance

## Problem

The product README is the main navigation surface for this documentation area. When a new canonical note is promoted but the product index is not updated in the same maintenance flow, the note exists on disk but remains easy to miss for future readers.

## Proposal

Treat product-index maintenance as a first-class documentation rule.

### Required behavior

- When a new canonical note is promoted under `knowledge/products/claude-code-memory-platform/`, the product index should be reviewed in the same maintenance pass.
- The product index should list the new note when that note is part of the stable documentation surface.
- Navigation updates should be treated as documentation maintenance, not as optional cleanup.

## Consequences

- Canonical notes become easier to discover from the product landing page.
- Product documentation stays coherent as the number of canonical notes grows.
- Memory curation work leaves behind both the note itself and a maintainable navigation path.

## Sources

- [knowledge/products/claude-code-memory-platform/README.md](../../../knowledge/products/claude-code-memory-platform/README.md)
- [knowledge/products/claude-code-memory-platform/claude-project-mcp-registration.md](../../../knowledge/products/claude-code-memory-platform/claude-project-mcp-registration.md)

## Acceptance criteria

- The note states that new canonical product notes require an index review.
- The note treats index maintenance as part of the same documentation maintenance flow.
- The note is scoped to the product documentation surface.
