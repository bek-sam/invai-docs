# Report: T-A7 Web Operations, Inventory health, Designs lifecycle column, Today actions panel
Author: web-engineer on Opus 5.5

Card: T-A7 Owner: web-engineer Scope ref: `product/scope.md#mvp-in` items 5, 6, 14
SHAs (invai-web, main): c756f61, e80298e, a33ffc7, e206b76 (QA's 3b6939e sits between mine, not authored by me)

## Built
- `digest-copy.ts`'s exhaustive switch gained D9-D13's six action kinds (en/es), unblocking typecheck (files: `invai-web/src/components/digest/digest-copy.{ts,test.ts}`)
- `/analytics/operations` (AC-B1/B2/B3): reprint cost by reason/station/vendor, film waste by vendor, waits per step + bottleneck, press minutes vs. labor setting with a Settings→Costs suggestion, late-shipment drivers ("were more often", counts-only under 30 orders) (files: `src/routes/_app/analytics/operations.tsx`, `src/features/analytics/operations-view.tsx`)
- `/analytics/inventory` (AC-C1/C2/C5): on-hand/turns, dead stock, size-mix gaps (AC-C1 "not enough data" per style×color), stockout exposure, plus a Supplier trends section with a lead-time suggestion (files: `src/routes/_app/analytics/inventory.tsx`, `src/features/analytics/{inventory-health-view,supplier-trends-view}.tsx`)
- AC-B/C-screen1 "not enough history yet" banner (`NotEnoughHistoryBanner`) on both screens, plus per-widget notes
- Designs list lifecycle badge (AC-C4): stage, market trend wins when present; gated on `finance.read` so other roles never call `analytics.designLifecycle` (file: `catalog/designs.index.tsx`)
- Nav: Operations, Inventory health under Analytics, `finance.read`-gated (`lib/nav.ts`)
- Today actions panel (AC-E2): up to 5 ranked actions with $ impact, wording via `digestActionText`, button fires `recordActionClick` without blocking nav, "Opened" indicator, steady-week empty state; hidden when `generatedAt` is null or on `NOT_IMPLEMENTED` (file: `features/today/actions-panel.tsx`, mounted in `routes/_app/index.tsx`)
- B-225: greeting date now follows UI language (`greetingDateLocale()`, local copy since `format.ts`'s `dateLocale()` isn't exported); repo-wide Vitest ban on raw `toLocaleDateString(undefined`/`toLocaleString(undefined` (`src/lib/date-locale-ban.test.ts`, via `import.meta.glob` raw text — no `@types/node` in this app)
- Export CSV on Operations, Inventory health and Supplier trends (AC-E6), same pattern as T-A6's, copied not imported per the card
- KPI tile / mini-table / banner / export-CSV patterns copied into `src/features/analytics/shared.tsx` from T-A6's read-only `profit-v2/` folder, not imported

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Operations | Yes | live curl + screenshots; reprint/film/waits/press/late-drivers all render real seed numbers |
| 2 Inventory health + Supplier trends | Yes | live curl + screenshots; AC-C1 confirmed live (6 style/colors "not enough data" at <30 units, larger groups show gapPts) |
| 3 AC-B/C-screen1 | Built, untriggered | `hasEnoughHistory: true` in current seed; banner code verified by reading the component, not seen rendering (no seed state to trigger it) |
| 4 Designs lifecycle | Yes | screenshot: "Growing"/"Declining" badges match live `analytics.designLifecycle` |
| 5 Export CSV | Built, not live-clicked | same `analytics.export` pattern as T-A6 (already proven); not separately re-clicked |
| 6 Today panel | Yes | screenshot + curl: 5 ranked actions, $ impact, real click recorded (`clickedAt` persists), "Opened" shown after a real UI click; presser sees Today with no panel, FORBIDDEN confirmed via curl |
| 7 B-225 | Yes | screenshot shows Spanish weekday/month; `date-locale-ban.test.ts` 3/3 pass (plants + real tree) |
| 8 en/es, Intl, points | Yes | es screenshots: money via `Money`/`formatMoney`, points via local `formatPoints`, no raw keys |

## Checks I ran
| Repo | Command | Result |
|---|---|---|
| invai-web | `tsc --noEmit` | clean |
| invai-web | `biome check src` | 0 errors, 1 pre-existing warning (not mine, `content/markdown.test.ts`) |
| invai-web | `vitest run` | 20 files, 131 tests passed |
| invai-web | `vite build` (VITE_API_URL=:3000) | built, no errors |
| invai-web | `python3 scripts/gen-i18n.py` | clean for my keys (pre-existing unrelated drift: 8 `extra es keys`) |
| invai-web | `playwright test e2e/screens.smoke.spec.ts` | 2/2 passed, "No screen issues" (includes `/analytics/operations`, `/analytics/inventory`) |

## Exercised for real
- Own API `PORT=3000 REDIS_URL=redis://localhost:6379/10`, web `vite` dev on :5173, against the shared dev DB (T-A9 had landed by the time I got here: `522433b T-A9: ...`)
- curl as owner: `today.actions`, `analytics.operations`, `.inventoryHealth`, `.supplierTrends`, `.designLifecycle` all return real seed data; `recordActionClick` idempotent (same `clickedAt` on repeat)
- Refused case: presser → `today.actions` → `FORBIDDEN` (`Missing permission finance.read`); presser → `today.summary` → 200 OK (Today still loads)
- Browser (Playwright, logged in as owner/presser): screenshots at 1440/390px, en/es, light/dark, under `/Users/bekbolsun/invai/.e2e-out/web/T-A7/` — looked at all of them, including a real UI click on an action confirming "Opened" appears after refetch
- Money never splits mid-number at 390px es (checked Operations, Inventory, Today)

## Decisions
- "Component tests with mocked query data" (card step 3): the repo has zero `.test.tsx` files anywhere; the established web-engineer pattern is pure-logic `.test.ts` plus real browser verification. Since T-A9 landed mid-card, I did full live verification instead (stronger evidence) rather than introduce a new untested-pattern test harness.
- Today panel hides on `NOT_IMPLEMENTED` the same as `generatedAt: null` (architect ruling only covered the latter explicitly) — both read as "not built yet" on the busiest screen.
- `opsV2.driverName.*` (not `opsV2.driver.*`) for the per-driver enum label: a same-path leaf+prefix key pair crashes `gen-i18n.py`'s `nest()`.

## Known gaps and follow-ups
- AC-B/C-screen1's whole-screen banner is built and code-reviewed-readable but never seen rendering live (current seed has `hasEnoughHistory: true` everywhere) — not exercised, only unit-level reasoning.
- `@invai/ui`'s `PageHeader` actions wrapper (`shrink-0`) clips (doesn't wrap or scroll) a 3-control actions row at 390px. Confirmed pre-existing on the already-reviewed `/analytics/profit` page too (not a regression here) — flagging for product-designer as a kit gap, same class as the earlier `StatCard` no-neutral-arrow gap.
- Export CSV button not re-clicked live on Operations/Inventory (same proven code path as T-A6's `finance.exportCsv`/`analytics.export`, already verified there).

## Blocked by other owners
- None.

## Processes and data
- Stopped: API (PID 53702, :3000), web dev server (PID 53723, :5173). Shared dev DB: not reset; left with a few benign `today_action_clicks` rows from live verification (idempotent, harmless).

## Round 2 (reviewer r1 + product-designer r1 fixes)
- SHA: invai-web fdce8c3
- AC9: `digest-copy.ts` `see_what_changed` now branches on `params.designName`, matching `render.ts`'s "D2 action.mover" en/es wording; falls back to plain text otherwise. 2 new unit tests (with/without mover).
- AC8: `operations-view.tsx` translated the backend's fixed sentinel/vocabulary values (no station, unknown/in-house vendor, 4 boolean late-driver values) via new `opsV2.*` keys; real station/vendor names pass through untouched; `channel` driver reuses existing `channel.*` keys. `scripts/i18n-extra-en.json` used for the dynamic-key (`driverValue.<driver>.<value>`) defaults, granted for this round.
- Non-blocking note (390px money overflow): `shared.tsx` `KpiTile` value now starts `text-lg` below `sm` (was `text-xl`), since this feature's grids stay 2-up at 390px unlike T-A6's profit grid. Confirmed by measuring the DOM: "12.441,31 US$" now sits 17px inside its card (was touching the edge).
- Checks: `pnpm typecheck && pnpm lint && pnpm test && pnpm i18n && pnpm build` all clean (133/133 tests, same 1 pre-existing lint warning in `content/markdown.test.ts`, no new "extra es keys").
- Browser: re-took `operations-es-1440`, `operations-es-390`, `inventory-es-390`, `today-es-1440` into `.e2e-out/web/T-A7/r2/`, looked at all four — "Desconocido" replaces "Unknown", all late-driver rows are Spanish, no page-level horizontal scroll at 390px (per-table `overflow-x-auto` scroll on the wide late-drivers table is pre-existing/intended, not a regression).
- Processes: API PID 56772 (:3000), web PID 56785 (:5173), both stopped. Shared dev DB: not reset.
