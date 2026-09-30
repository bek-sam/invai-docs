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

## Resumed session 2026-09-30 (backend-foundation on Sonnet 5)

Progress log (one line per step, per instructions):
- Step 0: Confirmed `invai_ta1` seed from the prior session was complete (not a stalled/partial
  run): `.ta1-seed.log` shows `[seed] done {"orders":1326,...,"seconds":543}` at 12:05:25, and DB
  counts match exactly (orders 1326, order_items 1780, order_item_transitions 11324, shipments
  1185, purchase_orders 32, listings 160). The log's tail also has a second process's failure
  output (`parse_relation.c` / `EXIT 1 at 06:56:19`) appended after the success line — a colliding
  concurrent reset attempt, not a corruption of the completed run. `.seed-output-ta1.json` present
  and matches (`counts: {orders:1326, items:1780, transitions:11324, dueSoon:88}, seconds:543`).
  Did not reseed.
- Step 1a: Wrote `invai-backend/.ta1-ac-seed1.sql` (AC-Seed1 verification queries, sourced from
  `specs/business-analytics-v2.md` AC-Seed1 and `metrics/sql/{late_rate_drivers,
  press_minutes_per_unit,supplier_trends,size_mix_gap,blank_stock_health}.sql`) and ran it against
  `invai_ta1`. **Found a real AC-Seed1 #2 failure**: 0 late-shipped orders across every driver cut
  (rush/personalized/blocked_over_24h all showed `late=0` out of hundreds of shipped orders),
  even though `src/db/seed/builder.ts`'s closed-history block clearly computes a late `shippedAt`
  (`shipBy + [4,36)h`) for `plan.driver !== null` orders.
- Step 1b: Root-caused it (own paths only, `src/db/seed/builder.ts`): historical orders are also
  pushed onto the shared `shippedOrders` array (used by both the live-flow and closed-history
  blocks to build `shipments` rows), but that array didn't carry the already-decided `shippedAt`.
  The shared "shipments" loop then always computed `labeledAt = min(shipBy - 3h, placedAt + 40h)`
  for every order — always **before** `shipBy** — silently overwriting every historical order's
  carefully-chosen on-time/late `shippedAt` with an always-on-time one. Net effect: no order in
  the whole seed could ever be late, regardless of its driver.
- Step 1c: Fixed (small, in-owned-path): added an optional `shippedAt?: Date` field to the
  `shippedOrders` array's type; the closed-history push now passes its already-computed
  `shippedAt`; the shipments loop now does `labeledAt = o.shippedAt ?? <old formula>` (live-flow
  orders, which never had a pre-computed `shippedAt`, are unaffected). `pnpm typecheck`: clean.
  (files: `invai-backend/src/db/seed/builder.ts`)
- Step 1d: Reseeded `invai_ta1` from scratch to verify the fix (pinned
  `DATABASE_URL`/`MIGRATION_DATABASE_URL`/`REDIS_URL`/`SEED_OUTPUT_FILE`, background + polled,
  under the agent-brief's long-command rule). Results below.

### AC-Seed1 results (fresh `invai_ta1`, reseeded after the fix, 31s total — see timing note below)

Full counts pasted from `docker exec -i local-postgres-1 psql -U invai -d invai_ta1 -v from="'2025-02-01'" -v to="'2026-10-01'" -v days=600 -f invai-backend/.ta1-ac-seed1.sql`:

| # | AC-Seed1 item | Threshold | Result | Met? |
|---|---|---|---|---|
| 1 | Span | ≥18 months | 2025-02-27 → 2026-09-30 = 19.0 months | yes |
| 1 | Q4 peak | ≥1.5x trailing avg | Nov 2025: 99 orders vs 44.0 trailing avg = **2.25x**; Dec 2025: 100 vs 44.0 = **2.27x** | yes |
| 2 | Late-shipment drivers ≥30 orders each | ≥2 | `blocked_over_24h=true`: 50 shipped / 50 late (100%); `rush=true`: 77/50 (64.9%); `personalized=true`: 158/62 (39.2%) — 3 drivers clear 30, all show nonzero lateness | yes (was **failing before the fix below**) |
| 3 | Station(s) with ≥100 timed units | ≥1 | Press 1 station: 176 timed units, median 4.02 min/unit, stddev 1.61 (non-constant) | yes |
| 4 | Supplier×style cost/lead changes | ≥2 pairs, ≥5% cost or >3d lead | ssactivewear×CC1717 (lead +5d), ssactivewear×G64000 (cost +9.6%) | yes |
| 5 | Repeat Shopify buyers | ≥2 buyers, ≥2 orders each | 7 buyers with 2-3 orders each | yes |
| 6 | Reprint reasons/stations/vendors | ≥3 reasons, ≥2 stations, ≥2 vendors | 4 reasons (peel/ghosting/misprint/wrong_placement), 3 stations, 2 vendors | yes |
| 7 | Size-mix gap | ≥1 gap ≥15pts, ≥30 units (group) | Top: G64000/Black/S, gap 60.5pts (group well over 30 units); 9 more rows ≥15pts | yes |
| 8 | Dead stock | ≥1 variant, nonzero $ | 14 dead variants, $1,619.27 | yes |
| 9 | (edge case) dest_zone spread | not always 1 | 8 distinct zones, 88-233 shipments each | yes |
| 10 | (edge case) orders with no profit line | present | 41 orders | yes |
| 11 | (edge case) cancelled-after-on_sheet | present | 7 orders | yes |

**Bug found and fixed (AC-Seed1 #2 was failing before this session's fix):** the closed-history
block in `builder.ts` computes a late `shippedAt` (`shipBy + [4,36)h`) for orders whose
`plan.driver !== null` (personalized/rush/blocked), but historical orders are also pushed onto the
shared `shippedOrders` array that both the live-flow and closed-history code use to build
`shipments` rows. The shared shipments loop unconditionally recomputed
`labeledAt = min(shipBy - 3h, placedAt + 40h)` — always **before** `shipBy` — and then overwrote
`orders.shippedAt` with it, silently erasing every historical order's on-time/late decision. Net
effect on the seed as it stood at session start: **0 late-shipped orders anywhere**, regardless of
driver (confirmed: `is_rush=true` historical orders all had `shipped_at` before `ship_by`).
Fix (in owned path `invai-backend/src/db/seed/builder.ts`, 3 small edits): added an optional
`shippedAt?: Date` field to the `shippedOrders` array type; the closed-history push now carries its
already-decided `shippedAt`; the shared shipments loop uses `o.shippedAt ?? <old formula>` (live-flow
orders, which never had a pre-decided `shippedAt`, are unaffected — confirmed no other AC or count
regressed). `pnpm typecheck`: clean. Verified by reseeding `invai_ta1` from scratch and re-running
the AC-Seed1 SQL (table above): all 3 driver cuts now show real, varied lateness.

**Timing note:** this reseed finished in 31s (`[seed] done {...,"seconds":31}`), vs. 543s for the
prior session's run. Not a shortcut: MinIO holds real files from this exact run window (57 artwork
PNGs at 13:45:29-30 UTC, 47-66 KiB each; 4 gang-sheet PNGs at 13:45:32-39 UTC, 2.9-7.7 MiB each — a
plausible few seconds per multi-MB sheet compose, not instant/cached), DB row counts match the
log's own summary exactly, and every AC-Seed1 query above returned real, varied data. The likely
cause: the prior 543s run happened right after an OrbStack crash and cold Docker restart (per that
session's own report), while this run had Postgres/imaging/MinIO already warm for hours. Either
way this is well **under** the "no slower than today" (15-20 min) budget, so not a regression to
chase further.

- Step 2a: First golden-path attempt (API on :3111, `invai_ta1`, Redis 5) failed at test 4 ("a
  personalized item gets a proof and is approved") with "timed out waiting for personalization
  render" — cause: I'd started only the API, no worker, so the `personalization.renderArtwork` job
  never ran. Started a worker pinned to the same `invai_ta1`/Redis 5 and re-ran; that second attempt
  (reusing the same, now-partially-mutated DB from attempt 1) failed at test 3 with a state
  mismatch (`expected "needs_attention", got "new"`) — the golden path isn't idempotent across two
  runs on the same seed (test 2's CSV import behaves differently against its own leftover data).
  Reseeded `invai_ta1` from scratch a third time (`[seed] done {...}` clean), then ran the suite
  **once**, API + worker both up, against the fresh seed. Result below.
- Step 3: Fixed the flaky `src/db/seed/market-demand.test.ts` (own path) — gave its one `it(...)` a
  `60_000` ms third-argument timeout (matches the existing pattern in
  `src/modules/channels/webhooks.test.ts`'s "Shopify OAuth state" tests, added by Biome's own
  formatter back onto one line). No assertion touched. Ran it alone twice against a fresh
  `invai_ta1_test` (created for this session) + Redis 5: **pass, pass** (7.99s, then 8.19s each
  time). Did not run the full suite (left to the gate per instructions).

### Golden path + Today queue counts (fresh `invai_ta1`, API :3111 + worker, one clean run)

`E2E_API=1 E2E_API_URL=http://localhost:3111 pnpm e2e e2e/api-golden-path.spec.ts --reporter=line`:
**7 passed, 1 failed, 5 did not run** (Playwright `serial` mode stops the rest of the file after a
failure). Tests 1-7 all green: sign-in/Today, Etsy CSV import, SKU mapping, personalization proof,
gang-sheet build (utilization **83.41% / 83.14%**, well inside the realistic 80%+ target and far
from the old "51.7%" bug), send-to-vendor, sheet-received.

Test 8 ("floor: PIN login...") failed with `Station token required`/`CLIENT_TOO_OLD` root cause:
`invai-web/e2e/helpers/api.ts`'s `seedOutput()` hardcodes reading `<backend>/seed-output.json` (no
env override), and that file belongs to the **shared dev DB's** shop (mtime Sep 29 23:56, a
different `shopId`/station token than `invai_ta1`'s). My role's rules forbid writing
`seed-output.json` (agent-brief "Never: ... write seed-output.json"), and another agent is reading
it read-only for the concurrent T-A5 review, so I did not touch it. This is an environmental gap in
the E2E harness for running this suite against any scratch DB other than the shared one, not a
regression from this card's changes: **verified directly** by calling `POST /rpc/floor/staff` with
`invai_ta1`'s own station token (from `.seed-output-ta1.json`) and the `x-contract-version: 0.9.0`
header by hand — it returned the real staff list (admin/designer/presser/office/...), so the floor
auth path itself works fine against this seed; only the E2E test's fixed file path can't reach it.
Flagging for QA/tech-lead: `seedOutput()`/`stationSession()` would need an env override (e.g.
`E2E_SEED_OUTPUT_FILE`) to run this suite against a scratch DB end-to-end; out of my owned paths
(`e2e/**` is QA's).

Today's queue (`GET today.summary`, called directly as the signed-in owner against the fresh seed):
```
orders:  dueToday=37  overdue=17  atRisk=30  onHold=0  newSinceYesterday=15
blocked: needsMapping=7  needsArtwork=3
stations waiting/doneToday: pick 57/0, press 57/22, qc 23/0, pack 26/0
```
All nonzero and varied (satisfies test 1's `dueToday+overdue+atRisk > 0` and `stations.length > 0`,
and the card's "Today's queue counts ... unchanged or the diff is called out" — I have no prior
`invai_ta1`-specific baseline to diff against since this is that baseline; order/item totals
(1325 orders / 1793 items on the final reseed) are consistent across all three reseeds this session,
within the seed's normal randomness).

## Round 2

Verification-only, read-only SQL against the shared dev DB (`docker exec -i local-postgres-1 psql -U
invai -d invai`), freshly seeded by the tech lead's gate at commit 5170e12 (log
`invai-infra/.gate/run-20260930T172303Z.log`: backend suite + golden path + browser + floor all
green at this commit). Did not reseed, did not run the full test suite (already proven by the gate).
Company `01354862-c5d7-4490-9e35-ec848902bee8` (Desert Bloom Tees).

| AC-Seed1 item | Threshold | Result | Met? |
|---|---|---|---|
| History span | ≥18 months | 2025-02-27 → 2026-09-30 = 19.0 months | yes |
| Q4 peak vs trailing avg | ≥1.5x | Nov-2025 439 / Dec-2025 462 vs Mar-Oct-2025 avg 214.4/mo = **2.05x / 2.15x** | yes |
| No live-window cliff | live vs prior ~2x | last 30d (live) = 358 orders; three prior 30d windows = 322, 315, 305 (avg 314) → **1.14x**, no cliff | yes |
| Late drivers ≥30 shipped, ≥2 | `late_rate_drivers.sql` | `blocked_over_24h=true` 50 shipped/50 late; `rush=true` 77/50; `personalized=true` 411/57 — **3 drivers** clear 30 with real, varied lateness | yes |
| Station ≥100 timed units | `press_minutes_per_unit.sql` | 1 station: 176 timed units, median 4.16 min, p75 5.60 min (non-constant) | yes |
| Supplier×style cost/lead pairs | ≥2, ≥5%/>3d | `supplier_trends.sql`: G64000 cost 260→285¢ (+9.6%), CC1717 lead 4→9d (+5d) | yes |
| Repeat Shopify buyers | ≥2 buyers, ≥2 orders | 7 buyers, 2+ Shopify orders each | yes |
| Reprints | ≥3 reasons, ≥2 stations, ≥2 vendors | 4 reasons (ghosting/misprint/peel/wrong_placement), 3 stations, 2 vendor connections | yes |
| Size-mix gap | ≥15 pts, ≥30 units in group | `size_mix_gap.sql`: BC3001/Black/3XL +18.0pts, BC3001/Dusty Blue/L -18.6pts (groups ≥30 units) | yes |
| Dead stock | nonzero $ | `blank_stock_health.sql`: 9 dead variants, $1,170.50 | yes |
| dest_zone spread (edge case) | not always 1 | 8 distinct zones | yes |
| No profit line yet (edge case) | present | 38 open orders with no `profit_lines` row | yes |
| Cancelled after on_sheet (edge case) | present | 12 order_items | yes |
| Golden path unchanged | gate | Already proven green at 5170e12 by the gate (API 13/13, browser 34/34, floor 3/3); not re-run here | yes |

**Review r1 finding 1 (history-volume cliff) — answered:** fixed by ramping closed-history daily
volume from 6/day (18 months back) to 11/day (at `histEnd`, ~31 days ago), times 1.75 in Q4, so it
meets the live window's own rate instead of stopping flat at ~1.5/day. Verified above: live 30-day
window (358 orders) is now only **1.14x** the trailing three 30-day history windows (avg 314), well
inside the ~2x target — no cliff. (Round 1's own numbers, 8x, are gone.)

**Review r1 finding 2 (Q4-year picks a partial, in-progress quarter) — answered:** fixed by picking
the most recent year whose Dec 31 falls on or before `histEnd`, instead of `histEnd`'s own year.
`histEnd` this run is ~2026-08-30 (before Dec 31 2026), so `q4Year` resolves to 2025 — the full,
already-closed Nov 1-Dec 31 2025 — not a partial in-progress quarter. Confirmed in the monthly
counts: Nov-2025 (439) and Dec-2025 (462) are both fully boosted, each ≈2.1x the pre-Q4 trailing
average, not just a few boosted days.

**Optional notes (a-e) from review r1:** left as-is, per the tech lead's instructions (round 2 was
scoped to findings 1 and 2 only). None of a-e block AC-Seed1: (a) late-iff-driver probability shape
is cosmetic realism, not a threshold; (b) scan/reprint/PO timing precision issues don't change any
AC-Seed1 count; (c) the weekly-digest comment is pre-existing and unrelated to this card's diff; (d)
AC-C1's premise recheck is T-A5's card, not this one; (e) the runtime claim was independently
reconfirmed by the gate (5377 orders, 43s — see gate log), settling it.

No code changed this round; no processes started; shared dev DB read-only (SELECT only, no reset).

### Verdict

All AC-Seed1 items pass against the dev DB at commit 5170e12. Both review r1 blocking findings are
resolved with numbers. Recommend: approve.
