# Review of T-6-3 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: (backend/web engineer) on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-backend-review-t63` (worktree @ HEAD `3feb9ff`) `tsc --noEmit` | pass, 0 errors |
| `invai-backend-review-t63` `biome check src` | pass, 250 files, no issues |
| `invai-backend-review-t63` (@ `d5dacfe`, fresh migrated DB `invai_review_t63`) `vitest run src/modules/finance/` | pass, 10/10 (incl. new `exportProfitCsv` test) |
| Negative check: new export test copied onto parent `3b08f5a`, run standalone | fails as expected (`svc.exportProfitCsv` doesn't exist) — proves the test is real |
| `invai-web-review-t63` (worktree @ HEAD `f2ef447`, includes `c130bde`) `tsc --noEmit` | 1 pre-existing unrelated error (`order-actions.tsx:79`, `FlagCode` union missing `channel_edit_after_press`) — not introduced by this card |
| `invai-web-review-t63` `biome check src` | pass, 133 files, no issues |
| `invai-web-review-t63` `vitest run` | pass, 76/76 |
| `invai-web-review-t63` `vite build` (@ HEAD `f2ef447`) | pass, exit 0 |
| `invai-web-review-t63` `vite build` (@ `c130bde` alone) | also exit 0, but only because TanStack Router's vite plugin silently regenerates `routeTree.gen.ts` from the files on disk at build time (masking the missing `ad-spend.tsx`) — see note below |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend origin/main` | hits found, all outside T-6-3's files (see below) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web origin/main` | hits found, all outside T-6-3's files (see below) |
| Browser/API pass on DB copy `invai_t63_browsercopy` (api :3192, web :5192, `REDIS_URL` db 10): add ad spend, CSV import w/ 1 bad row, recompute, export CSV | all pass, see below |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Ad spend list/add/edit/delete + CSV import w/ template + error rows | Yes | `POST /finance/ad-spend` created a $42.50 Etsy entry; `POST /finance/ad-spend/import` on a 2-row CSV (1 good, 1 `not-a-date`) returned `{"created":1,"failed":1,"errors":[{"row":3,"message":"Invalid or missing date"}]}` — matches the report exactly |
| 2. Profit includes ad spend; Recompute calls `finance.recompute` | Yes | `POST /finance/recompute` queued a job; worker processed it; `adsCost` in the resulting `by channel` rows includes ad spend (e.g. etsy `85703`¢ = my $42.50 + seed spend) |
| 3. Export CSV matches on-screen, drill-down navigates correctly | Yes | Downloaded export byte-matches the JSON totals to the cent (e.g. etsy revenue `687571`¢ → CSV `6875.71`; total net `558545`¢ → CSV `5585.45`; total margin `30.44%` → CSV `30.4`). `profit.tsx`'s `ordersSearchFor` produces `{channel, from, to}` for the channel dimension, which matches `/orders`' own `searchSchema` (`channel: z.enum`, `from`/`to`: `z.iso.date()`) — the route wraps `search.channel` into an array before calling `orders.list`, so the single-value URL param is correct, not a bug |
| 4. Credits history | Skipped, correctly deferred to T-6-4 | n/a |
| 5. Quality: en/es, 390px, cents | Yes | `en.ts`/`es.ts` diffs both add exactly 30 keys; `Money`/cents formatters used throughout `profit.tsx` and `ad-spend.tsx`; no raw hardcoded UI strings found outside `t()` calls (only i18n fallback default text) |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed — backend: `modules/finance/router.ts`, `service.ts`, `service.test.ts`; web: `features/finance/ad-spend.tsx`, `routes/_app/analytics/ad-spend.tsx`, `routes/_app/analytics/profit.tsx`, `src/i18n/{en,es}.ts`. All within the card's owned globs.
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened — the weakening scan flagged hits repo-wide (vs `origin/main`, which spans several other wave-6/7 cards), but nothing inside `modules/finance/**`, `features/finance/**`, or `routes/_app/analytics/**`. The one new backend test (`exports the profit summary to CSV`) was confirmed to fail on pre-change code.
- [x] Tenancy (`withTenant`, RLS), idempotency, money in cents, en/es text — `exportProfitCsv`/`getProfit` both run inside `withTenant(tenant.companyId, ...)`; no new tables added, so no new RLS surface; money handled entirely in integer cents end-to-end (backend divides by 100 only when formatting for CSV text, `toFixed(2)`); no side effects requiring idempotency keys (export just materializes a read-only CSV to S3).
- [x] Decisions recorded where needed — the known `orders.list` design/blank filter gap is documented on-screen and in the report; no decision doc needed for a documented, non-blocking limitation.

## CSV injection
`exportProfitCsv` builds rows via the shared `toCsv()` helper (`invai-backend/src/lib/csv.ts`), which runs every cell through `neutralizeFormula()` — prefixes a cell starting with `=`, `+`, `-`, `@`, tab or CR with `'` unless it's a plain number. In practice the profit export's only text cells are `key`/`label`, which come from a fixed dimension enum (channel/day/design/blank/order — never free-text user input), so there is no live injection vector today, but the defense-in-depth guard is correctly wired and would catch it if a future dimension used free text.

## `c130bde` + `f2ef447` (the shared-tree collision)
Confirmed the story in the report: `c130bde` (T-6-2) has `nav.ts` and `routeTree.gen.ts` hunks referencing `./routes/_app/analytics/ad-spend`, a file that doesn't exist at that commit — a real, broken commit in isolation. `f2ef447` (T-6-3, six minutes later) adds the missing route file and its `features/finance/ad-spend.tsx` counterpart. At **HEAD** (`f2ef447`, which is `c130bde` plus this fix), `tsc`, `biome`, `vitest`, and `vite build` are all clean — main is not broken today. One caveat for future bisects: `vite build`/`dev` running TanStack Router's file-based-routing plugin auto-regenerates `routeTree.gen.ts` from whatever route files exist on disk, so checking out `c130bde` alone and running `build` silently "fixes" the broken import rather than surfacing it — anyone needing to verify `c130bde` in isolation should diff `routeTree.gen.ts` against `git ls-tree` of `src/routes`, not just run the build.

## Cross-card note for the tech lead (not a T-6-3 finding)
Wave 7's `3feb9ff` (T-7-1/T-7-2) added `exportedAt` to the `shipments` schema and a new `refund_events` table in `src/db/schema/*.ts`, but **no drizzle migration was generated** for either — `drizzle/` still ends at `0019_production_bin_name_archived.sql`. The shared dev DB (and any fresh copy of it) is missing both, so any insert into `shipments` at current backend HEAD fails with `column "exported_at" does not exist`. I hit this while setting up a clean test DB for T-6-3 and had to manually patch it around to test the browser flow. This isn't T-6-3's bug (it doesn't touch shipping schema) and I didn't block on it, but the wave gate should not run golden-path E2E until T-7-1 generates the missing migration.

## Optional notes (not blocking)
- `vite build` reports two chunks over 500kB (`BarChart`, `index`) — pre-existing, not from this card.
- Worth a follow-up ticket: `orders.list` still has no `designId`/`blankVariantId` filter, so the `design`/`blank` profit dimensions can only drill down to a period, not the exact rows — already flagged on-screen and in the report as a known gap for whoever owns `modules/orders`.
