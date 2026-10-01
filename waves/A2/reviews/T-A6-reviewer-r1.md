# Review T-A6 r1: Profit v2 web (reviewer on Opus 5.5; author web-engineer)
Verdict: **changes-required** (1 blocking finding)

## Blocking
1. `invai-web/src/features/finance/profit-v2/kpi-tile.tsx:27`: `break-words` on the `text-2xl` value (the B-226 guard) breaks money in the middle of the number at 390 px in Spanish. `contribution-es-390.png` shows "16.468, / 39 US$", "7100,0 / 3 US$", "5169,7 / 6 US$". `why-es-390.png` shows "+1003, / 64 US$" and "-1441,3 / 0 US$". Failure: on a phone, an owner reads the first line and takes "5169,7" or "+1003," as the whole value. That's a wrong figure, and it's the same bug class B-226 folds in; the card needed 390 es screenshots checked for this. Fix: keep money on one line (`whitespace-nowrap`), use a smaller value size or one tile per row below `sm`, then retake the 390 es shots.

## Evidence I re-ran (invai-web @ f9124ac, clean tree)
| Command | Result |
|---|---|
| `pnpm typecheck` | exit 1: `src/components/digest/digest-copy.ts:106` TS2366, **not T-A6**. The file isn't in f9124ac; it comes from uncommitted T-A10 WIP in the symlinked `invai-contracts` (`src/contract/today.ts` M). It's T-A7's digest-copy grant; must be green by the gate |
| `pnpm lint` | 0 errors, 1 old warning (`src/content/markdown.test.ts`) |
| `pnpm test` | 19 files, 122 tests passed |
| `pnpm build` | fails only on the required `VITE_API_URL` guard. `VITE_API_URL=http://localhost:3000 pnpm build` built OK |
| `scan-test-weakening.sh invai-web f9124ac~1` | no hits |
| en/es flatten of generated `en.ts`/`es.ts` | 73 T-A6 keys, 0 missing in es (only `profit.dim.sku` = "SKU" is the same). `i18n-es-missing.json` is gitignored and older than the commit (13:34 vs 13:51) |

## Acceptance criteria
| # | Status | Evidence |
|---|---|---|
| 1 views + CSV | met | 6 views wired. Each `exportCsv.run` passes the same period/channel/dimension/by/groupBy as its query; only the display `limit` is dropped. The CSV comes from `analytics.export` → `files.downloadUrl` (attachment) |
| AC-A1 parity | met | `contribution-es-1440.png` CM3 5169,76 US$ = `overview-es-1440.png` Ganancia neta 5169,76 US$. The report also gives 527973 = 527973 from the API |
| AC-A2 | met (UI) | `losing-en-1440.png`: order #, CM2, biggest cost line, all CM2 negative |
| AC-A3 | met | `shipping-margin-view.tsx:98`: `labeledOrders === 0` shows an EmptyState with the exact copy (the report proved it with a 2015 period) |
| AC-A6 | met | `break-even-view.tsx:45`: prompt, a link to `/settings/costs`, no number; `breakeven-set-en-1440.png` shows the numbers. Costs: blank → null, invalid input blocks Save, hint text present |
| AC-A7 | met | The banner is on all 3 outputs that carry `ordersWithoutProfitLine` (unitEconomics, losingOrders, leakage) and hides at 0 |
| B-226 | partial | 1440 es: fixed (3-column grid, locale axis "340 $", "31,4 %"). The fix causes finding 1 at 390 |
| en/es, Intl, points, gating | met | Money goes through `Money`/`Intl`. `formatPercentPoints` gives "+6,9 pts"; `format.test.ts` +49 lines. Nav `permission: "finance.read"` (`nav.ts:224`), `designer-no-access.png`, and the report shows FORBIDDEN on the API |
| sample label | met | "Demo" badge in every screenshot |

## Checklist
- Ownership: all 18 paths are owned or granted (`i18n-extra-en.json`, wave.md Grants, 2026-09-30, template-literal keys only). No new route, so `routeTree.gen.ts` is unchanged.
- Buyer PII: the losing-orders CSV/UI carries the shop's order number only (the contract comment calls this allowed). Tenancy, idempotency and migrations: n/a (web only, no contract change).
- Golden path: the default view is the old table, so step 10's text still holds. E2E is left to the gate.

## Optional notes (non-blocking)
- `losing-en-1440.png`: all 8 losing orders show Units 0, Revenue $0.00, Design "—". The web mapping matches the contract fields, so this is backend data (T-A3 `losingOrders`, probably cancelled or refunded orders). Tech lead: worth checking before shops see it.
- The period select moves from the toolbar to the header between the default view and the v2 views. For product-designer.
