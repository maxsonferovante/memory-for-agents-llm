---
id: spec-memory-platform-component-review-v1
type: canonical
scope: product
status: active
owner: spec-memory-platform
supersedes: null
confidence: high
reviewed_at: 2026-06-15
---

# Current component review

## Review principle

Prioritize simplicity. Remove, merge, or demote components that do not clearly support Spec Kit artifacts, event capture, memory processing, knowledge projection, MCP retrieval, or runtime adaptation.

## Component decisions

| Component | Problem solved today | Still needed? | Replacement or simplification |
| --- | --- | --- | --- |
| `knowledge/` | Durable knowledge by scope. | Yes. | Keep as Knowledge Base projection derived from events and curation. |
| `knowledge/_proposals/` | Draft updates before canonical promotion. | Yes. | Keep as candidate-memory review workflow. |
| `knowledge/specs/` | SDD specs and historical specs. | Yes. | Make it the primary feature-memory anchor. |
| `knowledge/adr/` | Architecture decisions. | Yes. | Keep and link ADRs to `architecture.decision.created` events. |
| `hooks/` | Enforcement, ingestion, and promotion. | Yes, narrowed. | Use only for event capture, mandatory validation, memory updates, and summaries. |
| `local_stack/` | Local API, worker, and MCP stack. | Yes. | Evolve into Event Store, Memory Store, Processing, and MCP reference implementation. |
| `.agents/skills/` | Codex reusable workflows. | Yes, narrowed. | Use for decision classification, ADR generation, implementation summaries, memory consolidation, and context retrieval. |
| `.claude/skills/` | Claude reusable workflows. | Conditional. | Keep as Claude packaging for shared skill responsibilities. |
| `.claude/agents/` | Specialized Claude subagents. | Not by default. | Archive or keep only with documented ROI and no simpler alternative. |
| `.codex/agents/` | Specialized Codex subagents. | Not by default. | Treat as optional runtime UX; avoid platform dependency. |
| `CLAUDE.md` | Claude operating rules. | Adapter only. | Keep minimal setup and MCP instructions; no canonical memory. |
| `CODEX.md` and `.codex/config.toml` | Codex operating config. | Adapter only. | Keep operational settings and MCP discovery. |
| `.github/workflows/` | Automation for PRs, images, checks. | Yes. | Add event-producing workflows for PR, commit, CI, and release evidence. |
| Installer scripts | Copy runtime assets. | Transitional. | Keep until adapters and MCP discovery are stable. |
| Session templates | Repeatable prompts. | Conditional. | Replace durable guidance with Spec Kit artifact templates. |

## Agents policy

Start from zero custom agents. A proposed agent must document:

- Problem solved.
- Reason a hook, skill, workflow, document, or MCP tool is insufficient.
- Operational cost.
- Runtime portability risk.
- Simpler alternative considered.

## Hooks policy

Hooks are preferable to agents only for:

- Event capture.
- Mandatory validation.
- Memory update requests.
- Summary generation.

Hooks must not contain product business logic.

## Skills policy

Skills are appropriate for bounded cognitive workflows:

- Decision classification.
- ADR generation.
- Implementation summary generation.
- Memory consolidation.
- Context retrieval and context-pack assembly.

Skills must produce artifacts or events; they must not become durable memory stores.
