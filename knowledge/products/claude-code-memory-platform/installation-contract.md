---
id: claude-code-memory-platform-installation-contract-v1
type: canonical
scope: product
status: active
owner: cross-repo-coordinator
source:
  - ../../../scripts/install_claude_assets.py
  - ../../../QUICKSTART.md
  - ../../../README.md
  - ../../../hooks/README.md
  - ../../../knowledge/README.md
  - ../../../knowledge/_proposals/2026-06-10-distribution-installation/02-installation-contract.md
supersedes: null
---

# Installation contract

## Product scope

The install flow is deterministic, dry-run-first, and safe for third-party use.

## Supported install flow

1. Download or clone a versioned release artifact.
2. Inspect the artifact contents and the version.
3. Run the installer in dry-run mode.
4. Review the destination paths and any overwrite warnings.
5. Run the real installer only after the dry-run matches expectations.
6. Verify the local Claude config and the hook wiring.

## Supported locations

- Default target is `~/.claude`.
- An explicit `CLAUDE_CONFIG_DIR` overrides the default.
- The installer must not write outside the Claude config target except where the repo itself is the working directory.

## Trust boundary

- The installer may copy the approved runtime assets.
- The installer may wire hooks and settings.
- The installer must not invent new agent logic.
- The installer must not overwrite user files silently.
- The installer must never be the only source of truth for canonical memory.

## Verification steps

- Run the installer with `--dry-run`.
- Confirm the reported target paths.
- Run the installer without `--dry-run`.
- Confirm that the expected files exist in the Claude config directory.
- Confirm that the hook wiring points to the packaged runner.
- Confirm that the installed assets still reference the repo or release version that produced them.

## Fallback behavior

- If the local config already has matching files, the installer should report them as unchanged.
- If a file differs and `--force` is not provided, the installer should skip the overwrite.
- If `--force` is provided, the installer may back up the existing file before replacing it.

## Consequences

- Installation becomes repeatable for a non-author of the repo.
- The user can validate the install before committing to changes locally.
- The flow remains safe enough for public distribution because the installer is explicit about path, overwrite, and verification behavior.
