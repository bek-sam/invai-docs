# T-A3: Finance analytics service (CM ladder, leakage, shipping margin, bridge, break-even)

| Field | Value |
|---|---|
| Wave | A1 |
| Scope ref | `product/scope.md#mvp-in` item 8 (Profit per order, design, blank and channel), item 7 (shipping) |
| Spec | `specs/business-analytics-v2.md` Track A; AC-A1, AC-A2, AC-A3, AC-A5, AC-A6, AC-A7, AC-G1, AC-E4, AC-E5 |
| Owner | backend-engineer (finance) |
| Reviewer | reviewer (opus) |
| Co-reviewers | backend-foundation (migration), security-reviewer (tenancy) |
| Risk flags | tenancy, migration, money |
| Model | opus |
| Backlog ref | B-170 |

## Owned paths (edit)
- `invai-backend/src/modules/analytics/router.ts` (**take over** the stub T-A2 committed: implement its 6 procedures and keep the `stubRouter` spread for the other 5 until T-A4/T-A5)
- `invai-backend/src/modules/analytics/finance-service.ts` (unitEconomics, losingOrders, leakage, shippingMargin, profitBridge, breakEven)
- `invai-backend/src/modules/analytics/shared.ts` (**create**; the one function both the Profit page and `analytics.unitEconomics` call, for AC-G1 parity — extract, don't duplicate, the net-profit calculation)
- `invai-backend/src/modules/finance/service.ts` (refactor only as needed to call the shared function from `analytics/shared.ts`, and persist `fixedMonthlyCents` in `updateCostSettings` since `CostSettingsInput` now accepts it; don't change existing output shapes) and its tests `finance/*.test.ts`
- `invai-backend/src/modules/analytics/*.test.ts` for the files above (name them `finance-*.test.ts`)
- `invai-backend/src/db/schema/finance.ts` (add `cost_settings.fixed_monthly_cents`, nullable int) + its migration (`pnpm db:generate --name finance_fixed_monthly_cents`)
- `invai-docs/metrics/definitions/{contribution_margin,losing_order_rate,revenue_leakage,shipping_margin,profit_bridge,break_even}.md` (only if a definition needs a version line to match what you build — coordinate with data-analyst before editing; prefer no edit)

## Read-only paths
- `invai-backend/src/modules/shipping/**` (read `shipments.postage_cents`, `rate_quotes`; don't edit — T-A4 owns writes here)
- `invai-backend/src/modules/production/**`, `src/modules/inventory/**` (read only)

## Depends on
- T-A2 (contract stubs for `analytics.unitEconomics`, `losingOrders`, `leakage`, `shippingMargin`, `profitBridge`, `breakEven`, and `CostSettings.fixedMonthlyCents`) must land first.
- T-A1 (seed) should be far enough along to test against realistic data, but this card can start against the current seed and re-verify once T-A1 lands.

## Interfaces promised
- `computeNet(tx, ctx, period, opts)` in `analytics/shared.ts` (takes the tenant transaction and context like other services, so it runs inside `withTenant`; architect plan review finding 5): the single function the Profit page (`finance/service.ts` `getProfit`), `analytics.unitEconomics`, the future assistant `get_unit_economics` tool (T-A8) and the digest snapshot (T-A9) all call, so AC-G1 parity is structural, not coincidental.
- `analytics/router.ts` registers `unitEconomics`, `losingOrders`, `leakage`, `shippingMargin`, `profitBridge`, `breakEven` now. **T-A4 and T-A5 add their own procedure registrations to this same file later, sequenced after this card lands** (each adds only its own lines; neither may edit this card's registrations without a report to the tech lead).

## Acceptance criteria
1. **AC-A1**: Given the demo seed and a period, when an owner opens the contribution view (or calls `analytics.unitEconomics` directly), then CM1, CM2, CM3 per channel appear, and CM3 totals equal `finance.getProfit`'s Net for the same period to the cent.
2. **AC-A2**: Given an order whose label cost exceeds revenue less other costs, when `analytics.losingOrders` is called, then that order appears with CM2 and "Label" as the largest cost line; an order with positive CM2 does not appear.
3. **AC-A3**: Given labeled orders with shipping charged and label costs, when `analytics.shippingMargin` is called grouped by channel, then labeled orders, charged, label cost and margin match `metrics/sql/shipping_margin.sql` on the same database, and free-shipping orders are counted (not dropped).
4. **AC-A5**: Given two weeks with different sales, when `analytics.profitBridge` is called, then the stated volume and per-unit parts sum to the stated total change, and the top-named design matches `profit_bridge.sql`'s top rank.
5. **AC-A6**: Given no fixed costs set, when `analytics.breakEven` is called, then it returns `fixedCostsSet: false` and no break-even number; given `$2,500` set via `cost_settings.fixed_monthly_cents`, then break-even orders and pace match `break_even.sql`.
6. **AC-A7**: Given a period with orders that have no profit line, when `analytics.leakage` or `unitEconomics` loads, then `ordersWithoutProfitLine` is a nonzero, accurate count — never a silently partial total.
7. **AC-G1** (this card proves the whole-shop half now; the per-channel half and the assistant/digest call sites land with T-A8/T-A9): given the digest's last-completed calendar week, no channel filter, `dimension: order`, when `finance.getProfit` and `analytics.unitEconomics` both call `computeNet`, then they're equal to the cent for that exact week — proven by a test asserting both call sites resolve to the same function and the same number.
8. **AC-E4/AC-E5**: Given two companies A and B, when any of these procedures runs for A, no row of B appears; given a role without `finance.read`, the call returns `FORBIDDEN`.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test` in `invai-backend` (tests against `invai_test`, per `src/test/fixtures.ts`).
- Exercise for real: `PORT=31xx pnpm dev:api`, sign in as `owner@desertbloom.test`, curl each procedure; sign in as `designer@desertbloom.test` and confirm `FORBIDDEN`.
- Migration: `pnpm db:generate --name finance_fixed_monthly_cents`, commit the migration file.

## Out of scope
- Operations/shipping-zone analytics (T-A4), inventory/design analytics (T-A5), any web screen (T-A6), the assistant tools (T-A8).
- Track D (goals, cash view, anomaly alerts) — gated on OI-18.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
