# Review of T-6-3 (round 1)

- Reviewer: data-analyst on Sonnet 5
- Author: (backend/web engineer) on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-backend-review-t63` (@ `d5dacfe`, fresh migrated DB `invai_review_t63`) `vitest run src/modules/finance/` | pass, 10/10 |
| Negative check: new `exportProfitCsv` test copied onto parent commit `3b08f5a`, run standalone | fails (function doesn't exist yet) — confirms the test is real evidence, not a tautology |
| Read `src/modules/finance/service.ts` (`exportProfitCsv`, `profitCsvRow`) and `src/lib/csv.ts` (`toCsv`, `neutralizeFormula`) in full | see below |
| Read `src/modules/finance/profit.ts` (`allocate`, `allocateAdSpend`) | unchanged by this card; confirmed sound (largest-remainder allocation, no cent leakage — see below) |
| Browser/API pass on DB copy `invai_t63_browsercopy` (api :3192): added a $42.50 Etsy ad-spend entry, imported a 2-row CSV (1 clean, 1 bad date), ran `finance.recompute`, pulled `finance.profit` and `finance.exportCsv` for the same filters and diffed them | byte-exact match, see below |

## Money math
- **Cents everywhere.** `AdSpendInput.amount` is cents in the contract (`Cents` schema); the create call I ran (`{"amount":4250}`) stored and echoed back `4250`, not `42.50` — no float amount ever touches the wire or the DB.
- **Export transcription is loss-free and correct.** `profitCsvRow` divides each money column by 100 with `.toFixed(2)` only at the CSV-text boundary; it never touches the underlying cents used for aggregation. I confirmed this end to end: `finance.profit` returned `etsy.revenue = 687571`¢, `adsCost = 85703`¢, and `totals.net = 558545`¢; the CSV from `finance.exportCsv` for the identical filters read `6875.71`, `857.03`, and `5585.45` for the same rows — exact, to the cent, across all 4 channel rows plus the totals row.
- **`marginPct` conversion is consistent.** The API returns a 0..1 ratio (`0.30443828...` for the total); the CSV renders `30.4` (`(marginPct*100).toFixed(1)`), and the web page's `formatPct` uses the same ratio convention — no double-percent or decimal-shift bug.
- **Ad allocation itself is untouched by this card** (report and diff both confirm — `costSettings.adsAllocation` and `allocateAdSpend`/`allocate` in `profit.ts` are pre-existing). I read `allocate()` anyway since Recompute is now user-triggerable from the UI for the first time: it's a standard largest-remainder-method split (floor each share, hand out the leftover cents to the largest fractional remainders in order), which guarantees `sum(parts) === total` exactly — no pennies created or dropped when ad spend is divided across orders by revenue share or per-order count.
- **Totals row is additive, not recomputed independently.** `exportProfitCsv` appends `summary.totals` (already computed by `getProfit`) rather than re-summing the rows itself, so there's no way for the totals row to drift from the on-screen totals card — confirmed by the byte-exact diff above.

## CSV injection
`toCsv()` (`src/lib/csv.ts`) runs every cell through `neutralizeFormula()`, which prefixes any cell starting with `=`, `+`, `-`, `@`, tab, or CR with a `'` unless it parses as a plain signed number — the standard OWASP CSV-formula-injection guard. In this specific export the only text cells are `key`/`label`, both drawn from a fixed dimension enum (channel code, "TOTAL", a day string, or a design/blank/order label from existing catalog data) rather than raw ad-spend free text (`campaign`/`note` aren't exported), so there's no live injection vector in `finance.exportCsv` today. The guard is nonetheless correctly wired for any future export that does include free text.

## Acceptance criteria (money/data lens)
| # | Met? | Evidence |
|---|---|---|
| 2. Profit includes ad spend; Recompute → `finance.recompute` | Yes | Recompute button calls the existing job-backed procedure; verified the job actually ran (worker log) and `adsCost` reflected the newly-added spend on the next `finance.profit` read |
| 3. Export matches on-screen exactly | Yes | See byte-exact diff above; same filters (`dimension`, `period`) passed to both `finance.profit` and `finance.exportCsv` |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`modules/finance/router.ts`, `service.ts`, `service.test.ts`)
- [x] Nothing outside scope — allocation/fee logic untouched, only the new export function added
- [x] Tests exercise the behavior, and none were weakened — new test asserts the CSV header, every money column, and the totals row against the live `getProfit` output (not a hardcoded fixture that could drift silently)
- [x] Money in cents throughout; no float arithmetic on money anywhere in the diff
- [x] Decisions recorded where needed — n/a, no new decision required

## Optional notes (not blocking)
- `exportProfitCsv` recomputes `getProfit` fresh rather than reading a cached/materialized result — correct for matching what's on screen right now, but means Export and the visible table can theoretically read at slightly different instants if data changes between the two calls (e.g. a webhook lands mid-click). Not observable in practice given profit is itself a periodically materialized view, and not worth adding a shared-snapshot mechanism for.
