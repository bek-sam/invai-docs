# T-A2: `analytics.*` contract

| Field | Value |
|---|---|
| Wave | A1 |
| Scope ref | `product/scope.md#mvp-in` items 5, 6, 7, 8, 13, 14, 17 (read-only contract over already-in-scope data) |
| Spec | `specs/business-analytics-v2.md` Track A/B/C/E procedure list; AC-E4, AC-E5, AC-G1 |
| Owner | architect |
| Reviewer | reviewer (opus) |
| Co-reviewers | none (decision 0019: author is the architect; the opus primary reviewer covers consumer impact; tool names carry no prompt text) |
| Risk flags | contract |
| Model | fable |
| Backlog ref | B-169 |

## Owned paths (edit)
- `invai-contracts/src/contract/analytics.ts` (new file: `unitEconomics`, `losingOrders`, `leakage`, `shippingMargin`, `profitBridge`, `breakEven`, `operations`, `inventoryHealth`, `supplierTrends`, `designLifecycle`, `export`) and its registration in the root contract (`src/contract.ts`)
- `invai-contracts/src/schemas/analytics.ts` (new: input/output Zod schemas for the above) and its export from `src/index.ts`
- `invai-contracts/src/schemas/finance.ts` (add `CostSettings.fixedMonthlyCents: Cents.nonnegative().nullish()`, optional so existing handlers still typecheck)
- `invai-contracts/src/schemas/shipping.ts` (add `Shipment.destZone: z.number().int().min(1).max(9).nullish()`, in no input)
- `invai-contracts/src/schemas/ai.ts` (append the five v6 tool names to the `AssistantEvent` `tool_call.name` enum, at the end: `get_unit_economics`, `explain_profit_change`, `get_operations_health`, `get_inventory_health`, `get_shipping_insights`)
- `invai-contracts/src/*.test.ts` for the new shapes, `invai-contracts/README.md` (namespace/permission rows), `package.json` version bump (minor, additive)
- **Grant (tech lead, 2026-09-30, architect plan review ruling 1):** `invai-backend/src/modules/analytics/router.ts` (new, stub only: `stubRouter(authed.analytics, contract.analytics, ["analytics"])`) and the single `analytics: analyticsRouter` line plus its import in `invai-backend/src/api/router.ts`. Committed in the same step as the contract so backend typecheck never breaks.

## Read-only paths
- `invai-backend/src/modules/finance/**`, `src/modules/production/**`, `src/modules/inventory/**`, `src/modules/shipping/**` (read the existing shapes you're contracting over)

## Depends on
- None (first card in the wave; commits the stubs the other four cards build against).

## Interfaces promised
- `analytics.unitEconomics({period, dimension: order|design|blank|sku|channel, channel?}) -> {rows, totals, ordersWithoutProfitLine}` (rows carry revenue, CM1/CM2/CM3 + their %, orders, units, estimated share)
- `analytics.losingOrders({period, limit≤50}) -> {orders}` (order number, channel, design, CM2, largest cost line)
- `analytics.leakage({period, channel?}) -> {waterfall, ordersWithoutProfitLine}`
- `analytics.shippingMargin({period, groupBy: channel|service|weightBand|zone}) -> {rows}` (zone rows only for shipments with `destZone` set)
- `analytics.profitBridge({period, basePeriod?, by: design|channel|costLine}) -> {volumePart, ratePart, totalChange, topMovers}` (`basePeriod` defaults to the equal-length period just before `period`, stated in a doc comment)
- `analytics.breakEven({period}) -> {fixedCostsSet: boolean, breakEvenOrders?, pace?, operatingProfitPace?}`
- `analytics.operations({period}) -> {reprintCost, filmWaste, waits, bottleneckStep, pressMinutesPerUnit, lateDrivers, hasEnoughHistory}`
- `analytics.inventoryHealth({days}) -> {onHandValue, turns, deadStock, sizeMixGaps, stockoutExposure, hasEnoughHistory}`
- `analytics.supplierTrends({period}) -> {rows}` (unit cost by supplier x style x month, median lead days, lead-time-setting delta)
- `analytics.designLifecycle({asOf?, channel?}) -> {rows, hasEnoughHistory}` (stage per design; `asOf` is a DateOnly, default today in shop time zone)
- `analytics.export({view: enum of the 10 read procedures, period, channel?, ...}) -> ` the same output shape as `finance.exportCsv` (the S3 key of the file). Not "csv or URL".
- `hasEnoughHistory: boolean` is required on `operations`, `inventoryHealth`, `designLifecycle`. A per-metric "not enough data" is a nullable value plus its sample count (for example `timedUnits`), never an error: analytics reads don't throw for business outcomes.
- Every procedure requires the `finance.read` permission (exists: `src/roles.ts:91`; owner, admin, office hold it) with `auth: user`, never floor/station, and is `withTenant`-scoped (contract-level: the permission guard name on each procedure, per `add-contract-procedure`'s consumer checklist).
- All ten `analytics.*` reads and the five v6 tool schemas are committed as typed stubs (throw `NOT_IMPLEMENTED` in a trivial reference backend impl, or leave unimplemented per the usual stub pattern) so T-A3/T-A4/T-A5 and T-A8 can build against real types from day one.

## Acceptance criteria
1. Given the contract package, when `pnpm typecheck` runs in `invai-contracts`, `invai-backend`, `invai-web`, then all three pass against the new types (consumer checklist in `add-contract-procedure`).
2. Given any `analytics.*` procedure, when its permission is inspected, then it requires `finance.read` (AC-E5: a role without it — designer, presser, packer, receiver, vendor — must be refusable once implemented).
3. Given `Shipment.destZone`, when the schema is inspected, then it is a nullable smallint with no address, ZIP or name field alongside it (AC-A4's column-list constraint starts at the contract).
4. Given the `AssistantEvent` `tool_call.name` enum, when inspected, then the five v6 names are appended at its end and nothing else in it changes. The `{data, summary, answer}` shape and the ≤20-row limit are T-A8's criteria (they live in backend `ai/assistant-tools.ts`). The report lists the consumers grepped: `invai-web/src/i18n/{en,es}.ts` tool labels, backend `ai/validators/answer.ts`, `ai/providers/mock.ts` (additive; no exhaustive switch expected).
5. Edge cases: every range procedure takes the existing `Period {from, to}` (`schemas/common.ts`, as `finance.profit` does), required, so parity (AC-G1) is checkable; the snapshot procedures keep `days` (bounded int, `inventoryHealth`) and `asOf` (optional, `designLifecycle`). `channel` is `z.enum(CHANNELS).optional()` everywhere. `fixedMonthlyCents` and `destZone` are optional on output, so the backend's finance and shipping handlers and a web SPA one version behind still work.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test` in `invai-contracts`; `pnpm typecheck && pnpm lint` in `invai-backend` (with the stub router), `pnpm typecheck` in `invai-web` and `invai-floor` (as consumers, per the change-order rule) to confirm nothing else breaks.
- Exercise for real: a script or short backend test that calls each new procedure's stub against a running API and confirms the permission guard fires `FORBIDDEN` for a non-`finance.read` role token.

## Out of scope
- Any real implementation logic (that's T-A3/T-A4/T-A5/T-A8). This card is types and permissions only.
- Track D procedures (goals, anomaly alerts, customer analytics, cash view, scheduled emails) — gated on OI-18.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned. This card gates T-A3/T-A4/T-A5/T-A8; land it first.
