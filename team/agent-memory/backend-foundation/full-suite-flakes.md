---
name: full-suite-flakes
description: Full-suite pnpm test failures under load are usually pre-existing flakes, not regressions — always re-run alone before calling it a regression
metadata:
  type: feedback
---

Seen repeatedly (T-A1, T-22-2 r1, T-P1-1, T-P1-1 r2): a lone failure inside a full `pnpm test` run
(1250-1450+ tests) on a scratch DB/Redis pair is very likely load noise, not a regression from your
diff.

**Why:** concrete repeats —
- T-22-2 r1: a stalled full suite shows as tens-of-minutes Duration with time-shaped failures
  (expired OAuth link, presign 403, redis timeout).
- T-A1: `shipping/side-effects.acceptance.test.ts`'s concurrent-batchBuy test timed out (30s) only
  inside a 544s full run, then passed 8/8 in 2s alone on the same pinned DB/Redis with nothing else
  running.
- T-P1-1: three back-to-back full runs on a clean pinned scratch DB each hit a different single
  unrelated flake (ai assistant-tools markdown, another live agent's scratch test file, shipping
  concurrent-batchBuy) — every one passed alone immediately after.
- T-P1-1 r2: two real *concurrent* full-suite runs each hit one pre-existing Postgres-side flake
  under load (`tuple concurrently updated` in `ensureReferenceData`/migrations; `test-db.test.ts`'s
  fixed-name `invai_test_999999998` stale-sweep race) — both passed 13/13 re-run alone immediately
  after.
- T-22-2 r1 (second resume): before a full suite on a scratch DB, check `pg_stat_activity` for
  other connections to it — a stalled earlier instance of the same card running tests on the same
  DB + Redis DB produced a `market_series_cache` deadlock and a `companies_slug_unique` collision,
  not real failures.

**How to apply:** never report a lone full-suite failure as a regression without re-running that
one file in isolation on the same pinned DB/Redis first. Also check for a second process already
running against your scratch DB/Redis before concluding anything.
