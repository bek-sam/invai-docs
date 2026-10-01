# Review of T-P4-5 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: qa-engineer on Sonnet 5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` / `pnpm lint` (invai-backend @ b5dcd89) | exit 0 / 457 files, no fixes |
| `pnpm vitest run src/modules/market --reporter=dot` x2 (main tree, sequential) | exit 0 both: 5 files passed, 1 skipped; 95 passed, 1 skipped; 0 "pool after end" lines |
| `pnpm vitest run src/modules/digest/digest.acceptance.test.ts --reporter=dot` | exit 0: 16 passed, 1 todo |
| `scan-test-weakening.sh invai-backend 8d69b64` (this commit only) | only hit: removed `toBe(-500)` (replaced by `toBe(500)`); no skip/only/retry/config |
| Worktree b5dcd89 with history.ts, analytics/{shared,finance,design,inventory}-service, finance/{service,refunds}.ts from e3c3cf7: `vitest run market.acceptance -t AC17` | exit 1: AC17 `expected -0.25 to be close to 0` (9/12-1), so it catches the old filter; hand-SQL passes (fixture check only, expected) |
| Same worktree: `vitest run digest.acceptance -t AC10` | **exit 0: passes on old product code** |
| Same worktree, throwaway probe: AC10 + `getProfit(week).totals.units === 1` | old code: exit 1 (`expected +0 to be 1`); new code: exit 0. Worktree removed after |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Partly | market AC17 fixture flips `is_reprint` on 3 already-counted units, yoy stays exact 0, red on old code; hand-SQL gains `reprints=3`. Digest AC10 fixture is one item (no sibling row) and the cost change is honest arithmetic, but its assertion does not show the reprinted unit counts (finding 1) |
| 2 | Yes | all 7 refresh-writing blocks in market.acceptance + prod-mode + outage clear `market_series_cache` in `afterAll` after awaited `refreshDemand` (every call is `await`ed in beforeAll/it) |
| 3 | Yes (2 of my runs + author's 5) | above |
| 4 | Yes | scan clean, no timeout raise |

## Blocking findings
1. `src/modules/digest/digest.acceptance.test.ts:515` — AC10's only reprint check is `net === 500`, which is pure fixture arithmetic: `saleAt` writes `profit_lines` revenue/cost directly and the digest net sums them, so the test passes with or without decision 0020 (proven: green with all T-P4-1 product files reverted). Card AC1 asks the assertions to follow 0020, "the reprinted unit counts"; nothing here asserts a count. Failure scenario: someone puts `not is_reprint` back into `analytics/shared.ts` `isUnit`; the digest's week now counts 0 units for a reprinted sale, and AC10 (and `digest.test.ts` AC10, which also asserts only net/revenue) stays green. Fix (proven red on old, green on new): add a units assertion for the week, e.g. `getProfit(...).totals.units` toBe(1) (getProfit is already imported in this file), or the snapshot's `current.units`.
   The 500 -> 2000 cost change itself is not a loosening: equality is just as strict, the cancelled 9999 exclusion is still checked, and 2x cost for a second transfer matches 0020 §3.

## Checks
- [x] Only owned paths changed (`git show --stat b5dcd89`: the 4 owned files)
- [x] Nothing outside scope
- [ ] Tests exercise the behavior, none weakened: no weakening; digest AC10 does not exercise the reprint rule (finding 1)
- [x] Tenancy, idempotency, money, en/es: n/a (test code; cleanup uses `withSystem` on the tenant-less cache table, as 9eae8fd)
- [x] Decisions recorded: 0020 applies; none new needed

## Optional notes (not blocking)
- `market-scale.acceptance.test.ts` (skipIf, not owned) also calls `refreshDemand` without clearing; fine while skipped by default.
- The "2 Vite servers not exiting" close timeout appears on every run (exit unaffected); pre-existing.
