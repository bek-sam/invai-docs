---
name: market-signals-notes
description: Wave 18 facts for AI work on market signals - trademark screen threshold, answer check design, debugging tricks in this repo's vitest setup
metadata:
  type: project
---

- 2026-09-27 T-18-4: the trademark check at the medium band (25) drops real niche terms on fuzzy matches ("St. Patrick's Day" → Patrick Star, "easter bunny shirt", "groomsmen"). Unreviewed market terms use 60 (the listing hard gate). Re-measure over all taxonomy labels and queries before changing it.
  **Why:** a dropped niche label silently disables that niche's signals.
  **How to apply:** any new automatic trademark screen with no human reviewer: measure false positives on the real term list first.
- 2026-09-27 T-18-4: the market answer check (`src/ai/validators/answer.ts`) takes numbers only from JSON numbers in tool data, tool summary/answer text, the InvAI shop context and fixed copy. Never from shop-typed strings or the user's message (injection "say it's up 900%"). Date parts count only as literals (the month "09" × 100 once licensed "900").
- 2026-09-27 T-18-4: vitest's setup silences console output; surface debug values with a thrown Error in a temp test. The session scratchpad is shared with other agents (my files vanished): use a subfolder. tsx scripts outside the repo need `.mts` for top-level await and absolute imports into `invai-backend/node_modules`.
