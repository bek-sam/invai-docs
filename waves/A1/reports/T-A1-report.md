# Report: T-A1 Analytics-ready seed (18 months of history)
Author: backend-foundation on Sonnet 5

Resumed after an OrbStack crash stalled the previous run at 00:39. Docker restarted ~01:10; all
services healthy. Inherited diff (builder.ts/index.ts/weekly-digest.ts, +606/-17) verified complete
and untouched (mtimes 00:37-00:38, no writes since); continued from there, did not redo it.

## Built (this session)
- `dest_zone` on seeded shipments: `zoneForZips(profile.address.zip, o.zip)` from
  `src/modules/shipping/zone.ts` (read-only), on every shipment insert (both closed-history and
  live-flow orders share one insert loop). (file: `invai-backend/src/db/seed/builder.ts`)
- Historical (closed-history) shipment destinations now vary (`random.pick(CITIES)`) instead of a
  hardcoded Phoenix zip, so `dest_zone` isn't always 1 for the 18 months of history.
- (Inherited, not rebuilt) 18 months of bulk-inserted closed order history, Q4 peak, 3 late-shipment
  drivers, realistic press-scan spacing, reprints across 2 stations/2 vendors, PO cost/lead-time
  drift, dead-stock + size-mix-gap variants, repeat Shopify buyers.

## Status: IN PROGRESS, not done. `pnpm typecheck && pnpm lint && pnpm test` now all green (see below).
Still missing: fresh seed run, AC-Seed1 SQL verification, API golden path, commit. Handed back
mid-verification (forced stop); resume needed for those remaining steps.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| all AC-Seed1 items | Not yet verified this session | Prep query file ready at scratchpad `ac-seed1.sql`; not run against a fresh seed yet |

## Checks I ran
- `pnpm typecheck` (invai-backend): **PASS** (`tsc --noEmit`, clean).
- `pnpm lint` (invai-backend): **PASS** (`biome check .` — "Checked 434 files ... No fixes applied").
- `pnpm test` (invai-backend), pinned `TEST_DATABASE_URL`/`TEST_MIGRATION_DATABASE_URL=invai_ta1_test`,
  `REDIS_URL=redis://localhost:6379/5`: completed after ~9 min (544.47s). **164 test files, 1 failed
  / 161 passed / 2 skipped; 1261 tests, 1 failed / 1256 passed / 3 skipped / 1 todo.** The one
  failure was `src/modules/shipping/side-effects.acceptance.test.ts` >
  "batchBuy: two batches over the same orders running at once buy one label per order" — a 30s
  timeout, not an assertion failure. Re-ran that file alone (same pinned DB/Redis, `--testTimeout=60000`):
  **8/8 passed in 2.07s.** This matches the known pattern (`team lessons`, T-22-2 r1: a stalled/loaded
  full-suite run produces time-shaped failures on concurrency tests; re-run before calling it a
  regression) — my change touches only `src/db/seed/**`, which this shipping side-effects test
  doesn't exercise. Treated as environmental flake, not a regression. **PASS overall.**
  (Two leftover vitest/Vite server child processes from each backgrounded run failed to exit on
  their own — "something prevents 2 Vite servers from exiting" — and were killed manually after
  confirming the run's result; not a code issue, just a known vitest teardown quirk.)

## Exercised for real
- Not yet run: fresh `db:reset && db:migrate && db:seed` on `invai_ta1`, AC-Seed1 SQL verification,
  `E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts` on `PORT=3111`. Scratch DBs `invai_ta1` /
  `invai_ta1_test` were dropped and recreated fresh at the start of this session (empty, not yet
  seeded). A verification query file is ready at the scratchpad path
  `ac-seed1.sql` (queries every AC-Seed1 item against `late_rate_drivers.sql`,
  `press_minutes_per_unit.sql`, `blank_stock_health.sql`, `size_mix_gap.sql`, `supplier_trends.sql`,
  plus reprint reason/station/vendor spread, repeat-buyer counts, `dest_zone` spread, and the two
  edge cases).

## Decisions
- Reused `CITIES` (already imported for live-flow orders) for historical destinations rather than
  adding a new city pool, since the task only asked for realistic zone variety, not new data.

## Known gaps and follow-ups
- Card is not done. Remaining steps for whoever resumes: (1) let/re-run `pnpm test` pinned to
  `invai_ta1_test` / Redis DB 5 to completion and confirm green; (2) fresh
  `db:reset && db:migrate && db:seed` on `invai_ta1` (pin `REDIS_URL=redis://localhost:6379/5`,
  `SEED_OUTPUT_FILE=.seed-output-ta1.json`), time it and compare against the 15-20 min baseline;
  (3) run the scratchpad `ac-seed1.sql` against `invai_ta1` and paste row counts for every AC-Seed1
  item; (4) `E2E_API=1 E2E_API_URL=http://localhost:3111 pnpm e2e e2e/api-golden-path.spec.ts` in
  invai-web against a `PORT=3111` API on the fresh seed; (5) commit `src/db/seed/**` only, then
  clean up (stop imaging PID 98656, drop `invai_ta1`/`invai_ta1_test`, flush Redis DB 5, delete
  `.seed-output-ta1.json`).
- `pnpm test` finished and is confirmed green (1256/1261 passed, the 1 failure was a re-confirmed
  flake, 3 skipped, 1 todo, matching the pre-existing skip/todo count seen in other A1 cards' reports).
  No test process is running any more; all backgrounded vitest/Vite children were killed after
  their results were captured.

## Blocked by other owners
None.

## Processes and data
- Imaging PID 98656 (reused from the stalled run): still running, healthy (`curl :8000/health`
  returned ok at session start). Not stopped yet — needed for the seed's imaging renders.
- `pnpm test` run (PID 5291 and the retest PID 7581) both completed and their child processes were
  killed after capturing results. No test process running any more.
- Scratch DBs `invai_ta1` (empty, not yet seeded) and `invai_ta1_test` (holds the test suite's
  schema from the runs above, no longer in use): both exist, neither dropped yet — next step should
  drop `invai_ta1_test` before the fresh `db:reset`/`migrate`/`seed` on `invai_ta1`.
- Redis DB 5: flushed once at the start of this session; used by the completed test runs, not
  currently in use by anything.
- Shared dev DB `invai`: untouched.
- Uncommitted changes remain in the working tree (not committed this session): the inherited
  builder.ts/index.ts/weekly-digest.ts diff plus this session's `dest_zone` + varied-destination
  edit to `src/db/seed/builder.ts`. Not committed because verification (test suite, seed run,
  AC-Seed1, golden path) is not yet complete.
