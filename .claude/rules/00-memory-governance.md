# Memory governance

- Canonical knowledge lives in `knowledge/`.
- Draft knowledge lives in `knowledge/_proposals/`.
- A durable fact must always include source links, scope, and review status.
- If a fact is uncertain, label it as a hypothesis or open question.
- If two facts conflict, record the conflict and the source of each side.
- Do not overwrite a canonical note unless the new note explicitly supersedes it.
- Prefer append-only history for incidents, ADRs, and decisions.
- Use proposals as the bridge between a live conversation and durable memory.

Required metadata for durable notes:

- `id`
- `type`
- `scope`
- `source`
- `status`
- `owner`
- `reviewed_at`
- `supersedes`
- `confidence`
