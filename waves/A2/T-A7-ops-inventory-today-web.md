# T-A7: Web Operations, Inventory health, Designs lifecycle column, Today actions panel (B-174, B-177 web; folds in B-225)

| Field | Value |
|---|---|
| Wave | A2 |
| Scope ref | `product/scope.md#mvp-in` items 5, 6, 14 |
| Spec | `specs/business-analytics-v2.md` Tracks B, C, E; AC-B1..B3, AC-B/C-screen1, AC-C1, AC-C2, AC-C4, AC-C5, AC-E2 (web half), AC-E6 |
| Owner | web-engineer |
| Reviewer | reviewer (opus) |
| Co-reviewers | product-designer (new screens, sonnet) |
| Risk flags | ui, golden path (Today) |
| Model | sonnet |

## Owned paths (edit)
- new `invai-web/src/routes/_app/analytics/operations.tsx`, `invai-web/src/routes/_app/analytics/inventory.tsx`
- new `invai-web/src/features/analytics/**` (operations, inventory health, supplier trends sections)
- new `invai-web/src/features/today/**` (the actions panel)
- `invai-web/src/routes/_app/index.tsx` (mount the panel; B-225: use `dateLocale()` for the greeting date)
- `invai-web/src/routes/_app/catalog/designs.index.tsx` (lifecycle column)
- `invai-web/src/lib/nav.ts` (+ `nav.test.ts`): two entries under Analytics
- `invai-web/src/components/digest/digest-copy.ts` (+ test): the six new action-kind cases (D9–D13) with en/es copy; T-A10's contract breaks this exhaustive switch until you add them (architect finding 5). Reuse `digestActionText` for the panel wording.
- B-225 ban: a check that fails on `toLocaleDateString(undefined` / `toLocaleString(undefined` in `src/` (a test in `src/lib/`, or a Biome rule if `biome.json` supports it; say which)
- Generated: `src/routeTree.gen.ts`, `src/i18n/en.ts`, `src/i18n/es.ts`; `scripts/i18n-es.json` (your keys only)

## Read-only paths
- `invai-web/src/routes/_app/analytics/profit*`, `src/features/finance/**`, `settings/costs.tsx`, `src/lib/format.ts` (T-A6's; use its helpers), `invai-ui/**`, `invai-contracts/**`, `invai-backend/**`, `invai-web/e2e/**` (QA)

## Depends on
- T-A6 committed (generated files free). T-A10 contract 0.10.0 and T-A9 `today.actions` / `today.recordActionClick` committed.

## Acceptance criteria
1. Operations (`/analytics/operations`): reprint cost by reason/station/vendor, film waste $ and film use by vendor, waits per step (median, p90, still waiting) with the bottleneck named, measured press minutes per unit per station with the timed count (AC-B2: > 25% off the labor setting with ≥ 100 timed units → suggestion linking to Settings → Costs; fewer → "not enough scans yet"), late-shipment drivers with counts, cuts under 30 orders show counts only, copy "were more often", never "caused" (AC-B3). Stations only, no person's name.
2. Inventory health (`/analytics/inventory`): on-hand value, turns, dead stock count and value (AC-C2), size-mix gaps with sales and stock share (seed: BC3001 Black 3XL +18.0 pts, Dusty Blue L −18.6 pts; the old G64000 Sand premise is gone), "not enough data" for style × color under 30 units (AC-C1), stockout exposure; Supplier trends section: unit cost by month, median lead days, suggestion linking to the lead-time setting when off by > 3 days (AC-C5).
3. AC-B/C-screen1: when `hasEnoughHistory` is false, one whole-screen "not enough history yet" state (AC-A7 banner pattern), in addition to per-widget notes.
4. Designs list gains a lifecycle column (stage from `analytics.designLifecycle`; market trend wins when present) (AC-C4).
5. Export CSV on each view with the same filters (AC-E6).
6. Today panel (AC-E2): for `finance.read` roles, up to 5 ranked actions with $ impact and one button each, wording rendered from `kind` + `params` in the user's language, the button opens `href` and fires `today.recordActionClick` without blocking navigation; `steady` → "Nothing needs attention right now". The panel is hidden when `generatedAt` is null (not built yet). Gate with `can("finance.read")` and don't call the query otherwise. Roles without `finance.read` don't see the panel and Today still loads for them (floor roles use Today).
7. B-225: the Today greeting date follows the UI language; the ban check fails on a planted raw call and passes on the tree.
8. en and es everywhere; money and numbers through `Intl`; points for percent-point changes.

9. (Added 2026-09-30 from T-A9's report) D2 actions carry `params.designName` when a profit-bridge mover exists: `digest-copy.ts` renders "{{mover}} moved your profit the most" (es too), matching the email.

## Verification
- `cd invai-web && pnpm typecheck && pnpm lint && pnpm test && pnpm build 2>&1 | tail -n 40`; `pnpm i18n` clean.
- Browser on the shared dev stack: as `owner@desertbloom.test`, Operations, Inventory health, Designs and Today at 1440 and 390 px, en and es, screenshots under `/Users/bekbolsun/invai/.e2e-out/web/T-A7/`, looked at; click an action and show the click recorded (`today.actions` returns `clickedAt`). As `presser@` Today loads without the panel.
- Today is golden-path: run `pnpm e2e e2e/screens.smoke.spec.ts` once against the dev stack and report the result (the full E2E runs at the gate).

## Out of scope
- Backend or contract changes. B-223, B-224. PO form changes (AC-C3 is served by the backend split in A1). E2E spec edits (QA at the gate adds the two new routes to the smoke list).

## Budget
- About 4 hours. Escalate if blocked for more than about 30 minutes.
