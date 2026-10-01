# Report: T-A6 Profit v2 screens

Author: web-engineer on Claude Opus 5.5

## Built
- Six new views on `/analytics/profit?view=...` (contribution, losing, leakage, shipping, why, breakeven), added as a view switcher; default (no `view` param) is the untouched original by-day/by-order table, so the golden path is unchanged. (files: `invai-web/src/routes/_app/analytics/profit.tsx`, `invai-web/src/features/finance/profit-v2/**`)
- Export CSV on every new view, `analytics.export` with that view's own filters. (`profit-v2/export-csv.ts`)
- "{{n}} orders aren't in these numbers yet" banner (AC-A7) on Contribution and Leakage. (`profit-v2/banners.tsx`)
- Settings → Costs: "Fixed monthly costs ($)" field with the labor-already-counted hint, wired to `CostSettings.fixedMonthlyCents`. (`invai-web/src/routes/_app/settings/costs.tsx`)
- B-226 fix: old Profit KPI grid was `xl:grid-cols-6`; a Spanish currency string (non-breaking "16.468,39 US$") overflowed at that width. Capped the grid at 3 columns (matches the 4–5 columns the new views use safely, verified in screenshots) and added locale-aware `formatMoneyShortLocale`/`formatRatioPctLocale`/`formatPctNumberLocale`/`formatPercentPoints` to `format.ts`; switched the chart axis, tooltip and Margin KPI to them.
- Fixed a pre-existing (not just new) mobile bug: the Tabs row had no horizontal-scroll wrapper and would have pushed the whole page wider at 390px; wrapped both tab bars in the existing `-mx-1 overflow-x-auto px-1` pattern (same as `orders/index.tsx`).
- `scripts/i18n-extra-en.json`: added `profit.dim.sku` and the `profitV2.by.*`/`profitV2.groupBy.*` dynamic-key entries (not in the card's literal owned-paths list, but required infra for `pnpm i18n` to find template-literal keys — flagging per respect-ownership).

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| AC1 (6 views + export) | Yes | Screenshots; each Section has an Export CSV button calling `analytics.export` |
| AC-A1 (CM3 = Net, to the cent) | Yes | Real seed, 30-day period: `analytics.unitEconomics` totals.cm3 = 527973; `finance.profit` totals.net = 527973 (curl via typed client) |
| AC-A2 (losing orders: order #, CM2, biggest cost) | Yes | `losing-en-1440.png`: `#3104008399`, CM2 `-$60.30`, "Blanks -$29.35"; backend already excludes positive-CM2 (T-A3, not retested here) |
| AC-A3 (zero labeled shipments state) | Yes | Confirmed via API with a 2015 period (labeledOrders:0 → `EmptyState`, not a table); real period screenshot shows the normal state (270 labeled orders in seed) |
| AC-A6 (no fixed costs prompt; $2,500 → numbers) | Yes | `breakeven-en-1440.png` (prompt, linked to Costs), `breakeven-set-en-1440.png` (set to $2,500: break-even 153 orders/mo, pace 316, operating pace +$2,669.76); setting restored to null after |
| AC-A7 (banner, never silent partial) | Yes | `contribution-es-1440.png`, `losing-es-1440.png`, `leakage-es-1440.png`: "39 pedidos todavía no están en estos números" |
| B-226 (es 1440 no clipping; locale axes/percents) | Yes | `overview-es-1440.png` before/after; all KPI values one line, chart axis "340 $ / 255 $ / …" |
| en/es, finance.read gate | Yes | 73/73 new keys translated (real Spanish, not machine strings); `designer@` → API `FORBIDDEN` (403) and UI shows "No access" with nav link hidden |
| Sample-data label | Inherited | `app-frame.tsx`'s `me.org.demo` badge wraps every page already; nothing added here |

## Checks I ran
| Repo | Command | Result |
|---|---|---|
| invai-web | `tsc --noEmit -p .` | clean |
| invai-web | `biome check .` | 1 pre-existing warning, unrelated file (`src/content/markdown.test.ts`) |
| invai-web | `vitest run --passWithNoTests` | 19 files, 122 tests passed |
| invai-web | `vite build` (VITE_API_URL set) | built in ~1.6s |
| invai-web | `pnpm i18n` | 0 missing es keys of mine; 8 pre-existing unrelated "extra es keys" left untouched |
| invai-web | `playwright test e2e/screens.smoke.spec.ts` | 2 passed, no console/request errors |
| invai-web | `playwright test e2e/golden-path.spec.ts` | 10 passed, step 10 (my area) passed; step 11 (AI drafts, not mine) failed — see Known gaps |

## Exercised for real
- Shared dev API :3000 (PID 40059→40067) + web :5173 (PID 40078→40086), started and stopped by me; shared dev DB not reset.
- 37 Playwright screenshots under `/Users/bekbolsun/invai/.e2e-out/web/T-A6/` (1440+390, en+es, plus a dark sample and the break-even $2,500 state); I looked at all of them.
- Refused case: `designer@desertbloom.test` calling `analytics.unitEconomics` → `FORBIDDEN`/403 (typed-client script); browser confirms no "Profit" nav link and "No access" body.

## Decisions
- Kept the old by-day/by-order table as the default view rather than replacing it with Contribution, to preserve `e2e/golden-path.spec.ts` step 10's literal "Net profit" text assertion — the new views are reached via a view switcher, not a redesign of the landing state.
- Shared one page-level period (7/30/90) selector across all 7 views instead of per-view period pickers; each new view keeps its own `dimension`/`groupBy`/`by` selector as local state (not URL-persisted) to keep the search schema small — a v1 simplification, not a gap against any AC.
- "Why it changed" has no UI override for `basePeriod`; uses the contract's default (equal-length preceding period) only.

## Known gaps and follow-ups
- `e2e/golden-path.spec.ts` step 11 ("AI listing draft") fails consistently in my environment: "Claude is writing this draft…" never resolves within 60s. Root cause: I started only `dev:api` + `dev` (per the card), no `worker` process, so the AI-draft BullMQ job never completes. Not a regression — step 10 (Profit) passed, and I touched nothing under `src/ai`/`src/modules/ai`/listings. Flagging for whoever next runs the full gate with a worker running.
- `scripts/i18n-extra-en.json` isn't in my card's literal owned-paths list; I added 2 lines there (my keys only) since dynamic template-literal `t()` keys need it to reach `pnpm i18n`'s extractor. Precedent: `digest.costLine.*` already does the same for a different namespace.

## Blocked by other owners
- None.

## Processes and data
- Stopped: API dev server (40059/40067), web dev server (40078/40086). Shared dev DB: untouched (CostSettings.fixedMonthlyCents set to $2,500 during AC-A6 verification, restored to `null` immediately after, confirmed via a follow-up read).

## Round 2 (SHA 81d27c5)
- Fix (reviewer r1 blocking): `kpi-tile.tsx` swaps `break-words`→`whitespace-nowrap` (+ smaller
  base size, `sm:text-2xl`); all 6 KPI grids go single-column below `sm`. Money now shrinks/wraps
  as a whole unit, never mid-number.
- Designer r1 non-blocking: dropped unused `formatPercentPoints` (+ its test) — no Track A view
  compares two margin percentages; left the other 2 notes (backend `losingOrders` data gap,
  full-page "No access" gate) as-is, out of my small-fix scope.
- Checks: `pnpm typecheck` fails only at `digest-copy.ts:106` (T-A7, not mine, confirmed);
  `pnpm lint` 1 pre-existing unrelated warning; `pnpm test` 19 files/121 passed (one fewer: removed
  the dropped function's test); `VITE_API_URL=http://localhost:3000 pnpm build` succeeded.
- Verified in browser: started `invai-backend` `dev:api` (REDIS_URL=…/10, PID 46970→ restarted by
  tsx watch from backend-engineer's concurrent digest WIP, came back up each time) + `invai-web`
  `dev` (PID 47025) against the existing shared Postgres/Valkey/MinIO. Retook
  `contribution-es-390.png`, `why-es-390.png`, `why-es-1440.png` in
  `.e2e-out/web/T-A6/r2/` and looked at all three: money is one line in every tile, no horizontal
  scroll, 1440 layout unaffected.
- Stopped: PIDs 46970 (api), 47025 (web); ports 3000/5173 confirmed free. Shared dev DB untouched.
