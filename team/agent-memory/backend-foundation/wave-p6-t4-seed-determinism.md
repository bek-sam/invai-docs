---
name: wave-p6-t4-seed-determinism
description: How the demo seed was made repeatable (B-249) and how to prove seed determinism and post-seed pool settledness cheaply
metadata:
  type: project
---

T-P6-4 (2026-10-01). The seed's big run-to-run swings came from two clocks: now-relative plans and
midnight-pinned due-soon plans sorted together by real placedAt, so the PRNG stream shifted by time
of day and the whole closed history changed. Fixed with `src/db/seed/plan-order.ts` (sort key on a
noon-UTC anchor). Smaller sources: unordered LIMITs, `min(id)` over random UUIDs, heap-order blanks,
`order by created_at, id` timelines (fixed with `cmin`, valid only before the rows are updated).

**Why:** back-to-back seeds can look identical while a seed hours later differs completely.

**How to apply:**
- Prove time-of-day independence with a Date-shift preload (`tsx --import shift.mjs`, overriding
  `Date`/`Date.now` by SHIFT_HOURS) instead of waiting hours; DB `now()` is not shifted.
- The full seed takes ~45 s on a warm stack here (not 15-20 min), so A/B seeds are cheap.
- Pool settledness: snapshot the DB at seed exit (`createdb -T`, then GRANT to invai_app), build
  inline there, compare with a build after the worker drains. Held events did not move the pool;
  the worker's 10-min mock Shopify poll does ([[wave20-t20-5-seed-vs-worker]]).
- A residual: `weekly-digest.ts` recompute cutoff `now - 2d` still crosses the pinned orders.
