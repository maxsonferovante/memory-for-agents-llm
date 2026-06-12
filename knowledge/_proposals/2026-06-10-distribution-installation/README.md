# Distribution and installation package

This package defines how the Claude Code memory system is packaged, verified, installed, and distributed to third parties before the local stack exists.

## Bundle order

1. Distribution plan
2. Installation contract

## Promotion intent

- Promote the distribution plan into `knowledge/products/claude-code-memory-platform/`.
- Promote the installation contract into `knowledge/products/claude-code-memory-platform/`.
- Keep the repository reference implementation aligned with the product contract, but do not make the repo itself the distribution mechanism.

## Review rule

- A reviewer should be able to evaluate each file independently in one pass.
- The package is valid only when it states the packaging unit, verification flow, supported install paths, trust boundary, versioning rule, and fallback behavior.
