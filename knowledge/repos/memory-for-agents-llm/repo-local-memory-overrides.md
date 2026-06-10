---
id: memory-for-agents-llm-repo-local-memory-overrides-v1
type: canonical
scope: repo
status: active
owner: coordinator
source:
  - ../../../knowledge/products/claude-code-memory-platform/shared-memory-contract.md
  - ../../../knowledge/org/knowledge-scope-model.md
  - ../../../knowledge/org/memory-curation-flow.md
  - ../../../knowledge/_proposals/2026-06-09-memory-foundation/06-context-pack-example.md
supersedes: null
---

# Repo-local memory overrides

## Repo identity

This repository is the reference implementation repo for the memory architecture work.

## Local conventions

- `.claude/agents/` holds the subagent definitions for this repo.
- `.claude/skills/` holds the reusable workflows that the repo uses as skills.
- `knowledge/org/` holds org-wide canonical memory contracts.
- `knowledge/products/claude-code-memory-platform/` holds the shared product-level memory contract.
- `knowledge/_proposals/2026-06-09-memory-foundation/` holds the staged drafts and the example context pack.

## Repo-local delta

- This repo currently focuses on documentation and contract scaffolding rather than executable application code.
- The repo-local notes should stay narrow and should not duplicate the product contract.
- If a future implementation adds code paths or runtime helpers, those should be captured here as local notes and linked back to the product contract.

## Consumption pattern

- Read the product note first.
- Read this repo note second.
- Use the pair to decide whether a new fact belongs in org, product, or repo scope.
