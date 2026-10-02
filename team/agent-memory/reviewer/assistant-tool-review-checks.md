---
name: assistant-tool-review-checks
description: How to live-probe assistant tools (SSE ask via curl, rpc compare) and what mock-mode tests can't prove
metadata:
  type: feedback
---

2026-09-30 T-A8: live-probe assistant tools with `POST /api/v1/ai/assistant/ask` (SSE; parse `data:` lines, `tool_call` events carry name+input) and compare numbers via `POST /rpc/analytics/<proc>` with body `{"json":{...}}`. Headers need `Origin: http://localhost:5173`. In zsh, don't pack curl `-H` flags into one `$H` var (no word splitting -> 400).

**Why:** mock assistant plans calls from the message text only, so "injection in tool output doesn't change behavior" unit cases can't fail in mock; only a real-model eval (e.g. as-042) proves it. Note it, don't block.

**How to apply:** for assistant tool cards, check finance/permission gating against ROLE_PERMISSIONS in invai-contracts/src/roles.ts (every role with ai.assistant.ask also has finance.read today), and check baseline.json diffs for re-encoded unrelated rows.
