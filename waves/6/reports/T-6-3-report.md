# T-6-3: Profit — ad spend, export, drill-down — report

## Summary
Ad spend CRUD + CSV import screen, `finance.exportCsv` backend (wave 6 stub 7)
and web wiring (Recompute / Export CSV / drill-down to `orders`) on the Profit
page. Same filters as `finance.profit`, so the export always matches what's
on screen.

## Commits
- `invai-backend` `d5dacfe` — `finance.exportCsv`: `exportProfitCsv` in
  `modules/finance/service.ts` (same filters as `getProfit`, plus a totals
  row, via the existing `toCsv`/`objectKey`/`putObject` helpers), wired in
  `router.ts`, test added in `service.test.ts`.
- `invai-web` `f2ef447` — `/analytics/ad-spend` (list/add/edit/delete,
  CSV import with a template download and per-row errors), Profit page gets
  Recompute, Export CSV and a "Manage ad spend" link, drill-down navigates
  rows to `/orders` pre-filtered by period (and by channel for the channel
  dimension), nav entry, en/es keys by hand.

## Acceptance criteria
1. **Ad spend** — `/analytics/ad-spend`: filter by channel/date, add/edit/
   delete dialog, CSV import (`date,channel,amount,campaign,note`) reusing
   the existing `CsvImportDialog`, with a "Download template" link and a
   per-row error list.
2. **Profit includes ad spend** — unchanged backend behavior (already did,
   via `costSettings.adsAllocation`); added a **Recompute** button calling
   `finance.recompute` with a short-lived auto-refresh of the profit query.
3. **Export and drill-down** — **Export CSV** button calls the new
   `finance.exportCsv` with the screen's exact `dimension`/`period`, then
   downloads via `files.downloadUrl({ disposition: "attachment" })`.
   Drill-down: confirmed `orders.list`'s filters (`channel` array,
   `placedFrom`/`placedTo` — no `designId`/blank filter) before building.
   Rows now navigate to `/orders`: `day` dimension → that exact day,
   `channel` → channel + period, `design`/`blank` → period only (with an
   on-screen note, since `orders.list` has no design/blank filter yet — a
   real gap for whoever owns `modules/orders`/`contract/orders.ts` to close).
   `order` dimension keeps its existing breakdown sheet.
4. **Credits history** — skipped, T-6-4's path.
5. **Quality** — en/es added by hand; `Money`/cents formatters throughout;
   existing responsive components (`Page`, `DataTable`, dialogs) reused.

## Shared-tree collision (read before reviewing `invai-web`)
T-6-2's commit `c130bde` landed *while* I was reconciling `invai-web` main
(dirty from their concurrent, unworktreed session) and picked up my `nav.ts`
entry + `routeTree.gen.ts`'s `ad-spend` import without my actual route files
— a broken commit (`import ... from './routes/_app/analytics/ad-spend'` with
no such file). Fixed forward in `f2ef447` by adding the missing source +
i18n values rather than rewriting `c130bde`. `invai-backend`'s `d5dacfe` was
a clean cherry-pick from an isolated worktree, no collision. Recommend the
gate confirm `invai-web` `git log -p c130bde -- src/lib/nav.ts` was
intentional-looking noise only (it was) and that wave 7 work (already on
`main`, `3feb9ff`) didn't touch `modules/finance/**` or the web paths above.

## Verify
- `invai-backend`: `tsc --noEmit`, `biome check` — pass (one pre-existing,
  unrelated error in `modules/inventory/router.ts` re: `markPlaced`, not
  introduced by this card). `vitest run` on `modules/finance/`: 10/10 pass
  (incl. new `exportProfitCsv` test). Test DB `invai_test_t63`, dropped.
- `invai-web`: `tsc --noEmit` clean for my files (one pre-existing, unrelated
  error in `features/orders/order-actions.tsx`, `FlagCode` union, not mine).
  `biome check`, `vitest run` (76/76), `vite build` — pass.
- Browser pass on DB copy `invai_t63_copy` (api :3130, web :5133): logged in,
  added a $42.50 Etsy spend, imported a 2-row CSV (1 imported, 1 "Invalid or
  missing date"), ran Recompute, exported CSV from "By channel" and diffed it
  byte-for-byte against the on-screen totals (matched exactly), clicked the
  Etsy row and landed on `/orders?channel=etsy&from=...&to=...` pre-filtered
  correctly. 6 screenshots taken. DB copy and test DB dropped after.

## Known gaps / follow-ups
- `orders.list` needs a `designId`/`blankVariantId` filter for exact
  design/blank drill-down (currently period-only for those two dimensions).
- The pre-existing `modules/inventory/router.ts` (`markPlaced`) and
  `features/orders/order-actions.tsx` (`FlagCode`) type errors are unrelated
  to this card and were left as found.
