# Context Pack

1. Objective
   Prepare the first product and repo sharing docs for the memory architecture repo and capture the promotion path in a reusable format.

2. Scope
   product: claude-code-memory-platform

3. Canonical Sources
   - [knowledge/org/context-pack-contract.md](../../../knowledge/org/context-pack-contract.md) - defines the required nine-part output order.
   - [knowledge/org/memory-curation-flow.md](../../../knowledge/org/memory-curation-flow.md) - defines the promotion checklist and acceptance criteria.
   - [knowledge/org/knowledge-scope-model.md](../../../knowledge/org/knowledge-scope-model.md) - defines org, product, domain, and repo scope boundaries.
   - [.claude/agents/context-researcher.md](../../../.claude/agents/context-researcher.md) - defines the required context pack return format.
   - [.claude/agents/memory-curator.md](../../../.claude/agents/memory-curator.md) - defines the promotion flow and pass/fail reporting.
   - [knowledge/products/README.md](../../../knowledge/products/README.md) - shows the product bucket is the shared home for product-level knowledge.
   - [knowledge/repos/README.md](../../../knowledge/repos/README.md) - shows the repo bucket is the home for repo-local knowledge.

4. Verified Facts
   - Canonical org notes already define memory governance, scope classification, the context pack contract, the agent cycle, the curation flow, and cross-repo sharing. Sources: [knowledge/org/README.md](../../../knowledge/org/README.md), [knowledge/org/knowledge-scope-model.md](../../../knowledge/org/knowledge-scope-model.md), [knowledge/org/context-pack-contract.md](../../../knowledge/org/context-pack-contract.md), [knowledge/org/agent-memory-cycle.md](../../../knowledge/org/agent-memory-cycle.md), [knowledge/org/memory-curation-flow.md](../../../knowledge/org/memory-curation-flow.md), [knowledge/org/cross-repo-sharing-policy.md](../../../knowledge/org/cross-repo-sharing-policy.md).
   - `context-researcher` must return Objective, Scope, Canonical Sources, Verified Facts, Open Questions, Conflicts, Relevant Code Paths, Memory Candidates, and Next Agent in that order. Source: [.claude/agents/context-researcher.md](../../../.claude/agents/context-researcher.md).
   - `memory-curator` must evaluate a checklist and acceptance criteria before promoting a note into canonical knowledge. Source: [.claude/agents/memory-curator.md](../../../.claude/agents/memory-curator.md), [knowledge/org/memory-curation-flow.md](../../../knowledge/org/memory-curation-flow.md).
   - The repository already separates canonical org docs, product docs, repo docs, and proposals into distinct directories. Sources: [knowledge/org/README.md](../../../knowledge/org/README.md), [knowledge/products/README.md](../../../knowledge/products/README.md), [knowledge/repos/README.md](../../../knowledge/repos/README.md), [knowledge/_proposals/README.md](../../../knowledge/_proposals/README.md).
   - `knowledge/_proposals/` is the staging area for draft memory updates before promotion. Source: [knowledge/_proposals/README.md](../../../knowledge/_proposals/README.md).

5. Open Questions
   - Which additional repos will later consume the `claude-code-memory-platform` product contract?
   - Should the first repo-local note stay limited to local memory conventions, or also include repo-specific operational guidelines?

6. Conflicts
   None

7. Relevant Code Paths
   - `knowledge/org/*.md` - canonical org-level governance and contracts.
   - `knowledge/products/README.md` - product-level index for shared rules.
   - `knowledge/repos/README.md` - repo-level index for local deltas.
   - `.claude/agents/context-researcher.md` - source pack contract for research output.
   - `.claude/agents/memory-curator.md` - curation contract for promotion.
   - `knowledge/_proposals/2026-06-09-memory-foundation/` - draft bundle being promoted.

8. Memory Candidates
   - `knowledge/products/claude-code-memory-platform/shared-memory-contract.md` - define the product-wide shared memory contract and ownership rules.
   - `knowledge/repos/memory-for-agents-llm/repo-local-memory-overrides.md` - define the repo-local memory conventions and local path rules.

9. Next Agent
   memory-curator
