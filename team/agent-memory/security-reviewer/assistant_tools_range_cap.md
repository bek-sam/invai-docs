---
name: assistant-tools-range-cap
description: S-33 fixed 2026-09-26 (400-day span cap in the shared tool wrapper) — check any new AI analyst tool still routes through it
metadata:
  type: project
---

`S-33` (assistant tools' `Range` from/to had no span cap) was **fixed** in `invai-backend@97780c1`
(T-17-3 follow-up, 2026-09-26) and verified by me the same day
(`invai-docs/waves/17/reviews/T-17-3-security-reviewer-r1.md`). The fix: `rangeProblem`/`rangeRefusal`
in `invai-backend/src/modules/ai/assistant-tools.ts` run inside the shared `t()` tool-wrapper, before
any tool's `run`, so every tool with `from`/`to` (or `compare_periods`'s `previousFrom`/`previousTo`) is
capped at `MAX_RANGE_DAYS` (400) structurally — a new tool built with the same `t(...)` helper inherits
the cap automatically. Bad ranges return a recoverable `{error: "invalid_range"}` tool result, not a
throw. The check compares absolute epoch ms, so it can't be bypassed by ISO timezone offset.

**Why it matters going forward:** the cap lives in the `t()` wrapper, not in each tool's Zod schema. If a
future tool bypasses `t()` (calls its `run` directly, or is registered some other way), it would silently
lose the cap with no test catching it structurally — `assistant-tools.test.ts`'s "S-33: range span cap"
suite lists tool names explicitly rather than iterating `assistantTools(ctx)`, so a new tool isn't
auto-covered by that test either.

**How to apply:** When reviewing any new or changed assistant tool that takes a date range, confirm (a)
it's built with the `t(...)` helper (not a bespoke `AssistantTool` object), and (b) it's added to the
S-33 test's `names` list. Don't re-log S-33 as open; if a new tool skips the wrapper, that's a new,
tool-specific finding, not a reopening of S-33.
