# Session templates

These templates are the copy-paste operational layer for common Claude Code sessions in this repo.

Use them when you want the agent behavior as a concrete prompt rather than as a background subagent.

## Templates

- [context-researcher-session.md](./context-researcher-session.md) - source-backed research handoff template.
- [spec-analyst-session.md](./spec-analyst-session.md) - SDD-ready spec drafting template.
- [architect-session.md](./architect-session.md) - architecture review and ADR candidate template.
- [reviewer-session.md](./reviewer-session.md) - evidence-backed review template.
- [memory-curator-session.md](./memory-curator-session.md) - durable memory promotion template.

## Rule

- Keep these templates aligned with the canonical contracts in `knowledge/org/`.
- Update the template first when the session shape changes, then update the agent definition to match.
