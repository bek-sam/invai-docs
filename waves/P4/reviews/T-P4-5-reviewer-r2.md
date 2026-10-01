# Review of T-P4-5 (round 2)

- Reviewer: reviewer on Opus 5.5
- Author: qa-engineer on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git show --stat 19a85c3` | 1 file: `src/modules/digest/digest.acceptance.test.ts` +20/-0 (owned) |
| Worktree /tmp/rv-p4-5b @ 19a85c3, `analytics/shared.ts` from e3c3cf7 (via `git show`), `vitest run digest.acceptance -t AC10` | exit 1: `expected +0 to be 1` (1 failed, 16 skipped). Worktree removed |
| Main tree `pnpm vitest run src/modules/digest/digest.acceptance.test.ts --reporter=dot` | exit 0: 16 passed, 1 todo |
| `pnpm typecheck` / `pnpm lint` | tsc no errors / 457 files, no fixes |
| `scan-test-weakening.sh invai-backend b5dcd89` | no hits |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | r1 finding 1 resolved: AC10 keeps `net === 500` and adds `getProfit(week).rows[].units` summed `toBe(1)`; red with the old `not is_reprint` filter, green on HEAD |
| 2-4 | Yes | unchanged since r1 (approved there); scan clean, no timeout or skip |

## Blocking findings
none

## Checks
- [x] Only owned paths changed; nothing outside scope
- [x] Tests exercise the behavior, none weakened (additive assertion only)
- [x] Tenancy/idempotency/money/en-es: n/a (test code; `withSystem` read in a test, as elsewhere in the file)

## Optional notes (not blocking)
- The 6-line comment in the test is longer than needed; harmless.
