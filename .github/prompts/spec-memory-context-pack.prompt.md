---
description: Build a Spec Memory context pack for Copilot work
---

# Spec Memory context pack

Use this prompt before implementing or reviewing a Spec Memory Platform change.

1. Identify the active Spec Kit artifact and phase.
2. Retrieve or summarize relevant repository/product memory.
3. List related ADRs and event types.
4. State whether the change should emit a memory event.
5. Identify the smallest validation command.

Return:

- Active Spec Kit phase.
- Relevant artifacts.
- Event type(s).
- Memory scope.
- MCP context used or unavailable.
- Validation plan.
