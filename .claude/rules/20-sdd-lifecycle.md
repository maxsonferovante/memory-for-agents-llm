---
paths:
  - "knowledge/specs/**/*.md"
  - "knowledge/adr/**/*.md"
  - "knowledge/incidents/**/*.md"
  - "knowledge/runbooks/**/*.md"
---

# SDD lifecycle

- Start with the problem statement and the repo or domain scope.
- Turn demand into a spec before implementation starts.
- If the spec implies an architectural choice, create an ADR candidate.
- If the work touches operational behavior, add or update a runbook.
- If the work came from an incident, capture the incident timeline before the fix.
- Implementation should reference the spec and the decisions it depends on.
- Review should check correctness, consistency, and whether the durable knowledge was updated.
