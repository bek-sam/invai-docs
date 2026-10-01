# Review of T-P5-4 (round 2)

- Reviewer: reviewer on Opus 5.5
- Author: backend-engineer (round 2 on Opus 5.5, per the report)
- Verdict: approve

## Evidence I re-ran (own worktree /tmp/p5-rev-t4r2 at 471355a, scratch DB invai_p5rev_t4r2, Valkey DB 13; worktree and DB removed, DB 13 flushed, no process left)
| Command | Result |
|---|---|
| `tsc --noEmit` / `biome check src/modules` | exit 0 / 226 files, no fixes |
| `vitest run src/modules/today src/modules/orders/timeline.test.ts src/modules/inventory src/modules/vendors` | 15 files, 144 passed. `today/service.test.ts` run 3 more times: 22/22 each (no flake) |
| Mutation: drop `sheetStatus` from sheet_stuck params (service.ts:403) | 1 failed (killed) |
| Mutation: drop `incoming` from stock_low params (:424) | 1 failed (killed) |
| Mutation: rename `usedPct` in plan_limit_near params (:447) | 1 failed (killed) |
| Mutation: `toAlert` skips `AlertParams.safeParse` (:207) | 1 failed (killed) |
| `scan-test-weakening.sh invai-backend cdeb3e3` | no hits |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | Unchanged since r1. vendors: `vendorName` is `.optional()` in the contract (alerts.ts:85), so leaving it out still parses. `supplierName` now uses the same names as inventory/service.ts `SUPPLIER_NAMES` |
| 2 | yes | Unchanged since r1 |
| 3 | yes | Finding 1 is closed: the new generateAlerts test checks the exact params of sheet_stuck, stock_low, plan_limit_near and plan_limit_reached. Finding 2 is closed: a known code with bad params now loses both fields. All four r1 mutations now fail a test |
| 4 | yes | Unchanged since r1 |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (3 files: inventory/jobs.ts, vendors/delivery.ts, today/service.test.ts). Only the alert input objects were edited
- [x] Nothing outside the ruling's scope. Missing tests in the other modules' test files are an accepted gap (tech lead ruling)
- [x] Tests exercise the behavior; none weakened
- [x] Tenancy: the test's `withSystem` is only for fixture setup. Idempotency, PII, money and UI text: no change

## Optional notes (not blocking)
- `SUPPLIER_DISPLAY_NAMES` copies the private `SUPPLIER_NAMES` map. Export the original later so the two can't drift.
- No test covers the two leak fixes; the ruling accepts this gap.
