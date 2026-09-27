# Review of T-18-2 (round 2)

- Reviewer: reviewer on opus
- Author: integrations-engineer on sonnet
- Verdict: **changes-required** (one new finding, found in the fix for round-1 finding 3. It's a small fix. This is the second round, so the tech lead decides how it closes; see "For the tech lead")
- Commit reviewed: `invai-backend` `0fce415`, compared with round 1's `8dd2084`. I used my own worktree at `0fce415` with symlinked `node_modules`, a second worktree at `8dd2084` for the fail-without-fix runs, test DB `invai_t18_rev_2` and Redis DB 10. I removed both worktrees, dropped the DB and flushed Redis DB 10 afterwards.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git diff --stat 8dd2084 0fce415 -- src/integrations/market src/env.ts src/env.test.ts`, `git show --stat 0fce415` | 15 files, all under `src/integrations/market/**`. `env.ts` and `env.test.ts` are untouched this round, and the commit touches nothing else |
| `node_modules/.bin/tsc --noEmit` | exit 0 |
| `node_modules/.bin/biome check .` | "Checked 341 files … No fixes applied." |
| `vitest run src/integrations/market src/env.test.ts` | 7 files, **67/67 passed** (the report says 68. The count differs by one, but every test passed) |
| `vitest run src/modules/market/ src/modules/ai/market.acceptance.test.ts` | 6 files, **94 passed, 4 failed**, all 4 in `market.acceptance.test.ts`: **AC17** (`expected -0.25 to be close to +0`), **AC19** (`expected 12 to be 17`: the test counts the provider's raw mix, which the tech lead's AC19 decision says QA rewrites), **AC30** (`expected 14 to be ≥ 1364`: `thinAmazonDesign` enters `price: P0 / 100` in dollars against a cents contract), **AC26** (`R2 for the second thin design: expected undefined`: the same `thinAmazonDesign` dollars fixture). These are exactly the known reds. `market-outage`, `market-prod-mode` and `ai/market.acceptance` are fully green, including both "disagreement" suites that round 2b targeted |
| Fail-without-fix: copied the new or changed `index.test.ts`, `providers/{rate-limit-keys,census,providers}.test.ts` onto `8dd2084` | **8 failed, 17 passed**. Failed: finding 1 (census fixture), both constant-key tests (finding 2), the census Timestamp test and both stubbed Google/Pinterest `asOf` tests (finding 3), and both AC7 key-list tests (new fields). The new `mock.test.ts` cases import new exports (`THIN_TEST_SUFFIX`, `MOCK_TREND_SHAPES`), so they can't load on `8dd2084` at all |
| Import-cycle check: tsx script loading `src/modules/market/jobs` first and then `src/integrations/market/index`, and the reverse order | both load: `market-first ok 11 function`, and `integrations-first ok census:true,google_trends:true,pinterest_trends:true,jungle_scout:true 69`. `src/modules/market/niches.ts` has **no imports**, so `mock.ts → niches.ts` can't close a cycle |
| Exercise script (tsx), "teacher shirt" + "halloween shirt", weekly, 3 years, called twice per source | `census mock true n 1 identical true asOf 2025-12-31T23:59:59.999Z`; google_trends, pinterest_trends and jungle_scout give `n 2 identical true asOf 2026-09-27T23:59:59.999Z last 2026-W39`, and every `asOf` passes `Timestamp.safeParse` |
| Same script with `MARKET_MOCK_FAIL=google_trends` | `google_trends threw MarketProviderError google_trends mock is failing (MARKET_MOCK_FAIL)`. The other three still work |
| Pricing mock, sample workspace, Amazon, connection `connected` | `D1 total 22 match 17` (personalized + tee), keys `landedPriceCents,isFeatured,offerCount,personalized,garmentClass`, and `D2-THIN-TEST` matching group = 4 (< 8) |
| Weekly seasonality, monthly average of 3-year weekly mock series | Halloween peaks in month **10**, Christmas in **12**, Mother's Day in **5** |
| `periodEndIso("<year>-W<nn>", "week")`, converted back with `isoWeek()`, for 2021–2028 | **2024, 2025 and 2026 round-trip. 2021, 2022, 2023, 2027 and 2028 come back one week early** (for example `2027-W10 → 2027-03-07T23:59:59.999Z`, which is in `2027-W09`). See finding 1 |
| `grep -rn "fetch(" src/integrations/market` (non-test) | 1 hit, `http.ts:103` (the shared policy, behind the allowlist and key selection). This round adds no new outbound calls. Every new test that reaches `fetch` stubs it first |
| `grep "new Date()\|Date.now\|Math.random" mock.ts period.ts` | `mock.ts:191` (window end, accepted in round 1, note 3), `:232` and `:361` (`asOf`/`fetchedAt` only). No `Math.random` |
| `scan-test-weakening.sh <worktree> 8dd2084` | For T-18-2's files, the removed assertions are: the old "6 hash-picked shapes" test, the 40-query up/down test, `MOCK_SEASONAL_SHAPES`, the full-object `toEqual(first, second)` (round-1 note 4), and census `asOf toBe(period)`. Each has an equal or stronger replacement: a 0..100 check over every taxonomy query, per-niche peak-month tests, `g4` ≥ ±15% checks, an observations + requestKey comparison, and `Timestamp.parse` + `startsWith(period)`. The other hits are other cards' commits since `8dd2084` |

## Round-1 findings and routed items
| Item | Fixed? | Test that fails without it |
|---|---|---|
| R1-1 Census without a key = the recorded fixture | yes, `index.ts:36` → `censusDemandProvider()` | `index.test.ts` "reviewer finding 1" (fails on 8dd2084) |
| R1-2 Rate-limit key never contains the secret | yes, `google-trends.ts:36`, `pinterest.ts:40` | `rate-limit-keys.test.ts` constant-key tests (fail on 8dd2084). Its third test ("thrown error carries no key material") calls `takeToken` with a hard-coded constant, so it passes on the old code too and proves nothing. Not blocking; the two tests before it cover the fix |
| R1-3 One ISO-datetime `asOf` | mostly. Monthly periods are right. **Weekly periods are one week early in 3 of 7 years** (finding 1) | census, mock and stubbed-adapter `Timestamp.parse` tests (fail on 8dd2084). None of them catches the week error, because they only use 2026 weeks |
| R1 note 4 flake | yes. Determinism tests compare `points`/`observations` + `requestKey` only (`mock.test.ts:25, 200`) | n/a |
| QA 1: n ≥ 8, documented thin case | yes. 10–24 normal, 2–5 for `-THIN-TEST` (`mock.ts` `mockRawOffers`) | new `mock.test.ts` count tests |
| QA 2: `personalized` + `garmentClass` | yes. `personalized` is required and `garmentClass` optional (additive). The mock mixes both. The real skeletons default to `personalized: false` and copy the class from the request (documented) | `mock.test.ts` mix tests, `providers.test.ts` AC7 key lists |
| 2b: peaks follow the niche; a deterministic subset rises or falls | yes. Monthly unit tests plus my weekly check (10, 12, 5). Police rises and firefighter falls (niche-average g4). The acceptance "disagreement" suites pass | `mock.test.ts` 2b blocks |
| AC19 | per the tech lead's decision the provider returns the raw mix. The QA test is to be rewritten; the red is expected | n/a |
| Tuned trend parameters documented | yes. `TREND_WINDOW = 16`, `TREND_RATE ±0.13` and the 1–5 / 95–99 anchors each carry a comment with the reason, and B-131 records the non-detrended seasonality follow-up | n/a |
| `Object.keys` / equality changes in `providers.test.ts` | only the two added fields (`personalized`, `garmentClass`), plus a new `expect(obs.garmentClass).toBe("tee")`. The fixture input `"t-shirt"` became `"tee"`, a spec class. Nothing loosened | n/a |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Deterministic, seasonal mocks, `mock: true` | yes | The exercise gives identical points and requestKey twice. Peaks follow the niche (Halloween 10, Christmas 12, Mother's Day 5, back-to-school 8 in the unit test). Rising, falling and flat shapes all exist |
| 2 Census: fixture without a key | yes | 1 NAICS-448 series, `mock true`, `asOf 2025-12-31T23:59:59.999Z` |
| 3 Selection | yes | Unchanged since round 1. Tests are green. The sample workspace gets the mock |
| 4 Real skeletons | yes | Constant rate-limit keys now. The 401/403 tests are green |
| 5 `MARKET_MOCK_FAIL` | yes | The script run above |
| 6 Provenance, one `asOf` format | **partly** | Every value parses as a `Timestamp`, but a weekly `asOf` describes the wrong week in 2027 and later (finding 1) |
| 7 No seller identity | yes | Keys are exactly the 5 allowed fields. The mock and the stubbed adapters drop seller names |
| 8 Taxonomy queries only | yes | Unchanged |

## Blocking findings
1. **`src/integrations/market/period.ts:41-48` (`endOfIsoWeekIso`): in any year whose 1 January is a Friday, Saturday or Sunday, a weekly period's `asOf` is the Sunday one week earlier. That includes 2027 and 2028.** The code starts from `1 Jan + (week-1)*7` and walks back to its Monday. ISO week 1 is the week that contains 4 January, so for those years the result is the previous ISO week. I checked this with a round-trip (`periodEndIso` → `isoWeek`). `2027-W10` gives `2027-03-07T23:59:59.999Z`, which falls in `2027-W09`. The same happens in 2021, 2022, 2023 and 2028. 2024, 2025 and 2026 are correct, which is why the 2026-only tests pass. This is the round-1 finding 3 fix ("asOf = the end of the last point's period"). Failure scenario: from 4 January 2027, every weekly mock series (google_trends, pinterest_trends, jungle_scout, the ones the nightly refresh stores for sample and dev workspaces) gets an `asOf` 7 days older than the data. `confidence.ts` `freshness` (half-life 14 days) then scales those sources by about 0.71 (0.5^(7/14)), which can push a recommendation's band down. `isStale` (2 × 7-day TTL) marks a source stale a week early, so one missed refresh shows "stale source" to the shop. The same code runs for the real weekly adapters once a key is set. Fix: anchor on 4 January (`jan4 = Date.UTC(year, 0, 4)`, Monday of week 1 = jan4 − ((dow(jan4)+6)%7) days, + (week−1)·7, + 6 days for Sunday). Add a test that round-trips `isoWeek(new Date(periodEndIso(p, "week"))) === p` for weeks in 2021–2028, including 2026-W53 and 2027-W01.

## Checks
- [x] Only owned paths changed (15 files under `src/integrations/market/**`; `env.*` untouched this round)
- [x] Nothing outside scope (no tables, jobs, UI or new outbound hosts; the import of `modules/market/niches.ts` is read-only, as the round allows)
- [x] Tests exercise the behavior and none were weakened (scan read; the replacements are stronger). One tautological test, noted above
- [x] Tenancy, idempotency, money, en/es: no tables or request paths. Money is integer cents. Pricing rate-limit keys are per connection. No UI strings
- [x] Mock still works and stays deterministic (no wall clock except the window end and `asOf`/`fetchedAt`; determinism tests compare points and observations, not `asOf`)
- [x] No import cycle (niches.ts has no imports; both load orders work under tsx; tsc clean)
- [x] Decisions recorded where needed (AC19 decision and B-131 are in `wave.md`; `garmentClass` optional is explained in the report)

## Optional notes (not blocking)
1. `rate-limit-keys.test.ts:530-550`: the third test only checks `takeToken`'s message for a hard-coded constant, so it passes on the old code. It also writes `ratelimit:market:google_trends` into whatever Redis DB the test run uses. Either drop it or drive it through the provider.
2. The seasonal unit tests use fixed 2025 months (`monthlyValue(…, "2025-10")`). They stay valid only while 2025-02 is inside the 3-year window, which ends in January 2028. Deriving the year from "now" would remove that expiry date.
3. A weekly or monthly mock `asOf` is the end of the *current*, unfinished period, so it can be up to 6 days (weekly) or about 30 days (monthly) in the future. `freshness` clamps the age at 0, so nothing breaks, but a consumer showing "as of" to users would show a future date.
4. Real Amazon and Walmart skeletons set `personalized: false` on every offer, so once live, a personalized design would have zero comparables after `filterComparables`. This is documented in both files. Handle it when a key is wired.
5. Round-1 notes 2 (Pinterest `?? res.trends[0]` fallback), 5 (non-JSON 200 → `SyntaxError`) and 6 (one rate-limit token per call, not per retry) are unchanged. They're still optional.

## For the tech lead
This is round 2. The single finding is new (it's in the fix, not a leftover from round 1). The fix is about 6 lines in `period.ts` plus one round-trip test. A focused check of that commit (`tsc`, the market tests and the round-trip) would be enough to close it. Whether that counts as a round-3 review or a gate check is your call under the 2-round rule.
