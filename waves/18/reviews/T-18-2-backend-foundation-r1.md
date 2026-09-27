# Review of T-18-2 (round 1) — env.ts / env.test.ts hunks only

- Reviewer: backend-foundation on Sonnet 5
- Author: integrations-engineer on Sonnet 5 / Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend show 8dd2084 -- src/env.ts src/env.test.ts` | Only commit touching these files for this card; adds 4 optional keys + `MARKET_MOCK_FAIL` |
| `git -C invai-backend show 0fce415 -- src/env.ts src/env.test.ts` | Empty — round 2 didn't touch env.ts/env.test.ts |
| `git -C invai-backend diff 8dd2084^ 8dd2084 -- src/env.ts` (filtered to non-grant lines) | Only comments/structure belonging to the grant; nothing else changed |
| `grep -n "PRODUCTION_KEYS" -A15 src/env.ts` | `CENSUS_API_KEY`, `GOOGLE_TRENDS_API_KEY`, `PINTEREST_API_KEY`, `JUNGLE_SCOUT_API_KEY` not present |
| Worktree at `0fce415`, symlinked `node_modules`, `node_modules/.bin/vitest run src/env.test.ts` | `Test Files 1 passed (1)`, `Tests 10 passed (10)` |

## Acceptance criteria (card's Grant line)
| # | Met? | Evidence |
|---|---|---|
| Only optional keys `CENSUS_API_KEY`, `GOOGLE_TRENDS_API_KEY`, `PINTEREST_API_KEY`, `JUNGLE_SCOUT_API_KEY` added | Yes | All four use `secret(z.string())`, same as existing optional keys (`EASYPOST_API_KEY` etc.) |
| None in `PRODUCTION_KEYS` | Yes | `PRODUCTION_KEYS` list (env.ts:141-151) unchanged, doesn't include any of the four |
| `env.mocks` entries follow existing pattern | Yes | `census: !raw.CENSUS_API_KEY`, `googleTrends: !raw.GOOGLE_TRENDS_API_KEY`, etc. — identical shape to `billing: !raw.STRIPE_SECRET_KEY` |
| `MARKET_MOCK_FAIL` parses safely and is ignored in production | Yes | `secret(z.string())` input; output is `isProd ? [] : (raw.MARKET_MOCK_FAIL ?? "").split(",").map(trim).filter(Boolean)` wrapped in a `Set` — empty string, undefined and trailing commas all handled; always empty when `isProd` |
| Nothing else in env.ts changed | Yes | Filtered diff shows only comment/structure lines belonging to the grant |
| env tests pass | Yes | 10/10 passed in isolated worktree at 0fce415 |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat` for this card's env.ts/env.test.ts commits shows exactly these two files)
- [x] Nothing outside scope (no `PRODUCTION_KEYS` change, no unrelated env.ts edits)
- [x] Tests exercise the behavior (production-boot mocks JSON includes the four new keys; no weakened assertions)
- [x] Tenancy / idempotency / money / i18n — n/a to this hunk
- [x] Decisions recorded where needed — n/a, follows existing `env.ts` convention, no new pattern

## Optional notes (not blocking)
- None.
