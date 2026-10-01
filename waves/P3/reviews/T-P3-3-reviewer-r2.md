# Review: T-P3-3 es money grouping, round 2
Reviewer: reviewer on Opus 5.5. Author: product-designer. Commit: invai-ui `2e3519d` (on top of r1 `0649165`).

## Verdict: approve

## Round 2 items
1. Blocking r1 finding fixed: `money.test.ts:41-47` adds `formatMoney(12345,"USD","en")` → `$123.45` and `formatMoney(-123456,"USD","en")` → `-$1,234.56`, locale passed explicitly.
2. Ruling done: `money.tsx` drops the `formatToParts` re-grouping and `groupSeparator`; the cached formatter now uses `useGrouping: "always"` with no cast. The "no native way" comment is replaced by an accurate one.

## Test integrity
- Test diff is additions only (+8 lines); no round 1 test removed or loosened; no skip/only.
- Mutation: removing `useGrouping: "always"` from a HEAD copy in /tmp fails 3 tests (es 4-digit, es negative 4-digit, cache AC3). So the tests still prove AC1.

## Evidence I re-ran
| Repo | Command | Result |
|---|---|---|
| invai-ui | `pnpm typecheck && pnpm lint && pnpm test` | clean; biome 54 files OK; 5 files / 32 tests passed, exit 0 |
| invai-web | `pnpm typecheck` | clean, no errors |
| invai-floor | `pnpm typecheck` | clean, no errors |
| invai-ui | mutation, `useGrouping` line deleted (copy in /tmp) | 3 failed / 11 passed (expected red) |

## Checks
- [x] Only owned paths: `src/app/money.tsx`, `src/app/money.test.ts`; working tree clean
- [x] Nothing outside scope; money still integer cents; no new strings
- [x] Tenancy, idempotency: n/a

## Blocking findings
none

## Optional notes
none. No servers started; temp dir removed.
