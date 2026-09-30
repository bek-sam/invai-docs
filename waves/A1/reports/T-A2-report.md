# Report: T-A2 `analytics.*` contract
Author: architect on fable

## Intake
Card: T-A2  Owner: architect  Scope ref: `product/scope.md#mvp-in` items 5, 6, 7, 8, 13, 14, 17. Owned: the card's list (+ `src/compat.ts`, `CHANGELOG.md`: the version bump's other halves, a test ties `compat.ts` to `package.json`); grant: backend `modules/analytics/router.ts` (stub) + one line and import in `api/router.ts`. Read-only: everything else. Risk flags → reviewer (opus) only. Unknowns: none.

## Progress
- 2026-09-30 intake; build; all checks green; committed contracts `f466088`, backend `9228343`; live exercise on :3121 done; API stopped; report final.

## Built
- `analytics` namespace, 11 procedures under `/analytics`, all `finance.read`, `auth: user`; domain error `PERIOD_INVALID` (400) on range reads and export (files: `invai-contracts/src/contract/analytics.ts`, `src/contract.ts`)
- Schemas + exported types (`invai-contracts/src/schemas/analytics.ts`, `src/index.ts`). **Exact names T-A3/T-A4/T-A5/T-A8 build against:**
  - T-A3: `UnitEconomicsInput`→`UnitEconomics` (`rows: UnitEconomicsRow[]`, `totals: ContributionLadder` = `revenue, cm1..cm3, cm1Pct..cm3Pct (null <30 units), orders, units, estimatedShare`, `ordersWithoutProfitLine`, `computedAt`); `LosingOrdersInput`→`LosingOrders` (`orders: LosingOrder[]` with `orderNo, channel, designId/Name, cm2, largestCostLine: AnalyticsCostLine, largestCostLineCents, estimated`; `losingOrders, ordersWithProfitLine, losingPct, lossCents, ordersWithoutProfitLine`); `LeakageInput`→`Leakage` (`grossSales, waterfall: LeakageStep[]` over `LEAKAGE_COMPONENTS`, `remaining, leakagePct, orders, ordersWithoutProfitLine`); `ShippingMarginInput{groupBy: SHIPPING_MARGIN_GROUPS}`→`ShippingMargin` (`rows: ShippingMarginRow[]`, `totals: ShippingMarginTotals` = `labeledOrders, charged, labelCost, margin, marginPerOrder, freeShippingOrders`; `shipmentsWithoutZone`); `ProfitBridgeInput{period, basePeriod?, by: PROFIT_BRIDGE_BY (default design), channel?}`→`ProfitBridge` (`basePeriod` resolved, `baseCm3, currentCm3, totalChange = volumePart + ratePart, refundsChange` (own line), `topMovers: ProfitBridgeMover[] ≤10`, `baseOrders, currentOrders, hasEnoughOrders`); `BreakEvenInput{period}`→`BreakEven` (`fixedCostsSet, fixedMonthlyCents|null, orders, cm3, cm3PerOrder|null, breakEvenOrders|null, pace|null, operatingProfitPace|null, hasEnoughOrders`). Enums: `ANALYTICS_DIMENSIONS` (`order|design|blank|sku|channel`), `ANALYTICS_COST_LINES` (= `CostBuckets` keys).
  - T-A4: `OperationsInput{period, channel?}`→`Operations` (`hasEnoughHistory`, `reprintCost: ReprintCost{total, reprints, itemsPressed, ratePct, byReason[key∈REPRINT_REASONS], byStation, byVendor}`, `filmWaste: FilmWaste{sheets, wasteCost, filmUsePct, byVendor}`, `waits: StageWait[]{state∈ORDER_ITEM_STATES, entries, medianHours, p90Hours, stillWaiting}`, `bottleneckStep|null`, `pressMinutesPerUnit: PressStationRow[]{stationId, stationName, timedUnits, medianMinutes, p75Minutes, unitsPerActiveHour, settingMinutes, suggestUpdateLaborSetting}`, `lateDrivers: LateDrivers{shippedOrders, lateOrders, latePct, rows: LateDriverRow[]{driver∈LATE_DRIVERS, value, label, shippedOrders, lateOrders, latePct}}`, `computedAt`). `Shipment.destZone`.
  - T-A5: `InventoryHealthInput{days 7..365 default 90}`→`InventoryHealth` (`days, asOf, hasEnoughHistory, onHandUnits, onHandValue, consumedCost, turns|null, deadStock: DeadStock{variants, value, pctOfStockValue, rows: DeadStockRow[]≤50}, sizeMixGaps: SizeMixGapGroup[]{styleCode, color, label, unitsSold, onHand, hasEnoughUnits, sizes: SizeMixSizeRow[]{blankVariantId, size, unitsSold, onHand, salesSharePct, stockSharePct, gapPts|null, coverDays|null}}, stockoutExposure: StockoutExposure{units, blanks, revenueAtRisk, earliestShipBy, rows}`); `SupplierTrendsInput{period}`→`SupplierTrends` (`rows: SupplierTrendRow[]{supplier∈SUPPLIERS, supplierName, styleCode, month YYYY-MM, purchaseOrders, units, avgUnitCost, medianLeadDays|null}`, `leadTimeSettingDays, measuredLeadDays|null, suggestUpdateLeadTime`); `DesignLifecycleInput{asOf?, channel?}`→`DesignLifecycle` (`asOf, hasEnoughHistory, rows: DesignLifecycleRow[]{designId, designName, stage∈DESIGN_LIFECYCLE_STAGES, units4w, unitsPrior4w, units365d, firstSaleAt, lastSaleAt, hasActiveListing, marketTrend: TrendClass|null, marketGrowth4w|null}`, `stageCounts`); `AnalyticsExportInput` = discriminated union on `view∈ANALYTICS_VIEWS`, each member that view's input → `AnalyticsExport{key}` (same as `finance.exportCsv`).
  - T-A8: `tool_call.name` gains `get_unit_economics, explain_profit_change, get_operations_health, get_inventory_health, get_shipping_insights` (end of enum, `src/schemas/ai.ts`).
- `CostSettings.fixedMonthlyCents: Cents.nonnegative().nullish()` (writable via `CostSettingsInput`; `src/schemas/finance.ts`); `Shipment.destZone: int 1..9 nullish`, output only (`src/schemas/shipping.ts`).
- Version 0.9.0 (`package.json`, `src/compat.ts`, `CHANGELOG.md`); `FLOOR_COMPAT_BASELINE` untouched. README: namespace row + permission bullet.
- Backend: `src/modules/analytics/router.ts` = `stubRouter(...)` only; `analytics: analyticsRouter` in `src/api/router.ts`.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 typecheck contracts/backend/web | yes | commands below; floor also green |
| 2 every `analytics.*` needs `finance.read` | yes | `analytics.test.ts` "every procedure needs finance.read"; live: designer 403 on 3 procedures |
| 3 `destZone` int 1..9 nullish, no address field | yes | `analytics.test.ts` "Shipment.destZone" (rejects 0, 10, 2.5, "3"; no zip/address/street/city/name key; in no input) |
| 4 five names appended at the end, nothing else changed | yes | `analytics.test.ts` asserts the full 19-name enum; consumers grepped: `invai-web/src/i18n/{en,es}.ts` `assistant.tool.*` (plain string map, no switch: T-A8/web adds 5 labels), backend `ai/validators/answer.ts` (`MARKET_TOOL_NAMES` Set, untouched), `ai/providers/mock.ts` (mock call list, T-A8 adds cases), `modules/ai/assistant-tools.ts` (T-A8 registers the tools). No exhaustive switch; web/floor typecheck green |
| 5 `Period` required on range reads; `days`/`asOf` on snapshots; `channel` optional; new fields optional | yes | `analytics.test.ts` "range reads require the shared Period" (same `Period` object as `finance.profit`), "channel is an optional CHANNELS enum", `CostSettings` parses without the field |

## Checks I ran
| Repo | Command | Result |
|---|---|---|
| invai-contracts | `pnpm typecheck && pnpm lint && pnpm test` | tsc clean; biome 59 files, no fixes; `Test Files 9 passed, Tests 105 passed` |
| invai-backend | `pnpm typecheck && pnpm lint` | tsc clean; biome 425 files, no fixes |
| invai-web | `pnpm typecheck` | tsc clean |
| invai-floor | `pnpm typecheck` | tsc clean |

## Exercised for real
- `PORT=3121 REDIS_URL=redis://localhost:6379/6 pnpm dev:api` (shared dev DB, read-only); `POST /api/auth/sign-in/email` → 200 for designer@ and owner@.
- designer@ → `analytics.unitEconomics`, `analytics.inventoryHealth`, `analytics.export`: **403 `FORBIDDEN` `{"permission":"finance.read"}`** on all three (the guard fires before the stub).
- owner@ → the same three: **501 `NOT_IMPLEMENTED` "analytics.unitEconomics is not implemented yet"** (stub reached).

## Decisions
- `channel?` on the 7 sales-based reads (unitEconomics, losingOrders, leakage, shippingMargin, profitBridge, operations, designLifecycle), not on `inventoryHealth`, `supplierTrends`, `breakEven`: stock, POs and fixed costs have no channel, and a filter the backend would ignore is a lie. Deviates from AC5's literal "everywhere"; tested explicitly.
- "Not computed" is `.nullable()`, never optional (`breakEvenOrders: null`), so consumers get one shape; `hasEnoughHistory`/`hasEnoughOrders` are required booleans.
- `export` input is a discriminated union on `view` reusing each read's input schema (same filters as the screen, structurally). Unknown keys are stripped, not rejected (house `z.object` semantics).
- `profitBridge.totalChange = volumePart + ratePart` exactly (AC-A5); dated refunds are a separate `refundsChange` line per `profit_bridge.md`.
- No ADR file: `invai-docs/decisions/` isn't in the card's owned paths. The namespace rule (finance.read, user auth, values not errors) lives in the contract doc comment and README; tech lead may want a short ADR (I can write it on request).

## Known gaps and follow-ups
- Backend `analytics.*` all throw `NOT_IMPLEMENTED` until T-A3/T-A4/T-A5 register handlers (by design).
- T-A3 must persist `fixedMonthlyCents` in `finance/service.ts` `updateCostSettings` (it is already accepted by the contract).
- `src/market.test.ts` relaxed from "last four names" to "contiguous, in order" (the newest wave's test owns the "at the end" check); `src/p2-sweep.test.ts` version pin relaxed to "≥ 0.8.0".

## Blocked by other owners
- none

## Processes and data
- Started: API on :3121 (tsx watch PID 94717, node listener PID 94724). Stopped: both (`lsof :3121` free, `ps` shows neither). Shared dev DB: untouched (read-only sign-ins). Scratch cookie jars deleted.
- Commits (not pushed): invai-contracts `f466088`, invai-backend `9228343`. `git diff --stat origin/main` lists only owned paths in both repos.
