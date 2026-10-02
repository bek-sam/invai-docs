---
name: settled-toPass-fix
description: settled()'s swallowed timeout (eager-thumbnail-grid-aborts.md) is fixed as of T-P2-3 — it now uses expect(...).toPass() and throws a count+URL message; no call site needed a longer timeout.
metadata:
  type: project
---

T-P2-3 (2026-09-30) replaced `settled()`'s `expect.poll(...).toBe(0).catch(() => {})` in
`invai-web/e2e/helpers/ui.ts` with `expect(async () => { ... }).toPass({ timeout })`: the callback
throws `settled(): <n> skeleton/spinner element(s) still present at <url>` when the count is
non-zero, and `toPass` rethrows that on timeout instead of swallowing it.

**Why:** Playwright 1.63's `expect.poll` has no `message` option (checked
`playwright/types/test.d.ts`); `toPass` does the same polling but rethrows whatever the callback
last threw, which is the cleanest way to get a custom timeout message.

**How to apply:** after this fix landed, a full `pnpm e2e` (35 specs, dev DB, T-P2-1 lazy-thumbnails
already in) ran 34 passed / 1 skipped / 0 failed with no spec needing an explicit longer timeout at
its call site — confirms T-P2-1 actually fixed the root cause ([[eager-thumbnail-grid-aborts]]) and
wasn't being masked by anything else. If a future `pnpm e2e` run times out inside `settled()`, the
error now names the exact count and route, so root-cause from that message directly instead of
re-deriving it.
