# T-P3-3: Spanish money shows a thousands separator on 4-digit amounts (invai-ui)

| Field | Value |
|---|---|
| Wave | P3 |
| Scope ref | `always-in-scope: bug` (es number display; PM rank 1, `product/backlog-ranking.md` 2026-10-01) |
| Spec | `waves/A2/reviews/T-A6-product-designer-r1.md` (lines 13–25) |
| Owner | product-designer |
| Reviewer | reviewer (opus) |
| Co-reviewers | none (shared formatter fix, no new component) |
| Risk flags | ui |
| Model | sonnet |
| Depends on | starts after the P1+P2+P3 push |

## Owned paths (edit)
- `invai-ui/src/app/money.tsx` and its test

## Read-only paths
- `invai-web/**`, `invai-floor/**` (they have their own `Intl.NumberFormat` call sites: `invai-web/src/lib/format.ts`, `features/finance/order-profit.tsx`, `features/analytics/shared.tsx`, `components/digest/digest-copy.ts`; list which ones need the same fix in the report, the tech lead cards them for web-engineer)

## Acceptance criteria
1. Under `es`, `1234.56` USD formats with a group separator (`1.234,56 US$` style) like 5+ digit amounts already do; set `minimumGroupingDigits: 1` (check the installed TS/Intl types accept it) for every locale, so `en` is unchanged (`$1,234.56`).
2. Unit tests pin en and es for 3-, 4- and 7-digit amounts and a negative 4-digit amount.
3. The formatter cache key still distinguishes locale and currency.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test 2>&1 | tail -n 40` in `invai-ui`; `pnpm typecheck && pnpm build 2>&1 | tail -n 20` in `invai-web` and `invai-floor` (consumers still build).
- Report the list of web/floor formatters that bypass `money.tsx` with file:line.

## Rules
- Role file `.claude/agents/product-designer.md`; `team/agent-brief.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/product-designer/`.
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** No servers needed; if you start any, record PIDs and stop them.
- Report (≤ 60 lines) to `invai-docs/waves/P3/reports/T-P3-3.md`.

## Round 2 (tech lead, from `reviews/T-P3-3-reviewer-r1.md`)
1. **Blocking:** add en tests for a 3-digit amount (`$123.45`) and a negative 4-digit amount (`-$1,234.56`), locale passed explicitly.
2. Ruling: replace the custom `formatToParts` re-grouping with the standard `useGrouping: "always"` (typed in TS 7's ES2023 lib; the reviewer showed it is byte-identical in 1,530 cases). Less custom code on every money value. Fix the code comment that says there is no native way. All tests from round 1 stay.
