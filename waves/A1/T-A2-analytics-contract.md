# T-A2: `analytics.*` contract

| Field | Value |
|---|---|
| Wave | A1 |
| Scope ref | `product/scope.md#mvp-in` items 5, 6, 7, 8, 13, 14, 17 (read-only contract over already-in-scope data) |
| Spec | `specs/business-analytics-v2.md` Track A/B/C/E procedure list; AC-E4, AC-E5, AC-G1 |
| Owner | architect |
| Reviewer | reviewer (opus) |
| Co-reviewers | backend-foundation (consumer, tenancy shape), web-engineer (consumer), ai-engineer (v6 tool names) |
| Risk flags | contract |
| Model | fable |
| Backlog ref | B-169 |

## Owned paths (edit)
- `invai-contracts/src/contract/analytics.ts` (new file: `unitEconomics`, `losingOrders`, `leakage`, `shippingMargin`, `profitBridge`, `breakEven`, `operations`, `inventoryHealth`, `supplierTrends`, `designLifecycle`, `export`)
- `invai-contracts/src/schemas/analytics.ts` (new: input/output Zod schemas for the above)
- `invai-contracts/src/contract/finance.ts` (add `CostSettings.fixedMonthlyCents`, nullable int cents)
- `invai-contracts/src/contract/shipping.ts` (add `Shipment.destZone`, nullable smallint 1-9)
- `invai-contracts/src/contract/ai.ts` (add the five v6 assistant tool names/schemas as stubs: `get_unit_economics`, `explain_profit_change`, `get_operations_health`, `get_inventory_health`, `get_shipping_insights` — schema only, no prompt text)

## Read-only paths
- `invai-backend/src/modules/finance/**`, `src/modules/production/**`, `src/modules/inventory/**`, `src/modules/shipping/**` (read the existing shapes you're contracting over)

## Depends on
- None (first card in the wave; commits the stubs the other four cards build against).

## Interfaces promised
- `analytics.unitEconomics({period, dimension: order|design|blank|sku|channel, channel?}) -> {rows, totals}` (rows carry revenue, CM1/CM2/CM3 + their %, orders, units, estimated share)
- `analytics.losingOrders({period, limit≤50}) -> {orders}` (order number, channel, design, CM2, largest cost line)
- `analytics.leakage({period, channel?}) -> {waterfall, ordersWithoutProfitLine}`
- `analytics.shippingMargin({period, groupBy: channel|service|weightBand|zone}) -> {rows}` (zone rows only for shipments with `destZone` set)
- `analytics.profitBridge({period, basePeriod?, by: design|channel|costLine}) -> {volumePart, ratePart, totalChange, topMovers}`
- `analytics.breakEven({period}) -> {fixedCostsSet: boolean, breakEvenOrders?, pace?, operatingProfitPace?}`
- `analytics.operations({period}) -> {reprintCost, filmWaste, waits, bottleneckStep, pressMinutesPerUnit, lateDrivers, hasEnoughHistory}`
- `analytics.inventoryHealth({days}) -> {onHandValue, turns, deadStock, sizeMixGaps, stockoutExposure, hasEnoughHistory}`
- `analytics.supplierTrends({period}) -> {rows}` (unit cost by supplier x style x month, median lead days, lead-time-setting delta)
- `analytics.designLifecycle({asOf, channel?}) -> {rows, hasEnoughHistory}` (stage per design)
- `analytics.export({view, period, ...filters}) -> {csv}` (or a signed download URL, matching the existing profit-export pattern)
- Every procedure requires the `finance.read` permission and is `withTenant`-scoped (contract-level: the permission guard name on each procedure, per `add-contract-procedure`'s consumer checklist).
- All ten `analytics.*` reads and the five v6 tool schemas are committed as typed stubs (throw `NOT_IMPLEMENTED` in a trivial reference backend impl, or leave unimplemented per the usual stub pattern) so T-A3/T-A4/T-A5 and T-A8 can build against real types from day one.

## Acceptance criteria
1. Given the contract package, when `pnpm typecheck` runs in `invai-contracts`, `invai-backend`, `invai-web`, then all three pass against the new types (consumer checklist in `add-contract-procedure`).
2. Given any `analytics.*` procedure, when its permission is inspected, then it requires `finance.read` (AC-E5: a role without it — designer, presser, packer, receiver, vendor — must be refusable once implemented).
3. Given `Shipment.destZone`, when the schema is inspected, then it is a nullable smallint with no address, ZIP or name field alongside it (AC-A4's column-list constraint starts at the contract).
4. Given the five v6 assistant tool schemas, when `ai-engineer` reads them for T-A8, then each has the `{data, summary, answer}` shape used by the existing 14 tools and a ≤20-row limit on `data`.
5. Edge cases: `period` is a required, explicit range (not "trailing N days" implied) on every procedure so parity (AC-G1) is checkable; `channel` and other filters are optional and consistently named across procedures.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test` in `invai-contracts`; `pnpm typecheck` in `invai-backend`, `invai-web` (as consumers, per the change-order rule) to confirm nothing else breaks.
- Exercise for real: a script or short backend test that calls each new procedure's stub against a running API and confirms the permission guard fires `FORBIDDEN` for a non-`finance.read` role token.

## Out of scope
- Any real implementation logic (that's T-A3/T-A4/T-A5/T-A8). This card is types and permissions only.
- Track D procedures (goals, anomaly alerts, customer analytics, cash view, scheduled emails) — gated on OI-18.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned. This card gates T-A3/T-A4/T-A5/T-A8; land it first.
