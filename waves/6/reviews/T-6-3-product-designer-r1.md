# Review of T-6-3 (round 1)

- Reviewer: product-designer on Sonnet 5
- Author: (backend/web engineer) on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-web-review-t63` (worktree @ HEAD `f2ef447`) `tsc --noEmit` | 1 pre-existing unrelated error (`order-actions.tsx:79`, `FlagCode`), not from this card |
| `invai-web-review-t63` `biome check src` | pass, 133 files |
| `invai-web-review-t63` `vitest run` | pass, 76/76 |
| `invai-web-review-t63` `vite build` | pass |
| `git diff c130bde f2ef447 -- src/i18n/en.ts` / `es.ts` | +30 keys each, 1:1 |
| Read `src/features/finance/ad-spend.tsx`, `src/routes/_app/analytics/ad-spend.tsx`, `src/routes/_app/analytics/profit.tsx` in full | see below |
| Browser/API pass on DB copy (`invai_t63_browsercopy`, api :3192, web :5192) — add ad spend, CSV import w/ 1 bad row, recompute, export | all worked, see the `reviewer` file's evidence table for the exact requests/responses |

## Acceptance criteria (design/UX lens)
| # | Met? | Evidence |
|---|---|---|
| 1. Ad spend list/add/edit/delete, CSV import w/ template + per-row errors | Yes | `AdSpendDialog` reuses the existing `Field`/`NativeSelect`/`Dialog` primitives; the import flow reuses the existing `CsvImportDialog` + `RowErrors`/`ReportStats` components (same pattern as the catalog CSV import), so the error list, "Download template" link and per-row messaging match the rest of the app rather than inventing a new pattern |
| 3. Drill-down | Yes | Clicking a row navigates to a pre-filtered `/orders` list; where the filter can't be exact (design/blank dimensions), an on-screen note (`Info` icon + `profit.incomplete`-style text) explains the gap in plain language rather than silently showing wrong or unfiltered data |
| 5. Quality: en/es, 390px, money from cents | Yes | Every new string goes through `t()` with an English fallback and a matching key in both `en.ts` and `es.ts` (30/30, no orphans). All monetary values render through the shared `Money` component (cents in, formatted out) — no `.toFixed`/manual `$` string-building in the JSX I read. The screens use the existing `Page`/`Card`/`DataTable`/`Dialog` components, which are already verified responsive at 390px elsewhere in the app; nothing in the new markup introduces a fixed-width layout, a horizontal-scrolling table without a wrapper, or a dialog wider than the existing dialog primitive allows. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed — `features/finance/**`, `routes/_app/analytics/**`, i18n keys. Matches the card's owned globs.
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened (see the `reviewer` file for the weakening-scan detail; nothing in T-6-3's files)
- [x] en/es text present for every new string, money in cents throughout
- [x] Decisions recorded where needed — the design/blank drill-down gap is surfaced to the user on-screen (not silently swallowed), which is the right call for a known limitation rather than a hidden one

## Optional notes (not blocking)
- Consider a toast or inline confirmation after CSV import completes (beyond the error list) so a fully-successful import gets the same acknowledgment pattern as add/edit/delete — minor, and consistent with existing `CsvImportDialog` behavior elsewhere, so not a new gap introduced by this card.
- The "Manage ad spend" link on the Profit page is text-only (`text-sm font-medium text-primary hover:underline`); fine for now, but a `Button variant="link"` would match the visual weight of the adjacent Recompute/Export buttons a bit more closely. Cosmetic only.
