# Review T-A6 r2: Profit v2 web (reviewer on Opus 5.5; author web-engineer)
Verdict: **approve**

## r1 finding 1 (money split mid-number at 390 es): fixed
- `kpi-tile.tsx:28`: `break-words` replaced by `whitespace-nowrap text-xl sm:text-2xl`. All 6 KPI grids are now `grid-cols-1 sm:grid-cols-2 …`, so each tile gets the full row below `sm`.
- Screenshots checked: `r2/contribution-es-390.png` shows "16.468,39 US$", "10.752,31 US$", "7100,03 US$" on one line each. `r2/why-es-390.png` shows "4173,84 US$", "5169,76 US$", "+995,92 US$", "+2434,97 US$", all whole. `r2/why-es-1440.png`: 5 tiles in one row, all unclipped (longest is "-1439,05 US$"), and the table is intact.

## Scope and ownership
- 81d27c5 touches 9 files: 7 in `features/finance/profit-v2/` (owned) and `src/lib/format.ts` + `format.test.ts` (already granted in r1). The tree is clean apart from other cards' work.
- The commit removes `formatPercentPoints` and its test. The helper was unused (grep: 0 hits in `src/`), and no Track A contract output has a percent-point change field (grep of `analytics.ts`/`finance.ts`). AC8's points rule has nothing to apply to, so it's still met. The 122 → 121 test count is that one removed test for the deleted helper, not a weakened check.

## Evidence I re-ran (invai-web @ 81d27c5)
| Command | Result |
|---|---|
| `pnpm lint` | 0 errors, 1 old warning (`src/content/markdown.test.ts`) |
| `pnpm test` | 19 files, 121 passed |
| `scan-test-weakening.sh invai-web 81d27c5~1` | 1 hit: removed `formatPercentPoints` assertion (dead helper deleted, see above). No skips, config or snapshot changes |
| `pnpm typecheck` | not re-run. Known and accepted: fails only at `digest-copy.ts:106` (T-A7) |

## Blocking findings
none

## Optional notes (non-blocking)
- `whitespace-nowrap` with no overflow guard can spill at in-between widths: `sm` 2-col, or `md:grid-cols-4` at about 768–1100 px with the sidebar open. My estimate: at 1024 es, "16.468,39 US$" in `text-2xl` (~180 px) is wider than a ~140 px content box, so it could overlap the next tile. The number never splits. This is outside the card's 1440/390 checks. For product-designer: consider `md:grid-cols-2 lg:grid-cols-4` or a smaller `md` size.
- The r1 note about losing orders showing Units 0 / $0.00 (backend data) still stands, for the tech lead.
