# T-A5: Inventory and design analytics (turns, dead stock, size-mix gap, supplier trends, design lifecycle)

| Field | Value |
|---|---|
| Wave | A1 |
| Scope ref | `product/scope.md#mvp-in` item 6 (blank inventory, reservations, POs, receiving, reorder), item 8 (design profit) |
| Spec | `specs/business-analytics-v2.md` Track C; AC-C1, AC-C2, AC-C3, AC-C4, AC-C5, AC-B/C-screen1, AC-E4, AC-E5 |
| Owner | backend-engineer (inventory) |
| Reviewer | reviewer (opus) |
| Co-reviewers | security-reviewer (tenancy) — decision 0019; the primary reviewer checks that market data is read through the market module's service export, never its tables |
| Risk flags | tenancy |
| Model | sonnet |
| Backlog ref | B-172 |

## Owned paths (edit)
- `invai-backend/src/modules/analytics/router.ts` (add **only** the `inventoryHealth`, `supplierTrends`, `designLifecycle` and `export` procedure registrations; land after T-A4, don't touch T-A3/T-A4's existing registrations)
- `invai-backend/src/modules/analytics/inventory-service.ts` (**create**: turns, dead stock value, size-mix gaps, stockout exposure, supplier price/lead-time trends)
- `invai-backend/src/modules/analytics/design-service.ts` (**create**: design lifecycle stage; defers to the market module's trend when one exists for that design)
- `invai-backend/src/modules/analytics/*.test.ts` for this card's files (name them `inventory-*.test.ts`, `design-*.test.ts`)
- `invai-backend/src/modules/inventory/reorder.ts` (size-split suggestion only — proportional to the trailing size curve; the shop edits every line before submitting, nothing is submitted automatically)

## Read-only paths
- `invai-backend/src/modules/market/**` (read the existing trend computation for `analytics.designLifecycle` to defer to; don't edit market module code)
- `invai-backend/src/modules/analytics/finance-service.ts`, `shared.ts`, `operations-service.ts` (read only; don't edit T-A3/T-A4's files)

## Depends on
- T-A2 (contract stubs for `analytics.inventoryHealth`, `supplierTrends`, `designLifecycle`, `export`) must land first.
- T-A4 must land first (shares `analytics/router.ts`).
- T-A1 (seed) needed for AC-C1/AC-C2 (dead stock, size-mix gap with real dollar values).

## Interfaces promised
- `analytics/router.ts` gains three new registrations: `inventoryHealth`, `supplierTrends`, `designLifecycle` plus the shared `export` procedure (confirmed on T-A5, architect plan review ruling 3: output identical to `finance.exportCsv`; it calls T-A3/T-A4 services read-only). No edits to earlier cards' registrations.
- `reorder.ts`'s size-split suggestion never calls a supplier or creates a PO by itself — it only proposes quantities on a draft the shop edits and submits.

## Acceptance criteria
1. **AC-C1**: Given the seed's under-stocked size (e.g. a style/color's L size selling well below its stock share), when `analytics.inventoryHealth` is called, then that size shows as under-stocked with its sales and stock share; a style × color with < 30 units sold in the window is not shown (minimum-sample rule).
2. **AC-C2**: Given variants with stock and no use in 90 days, when `analytics.inventoryHealth` is called, then dead-stock count and value match `metrics/sql/blank_stock_health.sql`.
3. **AC-C3**: Given a reorder suggestion for a style with a size gap, when the owner creates a PO from it, then the proposed quantities follow the size curve and every line is editable before submitting; nothing is submitted automatically (test: no PO is created without an explicit submit call).
4. **AC-C4**: Given a design with an active listing and no sale in 60 days, when `analytics.designLifecycle` is called, then it's marked "dead"; given the market module has a trend for that design, then the market trend is shown instead and wins over the lifecycle-only stage.
5. **AC-C5**: Given purchase-order lines for a supplier × style over several months (from T-A1's seed), when `analytics.supplierTrends` is called, then unit cost by month and median lead days match `metrics/sql/supplier_trends.sql`, and when the measured lead time differs from the style's lead-time setting by > 3 days, the response includes a suggestion pointing at the setting.
6. **AC-B/C-screen1**: Given a shop below every metric's minimum sample overall, when `analytics.inventoryHealth` or `analytics.designLifecycle` is called, then the response's `hasEnoughHistory` flag is `false`, in addition to each metric's own per-widget threshold (e.g. AC-C1's 30-unit minimum still shows "not enough data" per style/color, not a silent omission).
7. **AC-E4/AC-E5**: Given two companies A and B, `analytics.inventoryHealth`/`supplierTrends`/`designLifecycle` for A show no row of B; a role without `finance.read` gets `FORBIDDEN`.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test` in `invai-backend`.
- Exercise for real: `PORT=31xx pnpm dev:api`, sign in as `owner@desertbloom.test`, curl each procedure against the fresh seed; create a reorder PO from a size-split suggestion and confirm every line is editable and nothing auto-submits.

## Out of scope
- Finance/profit analytics (T-A3), operations/shipping analytics (T-A4), any web screen (T-A7), the assistant tools (T-A8).
- Automatic PO creation, automatic price/listing changes (fence).
- Track D — gated on OI-18.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
