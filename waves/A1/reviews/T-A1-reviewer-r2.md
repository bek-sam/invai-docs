Verdict: approve
# Review of T-A1 (round 2). Reviewer: reviewer on Opus 5.5. Author: backend-foundation. Commit invai-backend 5170e12 (on top of 472bd80).

## Evidence I re-ran
| Command | Result |
|---|---|
| `git show --stat 5170e12`, `git status --short` | 1 file, `src/db/seed/builder.ts` (+37/-11). Tree clean |
| `pnpm typecheck && pnpm lint` (invai-backend) | tsc clean; `Checked 440 files ... No fixes applied.` |
| `scan-test-weakening.sh invai-backend 472bd80` | `Result: no hits` (no test files changed) |
| Gate log `run-20260930T172303Z.log` (read) | backend `1298 passed / 3 skipped / 1 todo`, API golden path 13 passed, browser 34 passed, floor 3 passed. The trailing exit 143/1 lines are the SIGTERM teardown of the dev servers |
| SELECT: Desert Bloom orders per month | 2025-03..10: 182-252/mo (avg ~214); Nov-25 439, Dec-25 462 (~2.1x); Jan-26..Sep-26 252-357, rising |
| SELECT: last 30 d vs three prior 30 d windows | 360 vs 319 / 312 / 307 (1.13x). No cliff |
| SELECT: `is_rush` orders by quarter | 2025-Q1 2, Q2 6, Q3 7, Q4 11, 2026-Q1 9, Q2 9, Q3 46 (history + live). All history rush orders shipped. Spread over the whole range |
No seed, reset or writes. Nothing started.

## Round-1 findings
1. History volume cliff (builder.ts ~1156-1173): **fixed.** Rate ramps 6→11/day, times 1.75 in Q4, plus jitter of ±2 with a floor of 1. The live window is now 1.13x the trailing windows, not 8x, so `basePeriod` comparisons are realistic.
2. Q4 year for a Nov/Dec run (builder.ts 1141-1144): **fixed.** It picks histEnd's year only when histEnd is on or after Dec 31 23:59:59 of that year, otherwise the year before. Because histEnd = now − ~31 d, a Dec-5 run gives histEnd around Nov 4 and q4Year = the previous year, a full quarter. The worst case puts Nov 1 about 425 d before histEnd, inside the 549-d span, so the chosen Q4 always lies inside the history.

## Driver stride (≥30 samples)
`driverStride = max(1, floor(N/200))` over the non-cancelled pool. Since N/floor(N/200) ≥ 200, the loop visits at least 200 plans, so all 3×50 targets fill. It also spreads them across the whole range, as the quarterly rush counts show. The author's `late_rate_drivers` numbers (blocked 50/50, rush 77/50, personalized 411/57) are consistent with this. Every driver clears the 30 minimum.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| AC-Seed1 | Yes | Span 19 months; Q4 ~2.1x trailing; drivers above; other items unchanged from r1 (the author's r2 SQL table) |
| Golden path | Yes | Gate at 5170e12: API 13/13, browser 34/34, floor 3/3 |
| Late drivers / scans / dead stock / PO trends / edge cases | Yes | Unchanged from r1; this diff touches only plan volume, the Q4 year and driver assignment |

## Checks
- [x] Only owned paths (`src/db/seed/**`)
- [x] No scope creep
- [x] Tests not weakened (no hits)
- [x] Tenancy / idempotency / money: no new tables or paths. Seed rows keep `companyId: shopId`
- [x] Decisions: none needed

## Optional notes (not blocking)
a. Round-1 notes a-e still stand as realism follow-ups. Note a (100% late iff driver) could go to the backlog.
b. The order count is now ~5.4k per seed. The gate seed took 43 s, which is fine.
