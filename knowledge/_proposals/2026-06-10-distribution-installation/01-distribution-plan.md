---
id: prop-distribution-plan-v1
type: proposal
scope: product
status: promoted
owner: cross-repo-coordinator
target_path: knowledge/products/claude-code-memory-platform/distribution-plan.md
supersedes: null
confidence: high
---

# Distribution plan v1

## Problem

The memory system is useful only if another Claude Code user can obtain the same agents, hooks, docs, and validation flow without manually reconstructing the repo design.

## Proposal

Ship the system as a versioned source package with a deterministic installer.

- The canonical source remains this repository.
- The distributable unit is the repo content plus a packaging manifest.
- The installer copies only the supported runtime assets into the local Claude config directory.
- The package must be reproducible from Git and the package manifest.
- Distribution can be public or semi-public, but the install contract must not depend on private repo internals.

## Distribution model

### Source of truth

- Git remains the canonical source of the assets.
- A release artifact is a signed or version-tagged snapshot of the repo content.
- The release artifact exists to make installation repeatable, not to become a new source of truth.

### Packaging unit

- `CLAUDE.md`
- `.claude/agents/`
- `.claude/skills/`
- `.claude/templates/`
- `.claude/rules/`
- `hooks/`
- `scripts/install_claude_assets.py`
- `knowledge/` only when the user wants the full memory reference package

### Versioning rule

- Every distributable package must declare a semantic or date-based version.
- The version must map to a commit or release tag.
- The installer must report the version it installed.

### Distribution channels

- Git clone for developers who want the reference repo.
- Release archive for users who want a single download.
- Optional package registry or release page for semi-public distribution.

## Consequences

- Any person can install the system from a stable artifact instead of hand-copying files.
- The repo remains the canonical source, so updates stay reviewable.
- The release process becomes a separate concern from the memory backend.

## Sources

- [README.md](../../../README.md)
- [QUICKSTART.md](../../../QUICKSTART.md)
- [scripts/install_claude_assets.py](../../../scripts/install_claude_assets.py)
- [knowledge/README.md](../../../knowledge/README.md)
- [knowledge/org/memory-governance.md](../../../knowledge/org/memory-governance.md)
- [knowledge/_proposals/2026-06-10-central-memory-backend/README.md](../2026-06-10-central-memory-backend/README.md)

## Acceptance criteria

- A third party can obtain a versioned artifact without reading the whole repo.
- The artifact maps to a specific commit or release tag.
- The artifact contains only the supported install surface.
- The distribution channel is explicit and does not require guessing.
- The install flow can be repeated with the same inputs and produce the same local layout.
