---
id: claude-code-memory-platform-shared-memory-contract-v1
type: canonical
scope: product
status: active
owner: cross-repo-coordinator
source:
  - ../../../knowledge/org/context-pack-contract.md
  - ../../../knowledge/org/memory-curation-flow.md
  - ../../../knowledge/org/knowledge-scope-model.md
  - ../../../knowledge/_proposals/2026-06-09-memory-foundation/06-context-pack-example.md
supersedes: null
---

# Shared memory contract

## Product scope

This product keeps one shared contract for memory-aware Claude Code workflows across its repos.

## Shared invariants

- The org-level `Context Pack` contract is the required output format for `context-researcher`.
- The org-level curation flow is the required promotion path for durable memory.
- Shared facts must live in the highest applicable scope and be linked, not duplicated.
- A product note may specialize the org contract, but it must not weaken it.

## Product responsibilities

- Define the shared behavior that every repo in this product must follow.
- Record product-wide deltas only once.
- Route repo-local exceptions into `knowledge/repos/`.
- Keep the canonical home explicit when more than one repo uses the same rule.

## Example consumption pattern

- A repo reads this note to learn the shared memory contract.
- The repo then adds its local delta under `knowledge/repos/<repo>/`.
- The repo-local note links back to this product note instead of copying it.
