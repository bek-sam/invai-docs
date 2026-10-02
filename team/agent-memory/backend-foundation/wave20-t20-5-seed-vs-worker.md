---
name: wave20-t20-5-seed-vs-worker
description: T-20-5 lessons - the demo seed's counts depend on the UTC day (compare baselines back-to-back), relayOnce is a 100-row batch on a never-truncated test DB, and db:reset now obliterates queues in REDIS_URL's DB
metadata:
  type: project
---

Facts learned on T-20-5 (2026-09-28/29), seed safe next to a running worker.

- The demo seed is **not** run-to-run stable across a UTC midnight: same code gave 683 items / 3908 transitions
  at 23:5x UTC and 694 / 3935 at 00:1x UTC (`Date.now()`-relative order placement crosses day boundaries), and
  even minutes apart the transition count can differ by 1. **Why:** comparing "before vs after my change" by
  seed counts is only valid when the baseline (a detached worktree at HEAD, symlinked `node_modules`) and the
  new code run back-to-back, and the proof is the per-state transition breakdown and per-event outbox
  breakdown diffing empty, not the `[seed] done` line alone. **How to apply:** any card that touches the seed
  or claims "counts unchanged" runs HEAD and the change within minutes of each other on the same DB copy.
- `relayOnce()` (`src/worker/outbox-relay.ts`) takes the 100 oldest pending rows per call, and the shared test
  DB is migrated but never truncated between files, so a full-suite run leaves hundreds of pending rows from
  other companies ahead of a new test's rows. A relay test that passes alone and fails in the full suite is
  this; loop `relayOnce()` until your company's rows are gone (bounded), never assume one call reaches them.
- `pnpm test` and `pnpm db:reset` both use `REDIS_URL` from `.env` (DB 0, the dev worker's DB): `env.ts`
  rewrites `DATABASE_URL` under `NODE_ENV=test` but not `REDIS_URL`. Pin `REDIS_URL=redis://localhost:6379/<n>`
  on every run of a card; `reset.test.ts` obliterates the queues of whatever DB it is pointed at.
- Vitest (v5) prints no per-test lines in a non-TTY log until the end; `grep -c "✓"` on a running log shows 0
  and means nothing. Judge progress by `ps -o etime` and the final summary.
