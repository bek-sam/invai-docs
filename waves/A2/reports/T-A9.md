# Report: T-A9 Digest D9–D13, D2 bridge mover, Today actions backend
Author: backend-engineer on opus. Commit: invai-backend `522433b` (not pushed).

## Built
- D9–D13 in `digest/detectors.ts` (`d9ShippingLoss`, `d10LosingOrders`, `d11StockHealth`, `d12BlankCost`, `d13BreakEven`), in `detect()`; D10/D13 gated like other money detectors when > 20% of orders lack final fees. Thresholds in `config.ts` (d9..d13, severity D9..D13, `today`).
- `digest/track-e.ts`: inputs from `analytics.shippingMargin` (week + 4 prior weeks by channel), `losingOrders`, `inventoryHealth` (90 d), `supplierTrends` (200 d), `breakEven` (last 28 d), `profitBridge` (by design, same period). Runs in a savepoint inside `computeSnapshot`; a failure leaves D9–D13 silent, never fails the digest.
- D2 names `profitBridge.topMovers[0]` (params `designName`/`designId`, fact `d2.topMover`, href `/analytics/profit?view=why&days=7`, template `D2 action.mover`).
- en/es copy for D2 mover and D9–D13 in `render.ts`; `rank(…, { maxActions })` (digest 3, Today 5).
- Tables `today_action_sets`, `today_actions`, `today_action_clicks` in `db/schema/digest.ts`, migration `drizzle/0038_today_actions.sql` (generated; RLS + tenant policies; FKs `(company_id, set_id)`/`(company_id, action_id)` → `(company_id, id)`).
- `today/actions.ts`: `computeTodayActions(tx, ctx, {date})`, `buildTodayActions(companyId, date, {force})`, `getTodayActions`, `recordActionClick`. `today/jobs.ts`: `today.buildActions` (jobId `today-actions-${companyId}-${date}`), hourly `today.actionsSweep` (:15), nightly `today.actionsPurge` (90 d). Router off `stubRouter`.
- A1 note: `shippingMargin` channel/service rows tie-break on label, then key.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1–5 D9–D13 | Yes | `digest/track-e.test.ts` fires/doesn't pairs at each edge (19 tests) |
| 6 D2 = bridge top mover | Yes | `today/actions.test.ts` "AC-G1 digest leg" (DB, same period) |
| 7 pairs, en/es, no buyer data | Yes | track-e.test.ts copy + params allowlist + `DigestActionParams` parse |
| 8 ≤5 actions, cents, steady, click idempotent | Yes | actions.test.ts; curl below |
| 9 RLS, isolation, FORBIDDEN | Yes | rls/fk-coverage green; B sees none, B's click on A's key 404, FK 23503; 4 floor/designer roles + vendor 403 |
| 10 AC-G1 net | Yes | snapshot net == `unitEconomics(order).totals.cm3` |
| 11 run twice, purge, ACTION_NOT_FOUND | Yes | job run twice → `exists`, same rows; sweep twice → 1 set; purge keeps < 90 d |
| 12 tie sort | Yes | finance-service.test.ts "A1 note" (red on the old sort, green now) |

## Checks I ran
| Repo | Command | Result |
|---|---|---|
| backend | pnpm typecheck && pnpm lint | 0 errors; 446 files clean |
| backend | vitest digest today analytics src/db authz.test.ts | 29 files, 226 passed, 2 skipped, 1 todo |
| backend | pnpm typecheck && pnpm lint && pnpm test (full, run 3) | exit 0; 168 files passed, 2 skipped. Run 1: 8 files red (FK errors on vanished companies, likely a concurrent invai_test user); run 2: 1 flaky race in ai/publish.acceptance (passes alone). Neither touches T-A9 paths |

## Exercised for real (API :3161 PID 49504 + child 49521, worker PID 49506, Redis db 11)
- owner `GET /today/actions` → `generatedAt:null, actions:[]`; worker log `today actions built … actions:5` once; re-read → 5 actions (D6 overdue, D7 ×4), integer cents.
- `POST /today/actions/clicks` twice → same `clickedAt` 19:30:18.033Z; unknown key → 404 ACTION_NOT_FOUND.
- Refused: designer, presser → 403 FORBIDDEN (finance.read); vendor click → 403.
- Seed (digest week 09-21..28 and Today window 09-23..29), none of D9–D13 fires:
  - D9: max 22 labeled orders per channel per week (< 30); Shopify is 180¢ worse than its median and would fire at 30.
  - D10: 4.6% / 1.1% losing (≤ 5%). D11: dead stock 9.4% (≤ 15%); worst gaps G64000 Sand L −28 pts, CC1717 Moss M −21.3 have 22–25 days of cover (≥ 14). BC3001 Dusty Blue L only has enough units at 180 d (−24.4, 140 days cover).
  - D12: S&S costs flat (G64000 285¢, CC1717 640¢), last PO month 2026-07 is stale. D13: no fixed costs on the seed.
  - D2: digest week net change < 15%; Today window has 28/123 orders without final fees (> 20%), so money detectors stay silent.

## Decisions
- Added `today_action_sets` (one row per built day) beyond ruling 2's two tables: a steady day with zero actions still needs a "built" marker, and `fk-coverage.test.ts` requires FKs to reference `(company_id, id)`, so children carry `set_id`/`action_id`. Keys stay unique per `(company_id, date, key)` and clicks per `(company_id, action_id, user_id)`.
- Build guard is the set row (insert on conflict do nothing); `force` rebuild = delete + insert in one tx (clicks of that day go with it).
- D9 fires only on a loss (margin per order < 0) that worsened ≥ 50¢; D13 uses a 28-day pace, impact = monthly shortfall × 7/30; D11 impact = dead value, gap = units short over 14 d × net per unit; D12 impact = rise × latest month's units. Today: no Market items, no repeat suppression.
- D2 without a bridge mover keeps its old wording and `channel` param.

## Known gaps and follow-ups
- Web (T-A7/T-A6 `digest-copy.ts`): D2 `see_what_changed` now carries `designName` (the mover) instead of `channel` when the bridge has one; show "{{mover}} moved your profit the most" to match the email.
- `supplierTrends` rows have no supplier UUID, so D12 sets `supplierName` only (no `supplierId`).
- Seed fires no D9–D13; QA may want a seed shop with fixed costs set to show D13.

## Blocked by other owners
- none

## Processes and data
- Stopped: 49504, 49521, 49506 (ports 3161/3162 free). Shared dev DB: migration 0038 applied (an earlier uncommitted 0038 draft was dropped from dev and invai_test before regenerating); one Today set built for Desert Bloom (2026-09-30) and one click by owner.
