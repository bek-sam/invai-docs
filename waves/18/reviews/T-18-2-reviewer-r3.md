# Review of T-18-2 (round 3, OI-16: the ISO-week fix only)

- Reviewer: reviewer on opus
- Author: integrations-engineer on sonnet
- Verdict: **approve**
- Scope: owner-inbox OI-16 limits this round to round-2 finding 1 (`endOfIsoWeekIso`). Commit reviewed: `invai-backend` `480302c`, compared with `0fce415`. I used my own worktrees at `480302c` and `0fce415` (next to the repos, `node_modules` symlinked, `node_modules/.bin/*` run directly), test DB `invai_t18_rev_2` and Redis DB 10. Afterwards I removed both worktrees, dropped the DB and flushed Redis DB 10.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git show --stat 480302c`, `git diff --stat 0fce415 480302c` | 2 files: `src/integrations/market/period.ts` (+8/−6) and `src/integrations/market/period.test.ts` (new, 68 lines). Nothing else changed |
| My own independent check (tsx script in my scratchpad, outside the repo). I walked every UTC day from 2019-12-01 to 2031-01-31, labelled each day's ISO week with the Thursday rule (ISO year = the year of that week's Thursday) and took the last day of each week as the expected end. Then I compared `periodEndIso(p, "week")` with it for every week of 2020–2030 | At `480302c`: **574 weeks checked, 0 mismatches** (53 weeks in 2020 and 2026, 52 in the other years). At `0fce415` the same script shows the old bug: `2027-W10 → 2027-03-07`, `2027-W01 → 2027-01-03`, `2021-W01 → 2021-01-03` |
| A second independent oracle: Python `datetime.date.fromisocalendar(y, w, 7)` for every ISO week of 2020–2030, written to JSON and compared in tsx | **574 compared, 0 bad**. `2027-W10 → 2027-03-14T23:59:59.999Z`, `2026-W53 → 2027-01-03`, `2027-W01 → 2027-01-10`, `2020-W53 → 2021-01-03`, `2021-W01 → 2021-01-10`. (Node 24 here has no `Temporal`, so I used Python as the second oracle) |
| Fail-without-fix: copied `period.test.ts` onto `0fce415` and ran `vitest run src/integrations/market/period.test.ts` | **6 failed, 6 passed**: the 2027-W10 example and the years 2021, 2022, 2023, 2027 and 2028. 2020 and 2024–2026, 2029 and 2030 pass on the old code, which matches the rule (1 Jan on a Fri, Sat or Sun) |
| At `480302c`: `vitest run src/integrations/market` | **Test Files 7 passed (7), Tests 69 passed (69)**. That matches the report's count |
| `node_modules/.bin/tsc --noEmit` | exit 0 |
| `node_modules/.bin/biome check .` | "Checked 342 files … No fixes applied." |
| `scan-test-weakening.sh <worktree> 0fce415` | "Result: no hits" (no test-only branches added and no assertions removed) |

## Round-2 finding
| Item | Fixed? | Test that fails without it |
|---|---|---|
| R2-1 A weekly `asOf` is one week early when 1 Jan falls on a Fri, Sat or Sun (`period.ts` `endOfIsoWeekIso`) | **yes**. The code now anchors on 4 January: week-1 Monday = jan4 − (dow(jan4) − 1) days, then + (week − 1)·7 days, then + 6 days at 23:59:59.999Z. Two independent oracles agree on all 574 weeks of 2020–2030 | `period.test.ts`, which fails 6 of 12 on `0fce415`. Its independent ordinal-date `isoWeekOf` agrees with Python's `fromisocalendar`, because the test passes at `480302c`, where I checked all 574 outputs against Python |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1–5, 7, 8 | yes (not changed this round) | Round 2 already checked these. `480302c` touches only `period.ts` and its new test. All 69 market tests are green |
| 6 Provenance, one `asOf` format | **yes** | A weekly `asOf` is now the Sunday end of the correct ISO week for every week of 2020–2030 (both oracles). The monthly path is unchanged |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (2 files under `src/integrations/market/**`)
- [x] Nothing outside scope (just the OI-16 fix plus its test)
- [x] Tests exercise the behavior, and none were weakened (the new test fails on the old code, and the scan found no hits)
- [x] Tenancy, idempotency, money, en/es: not affected (a pure date helper; no tables, request paths or strings)
- [x] Decisions recorded where needed (OI-16 scoped the round; no new decision)

## Optional notes (not blocking; OI-16 allows no more rounds, so these are for a new card if wanted)
1. The commit message and the report's Round 3 section list 2020 as an affected year. 1 Jan 2020 was a Wednesday, and the old code was correct for 2020 (the new test passes 2020 on `0fce415`). This is only a documentation slip.
2. `endOfIsoWeekIso` accepts out-of-range weeks (`W00`, `W54`, or `W53` in a 52-week year) and silently rolls them into a neighbouring week. Periods come from `isoWeek()`, so this can't happen today. A range check would guard any future caller.
3. The round-2 optional notes (tautological third test in `rate-limit-keys.test.ts`, the 2025-fixed seasonal tests expiring in January 2028, a future-dated `asOf` for the current period, `personalized: false` in the real Amazon and Walmart skeletons) are still open. They belong on a new card if the tech lead wants them.
