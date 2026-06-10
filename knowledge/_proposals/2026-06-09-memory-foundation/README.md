# Memory foundation package

This package is the first proposal bundle for the memory system.
The canonical versions have been promoted into `knowledge/org/`.

It defines the minimum durable contract for:

- how knowledge becomes canonical
- how scope is classified across org, product, domain, and repo
- how a context pack is formed
- how agents hand off memory between sessions
- how hooks and proposals enforce the lifecycle

## Bundle order

1. Memory governance
2. Knowledge scope model
3. Context pack contract
4. Agent memory cycle
5. Cross-repo sharing policy

## Worked example

- [06-context-pack-example.md](./06-context-pack-example.md) - concrete Context Pack that uses the promoted contracts and feeds the promotion flow.

## Promotion intent

- Approved notes should be promoted into `knowledge/org/` first when they are global.
- Product-wide variants go into `knowledge/products/`.
- Repo-local exceptions go into `knowledge/repos/`.
- Any note that changes architecture should also spawn or update an ADR in `knowledge/adr/`.

## Review rule

- A reviewer should be able to evaluate each file independently in one pass.
- The package is valid only when every file has sources, scope, target path, and a clear supersession rule.
