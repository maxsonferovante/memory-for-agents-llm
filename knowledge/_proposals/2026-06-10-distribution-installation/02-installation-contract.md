---
id: prop-installation-contract-v1
type: proposal
scope: product
status: promoted
owner: cross-repo-coordinator
target_path: knowledge/products/claude-code-memory-platform/installation-contract.md
supersedes: null
confidence: high
---

# Installation contract v1

## Problem

A third party needs a clear, low-risk path to install the memory system into Claude Code without guessing where files go, what can be overwritten, or how to validate the result.

## Proposal

Define the install contract as a deterministic, dry-run-first bootstrap.

### Supported install flow

1. Download or clone a versioned release artifact.
2. Inspect the artifact contents and the version.
3. Run the installer in dry-run mode.
4. Review the destination paths and any overwrite warnings.
5. Run the real installer only after the dry-run matches expectations.
6. Verify the local Claude config and the hook wiring.

### Supported locations

- Default target is `~/.claude`.
- An explicit `CLAUDE_CONFIG_DIR` overrides the default.
- The installer must not write outside the Claude config target except where the repo itself is the working directory.

### Trust boundary

- The installer may copy the approved runtime assets.
- The installer may wire hooks and settings.
- The installer must not invent new agent logic.
- The installer must not overwrite user files silently.
- The installer must never be the only source of truth for canonical memory.

### Verification steps

- Run the installer with `--dry-run`.
- Confirm the reported target paths.
- Run the installer without `--dry-run`.
- Confirm that the expected files exist in the Claude config directory.
- Confirm that the hook wiring points to the packaged runner.
- Confirm that the installed assets still reference the repo or release version that produced them.

### Fallback behavior

- If the local config already has matching files, the installer should report them as unchanged.
- If a file differs and `--force` is not provided, the installer should skip the overwrite.
- If `--force` is provided, the installer may back up the existing file before replacing it.

## Consequences

- Installation becomes repeatable for a non-author of the repo.
- The user can validate the install before committing to changes locally.
- The flow remains safe enough for public distribution because the installer is explicit about path, overwrite, and verification behavior.

## Sources

- [scripts/install_claude_assets.py](../../../scripts/install_claude_assets.py)
- [QUICKSTART.md](../../../QUICKSTART.md)
- [README.md](../../../README.md)
- [hooks/README.md](../../../hooks/README.md)
- [knowledge/README.md](../../../knowledge/README.md)

## Acceptance criteria

- The installer has a documented dry-run-first path.
- The install target is explicit.
- Overwrites are opt-in.
- The local verification steps are documented.
- The install contract is usable by someone who did not author the repo.
