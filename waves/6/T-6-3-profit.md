# T-6-3: Profit: ad spend, export, drill-down
Scope: item 8. Backlog: B-88.

## Owned paths
- web: the analytics routes, `settings/costs.tsx`, `features/finance/**`, own i18n keys
- backend: `modules/finance/**`, only if the procedures need fixes
- tests

## Acceptance criteria
1. **Ad spend:** a screen to list, add, edit and delete entries by channel and date range, and a CSV import with a template and error rows.
2. **Profit:** includes ad spend per the allocation setting. "Recompute" calls `finance.recompute`.
3. **Export and drill-down:** CSV export of the profit views via the new `finance.exportCsv` (exact stub in `wave.md` — no export endpoint exists today; same filters as `finance.profit` so the export matches what's on screen). Each row drills down to its orders by linking to the orders list pre-filtered by that row's dimension key and period — confirm `orders.list`'s filters actually cover a blank/design filter before building this; `ProfitSummary` rows are keyed by dimension, not by an `orderIds` array.
4. **Credits history:** AI-credit history (`ai.credits.ledger`) shown in billing. That's T-6-4's path, so skip it here.
5. **Quality:** en and es, 390 px, money shown from cents.

## Verify
Run tsc, lint, test and build. Browser pass on a DB copy: add ad spend, import a CSV with 1 bad row, see profit change, drill down, export. At most 6 screenshots.
