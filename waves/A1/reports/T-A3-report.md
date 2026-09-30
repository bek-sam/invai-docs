# Report: T-A3 Finance analytics service + `fixed_monthly_cents`
Author: backend-engineer (finance) on opus. Status: **built, one final test run blocked by the Postgres/OrbStack hang (see Known gaps).**

## Intake
Card T-A3 (B-170), scope `mvp-in` items 7, 8. Owned: `analytics/{router,shared,finance-service,finance-*}.ts`, `finance/service.ts`, `db/schema/finance.ts` + migration. Flags: tenancy, migration, money → reviewer + backend-foundation + security-reviewer.

## Progress
- 00:31 migration generated and committed first (`95e9d69`) so T-A4 could follow.
- Service, shared `computeNet`, router, tests; analytics 13/13 + parity 6/6 + finance/digest 111 green; committed `1afdfc3`.
- Live exercise on :3131 found a bug (fixed-cost PATCH still emitted a recompute); fixed + router-level test, committed `31db7f3`.
- Then Postgres stopped completing handshakes (TCP open, `docker exec` hangs): post-fix test run and full suite could not run.

## Built
- `cost_settings.fixed_monthly_cents` nullable int (`drizzle/0036_finance_fixed_monthly_cents.sql`, one `ADD COLUMN`).
- `analytics/shared.ts` `computeNet(tx, ctx, period, {dimension, channel?, designId?})`: the one net calculation (profit lines by placed_at + dated refunds). `finance.getProfit` now calls it (output shape and numbers unchanged); `mergeRefunds`/`companyTimezone` moved here (extracted, not duplicated). Also `countOrdersWithoutProfitLine`.
- `analytics/finance-service.ts`: `unitEconomics`, `losingOrders`, `leakage`, `shippingMargin`, `profitBridge`, `breakEven`, plus `assertPeriod` (PERIOD_INVALID), `pgRound`, `bridgeSplit`, `weightBand`.
- `analytics/router.ts`: 6 handlers in `withTenant`; `stubRouter` spread kept (T-A4 has since added `operations`).
- `updateCostSettings` persists `fixedMonthlyCents` (null clears it); a fixed-cost-only change emits no `cost_settings.changed` (no 90-day recompute).

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| AC-A1 | yes | test "CM3 totals equal getProfit's Net"; live: unitEconomics cm3 559309 = finance.profit net 559309; per-channel CM1/2/3 = `contribution_margin.sql` on dev DB |
| AC-A2 | yes | test: label-sunk order cm2 −1635, `labelCost` 2400; positive orders absent; = `losing_orders.sql` |
| AC-A3 | yes | parity test vs `shipping_margin.sql`; live channel rows identical to SQL on dev DB (etsy 107 / −47171 / 50 free …); 0 labeled → null per-order margin |
| AC-A5 | yes | test volume+rate=total, top mover = SQL rank 1; live week 09-21: total 32666 = 25865+6801 and top 8328 = SQL |
| AC-A6 | yes | test + live: before → `fixedCostsSet:false`, nulls; $2,500 → 154 orders, pace 343, op. pace 309309 = `break_even.sql` |
| AC-A7 | yes | tests: 3 orders without a line counted in leakage and unitEconomics; live shows 3 |
| AC-G1 | yes (whole-shop) | test mocks `computeNet` as a pass-through spy: getProfit and unitEconomics each call it once with the same period (digest `lastCompleteWeek` + `localMidnights`), totals equal; shopify-filtered case too |
| AC-E4/E5 | yes | test: B's rows never in A (all 6), A's ctx inside B's tenant → 0 rows; router: designer and presser FORBIDDEN on all 6; live designer 403 ×6 |

## Checks I ran
| Repo | Command | Result |
|---|---|---|
| backend | `pnpm typecheck && pnpm lint` (after last commit) | tsc clean; biome 434 files, no fixes |
| backend | `vitest run src/modules/analytics` (at `1afdfc3`, own DB `invai_ta3_test`, redis/8) | 13 + 6 passed |
| backend | `vitest run src/modules/finance src/modules/digest …/onboarding.test.ts` | 14 files, 111 passed |
| backend | `pnpm typecheck && pnpm lint && pnpm test` after `31db7f3` (no pipe, own DB) | tsc clean; biome 434 files clean; **`pnpm test` exit 1 in global setup: `connect ECONNREFUSED 127.0.0.1:5432`** (Postgres down, not a test failure; 0 tests ran) |

## Exercised for real (API :3131, shared dev DB, period 2026-09-01..10-01 Phoenix)
- owner: all 6 procedures 200 with numbers above; PERIOD_INVALID 400 for an inverted period; shippingMargin groupBy zone → no rows, `shipmentsWithoutZone` 263.
- `PATCH /finance/cost-settings {fixedMonthlyCents:250000}` → 250000, then breakEven as above.
- Refused: designer → 403 FORBIDDEN `finance.read` on all 6, and 403 on the PATCH.

## Decisions
- breakEven's CM3 is the Profit page's Net (`computeNet`, includes dated refunds), per the definition's intent ("Profit page's Net / orders"). `break_even.sql` v1 sums `net_cents` only; they agree when no refund falls in the window (dev seed: exact match); the parity test pins the gap to the refund net. **data-analyst: consider a v2 of break_even.sql.**
- profitBridge `refundsChange` = effect on profit (−Δ net dated refunds), so totalChange + refundsChange = change in Net (tested). `by: costLine` pools units shop-wide and lists every bucket plus `revenue` ("Sales"), so the movers sum to the total.
- Weight bands: 0-4oz, 4-8oz, 8-12oz, 12-16oz, 1-2lb, 2-5lb, 5lb+ (USPS price breaks); service key `carrier/service`.
- leakage follows `revenue_leakage.sql` exactly (cancelled orders out of gross and counts); unitEconomics/losingOrders use getProfit's "items, no profit line" count.
- Parity suite reads `../invai-docs/metrics/sql` and `skipIf` that path is missing (backend-only CI).

## Known gaps and follow-ups
- Post-fix test run and full `pnpm test` are pending the infra hang; the tech lead or reviewer should rerun `vitest run src/modules/analytics src/modules/finance` and `pnpm test` once Postgres answers.
- Zone rows need `shipments.dest_zone` (T-A4): `shippingMargin` groupBy zone must read it then (T-A4 or a follow-up; my file).
- Shared dev DB: desertbloom `fixed_monthly_cents` left at 250000 (restore to null failed with the hang), and one `cost_settings.changed` event from the pre-fix PATCH (an idempotent 90-day recompute).

## Functions other modules may call
`computeNet`, `countOrdersWithoutProfitLine`, `companyTimezone` (analytics/shared.ts); the 6 finance-service functions (for T-A8 tools, T-A9 digest).

## Blocked by other owners
- Local Postgres (OrbStack) hang: platform-sre / tech lead. I did not restart orb (shared wave).

## Processes and data
- Started/stopped: API node PID 98951 (wrong entry, killed at once), 98988 (API :3131, killed); orphan vitest 99559 (killed); my hung `docker exec`/`docker ps` probes 356/358, 99809/99811, 116/118 (killed). Other agents' vitest/docker processes untouched.
- `invai_ta3_test` and redis DB 8 not yet dropped/flushed (infra hang): to do once Postgres answers.
- Commits (not pushed): backend `95e9d69`, `1afdfc3`, `31db7f3`.
