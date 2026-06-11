---
id: claude-code-memory-platform-release-checklist-v1
type: canonical
scope: product
status: active
owner: cross-repo-coordinator
source:
  - ../../../README.md
  - ../../../QUICKSTART.md
  - ../../../scripts/install_claude_assets.py
  - ../../../knowledge/products/claude-code-memory-platform/distribution-plan.md
  - ../../../knowledge/products/claude-code-memory-platform/installation-contract.md
supersedes: null
---

# Release checklist

## Purpose

Use this checklist before publishing a versioned package so a third party can install it without guessing.

## Checklist

- [ ] The release points to a commit or tag.
- [ ] The packaged assets are limited to the supported runtime surface.
- [ ] `README.md` and `QUICKSTART.md` describe the distribution and install flow.
- [ ] The installer supports `--dry-run`.
- [ ] The installer reports the target directory and overwrite behavior.
- [ ] `CLAUDE_CONFIG_DIR` is documented as the override path.
- [ ] The packaged hooks and settings point to the right runner.
- [ ] The package version is visible in the artifact or release notes.
- [ ] A non-author can complete the install from the docs alone.
- [ ] The backend deployment tutorial shows Terraform init, plan, and apply.
- [ ] The backend deployment tutorial shows the one-step release script and the generated `backend.env` file.
- [ ] The backend tutorial documents the required AWS profile and region inputs.
- [ ] The backend tutorial documents the API key and rate limit inputs.
- [ ] The backend tutorial includes the read-path and write-path smoke tests.
- [ ] The backend release bundle exposes the API endpoint and storage outputs.

## Release rule

- Do not publish a package that requires hidden tribal knowledge to install.
- Do not publish a package whose files differ from the documented install surface.
- Do not publish a package until the dry-run and real install paths both work on a clean machine.
