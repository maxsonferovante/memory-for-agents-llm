---
id: prop-codex-installer-toml-serialization-v1
type: canonical
scope: repo
status: active
owner: memory-curator
supersedes: null
confidence: high
reviewed_at: 2026-06-12
---


# Codex installer TOML serialization candidate

## Problem

The repo-local Codex installer writes `~/.codex/config.toml` through a hand-rolled TOML emitter. Bare key output is valid only for a restricted character set, so path keys, dotted version names, and plugin or hook identifiers can be serialized into invalid or mis-typed TOML.

## Proposal

Define a repo-local serialization invariant for `scripts/install_codex_assets.py`.

### Required key handling

- Emit bare keys only when the key matches the TOML bare-key character set used by the repo serializer.
- Quote any key that contains path separators, dots that must remain literal, spaces, `@`, `:`, or other non-bare characters.
- Apply the same quoting rule to scalar keys and dotted table path segments.

### Known failure classes

- File paths used as literal keys must be emitted like `"/Users/path/to/project" = "vscode"`.
- Dotted table headers that include literal paths must be emitted like `[projects."/Users/mferovante/Documents/memory for agents llm"]`.
- Version-like keys must be emitted like `"gpt-5.2" = "gpt-5.5"` so they remain string keys instead of nested tables.
- Plugin and hook-state identifiers must be emitted like `[plugins."browser@openai-bundled"]` and `[hooks.state."mcpmarket-my-toolkit@...:session_start:0:0"]`.

### Validation rule

- Any serializer change must be validated with a round-trip parse that confirms the generated TOML decodes back to the original nested data structure.

## Consequences

- The installer can safely merge into richer Codex configs without corrupting path-based preferences or version-migration tables.
- Repo maintainers have an explicit rule for when manual TOML emission is still acceptable.
- Future installer changes have a concrete regression target instead of relying on ad hoc examples.

## Sources

- [scripts/install_codex_assets.py](../../../scripts/install_codex_assets.py)
- [README.md](../../../README.md)
- [CODEX.md](../../../CODEX.md)
- [QUICKSTART.md](../../../QUICKSTART.md)

## Acceptance criteria

- The proposal states when keys must be quoted.
- It covers path keys, dotted table paths, version-like keys, and plugin or hook identifiers.
- It requires a parse-based validation step rather than string inspection alone.
