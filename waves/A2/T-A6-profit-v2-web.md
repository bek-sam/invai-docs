# T-A6: Web Profit v2 screens (B-173, folds in B-226)

| Field | Value |
|---|---|
| Wave | A2 |
| Scope ref | `product/scope.md#mvp-in` item 8 |
| Spec | `specs/business-analytics-v2.md` Track A; AC-A1, AC-A2, AC-A3, AC-A6, AC-A7, AC-E6 |
| Owner | web-engineer |
| Reviewer | reviewer (opus) |
| Co-reviewers | product-designer (new screens, sonnet) |
| Risk flags | ui |
| Model | sonnet |

## Owned paths (edit)
- `invai-web/src/routes/_app/analytics/profit.tsx` and new `invai-web/src/routes/_app/analytics/profit.*.tsx` if you split views into child routes
- new `invai-web/src/features/finance/profit-v2/**`
- `invai-web/src/routes/_app/settings/costs.tsx` (the fixed monthly costs field)
- `invai-web/src/lib/format.ts` and `format.test.ts` (additions only: locale-aware chart axis and percent helpers)
- Generated: `invai-web/src/routeTree.gen.ts`, `src/i18n/en.ts`, `src/i18n/es.ts`; `invai-web/scripts/i18n-es.json` (your keys only)

## Read-only paths
- Everything else in `invai-web` (notably `src/lib/nav.ts`, `src/routes/_app/index.tsx`, `analytics/operations*`, `analytics/inventory*`: T-A7's), `invai-ui/**`, `invai-contracts/**`, `invai-backend/**`, `invai-web/e2e/**` (QA)

## Depends on
- `analytics.*` in contract 0.9.0 (pushed in A1). No A2 contract change needed.
- T-A7 starts after this card commits its i18n and routeTree files (one owner of generated files at a time).

## Acceptance criteria
1. Views on Profit: Contribution (CM1/CM2/CM3 per channel, dimension switch order/design/blank/sku/channel), Orders that lost money, Leakage waterfall, Shipping profit (by channel, service, weight band, zone), Why it changed (bridge, volume vs rate, top 10 movers), Break-even card. Each view has Export CSV using `analytics.export` with the same filters.
2. AC-A1: CM3 total equals the Profit page's Net for the same period to the cent (say so in the report with both numbers from the seed).
3. AC-A2: losing orders list shows the shop's order number, CM2 and the largest cost line; no positive-CM2 order.
4. AC-A3: zero labeled shipments in the period → "No labeled shipments yet in this period", never an empty table or a $0 margin.
5. AC-A6: no fixed costs → "Add your monthly fixed costs to see break-even" linking to Settings → Costs, no number. Settings → Costs gains "Fixed monthly costs" (`CostSettings.fixedMonthlyCents`) with the hint that labor per shirt is already counted; set $2,500 → break-even orders and pace appear.
6. AC-A7: when orders lack a profit line, the view shows "{{n}} orders aren't in these numbers yet" (the banner pattern), never a silently partial total.
7. B-226: in Spanish at 1440 px the Costos KPI value isn't clipped; chart axes and percents use the active locale (`Intl`), including the existing Profit chart.
8. en and es for every label, empty state and explanation; money through `Intl`; percent-point changes as points ("+6,9 pts" style per the spec's locale rule). Owner and admin see the views; a role without `finance.read` doesn't get the nav entry or data.
9. Sample workspaces show the "sample data" label as the existing Profit page does.

## Verification
- `cd invai-web && pnpm typecheck && pnpm lint && pnpm test && pnpm build 2>&1 | tail -n 40`; `pnpm i18n` leaves no `scripts/i18n-es-missing.json` entry of yours.
- Browser against the shared dev stack (API :3000, web :5173; the dev CSP allows only :3000): as `owner@desertbloom.test`, each view at 1440 and 390 px in en and es; screenshots under `/Users/bekbolsun/invai/.e2e-out/web/T-A6/`, looked at. As `designer@` Profit is not reachable.
- Don't reset the shared dev DB. Don't start a second web server on :5173.

## Out of scope
- New backend or contract work (report gaps to the tech lead). Operations/Inventory screens and Today (T-A7). E2E spec edits (QA at the gate).

## Budget
- About 4 hours. Escalate if blocked for more than about 30 minutes.
