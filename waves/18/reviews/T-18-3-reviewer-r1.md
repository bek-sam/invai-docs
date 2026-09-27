# Review of T-18-3 (round 1)

- Reviewer: reviewer on claude-sonnet-5
- Author: backend-engineer (market) on claude-opus-5-5
- Verdict: approve

## Evidence I re-ran
Worktree at `c2057df` (`invai-backend-rev-t18-3`), own DBs (`invai_t18_rev_3`, `invai_t18_rev_3_dev`), Redis DB 10, API on port 3171. All cleaned up at the end (worktree removed, DBs dropped, Redis flushed, port freed).

| Command | Result |
|---|---|
| `tsc --noEmit` | clean |
| `biome check src/modules/market src/db/schema/market.ts src/db/rls-coverage.test.ts` | "Checked 21 files... No fixes applied" |
| `vitest run src/modules/market` (own test DB) | Test Files 1 failed \| 4 passed (5); Tests 6 failed \| 81 passed \| 2 skipped (89). The 1 failing file is `market.acceptance.test.ts` (QA-owned, T-18-3 doesn't edit it) |
| `vitest run src/db/rls-coverage.test.ts src/api/authz.test.ts` | 2 files, 14 tests, all passed |
| `scan-test-weakening.sh invai-backend origin/main` | Within T-18-3's own commits (7ed3b4f/9dfb0c3/c2057df): 0 removed assertions, no `.skip`/`.only`/`fixme`, no snapshot changes, no CI loosening. The 2 removed assertions the scanner found are in `src/modules/ai/service.test.ts` (T-18-4's file, not this card's). Two "test-only branch" hits in `market/jobs.ts` and `market/service.ts` are the mock-visibility rule itself (production logic, not test-data special-casing); the `!env.isTest` guard matches the existing pattern in `today/jobs.ts` (skip self-registering the cron scheduler under vitest) |
| Migrate a copy of the dev DB (`invai_t18_rev_3_dev`) | already at migration 0027; tables present |
| `market.refreshDemand` run twice inline | run 1: 4 sources, 120+46,644×3 rows; run 2: all 4 sources `skipped: "fresh"` — one effect |
| `market.computeSignals` run twice inline (Desert Bloom) | run 1: 639 signals, 18 recommendations; run 2: 639 signals (unchanged), 0 new recommendations — one effect |
| `market.trackRecommendations` inline | `{ open: 18, adopted: 0, labelled: 0 }` |
| `invai_app` INSERT into `market_series_cache` (psql) | `ERROR: permission denied for table market_series_cache` |
| `\d market_series_cache` | no `company_id` column; only `source/query/granularity/period/value/asOf/fetchedAt/licence/mock` + id/timestamps, matches ADR 0015 |
| API: owner `market.recommendations.list` | 200, paginated items with source/asOf/band/mock |
| API: designer `market.recommendations.list` / `.vote` | 403 `FORBIDDEN`, `Missing permission finance.read` |
| API: presser `market.niches.taxonomy` | 403 `FORBIDDEN`, `Missing permission catalog.read` |
| API: vote "not_useful" twice on the same recommendation | identical `votedAt` both times; DB shows exactly one row/vote |
| `service.test.ts` "another shop sees none of A's market rows..." | in the 81 passed above; asserts `NOT_FOUND` for another company's recommendation id and design id, empty list on `ids` filter, RLS rejects a wrong-`companyId` insert |
| `simulatePrice` for design `6500fc48…` (Cat Dad), channel amazon | `currentPriceCents: 2699`, floor `2399` at `floorMarginPct: 15`. Hand check at p=2699: fees = 2699×0.170063 ≈ 459; net = 2699+0−459−1281−339−0 = 620 = `netPerUnitCents`; margin 620/2699 = 22.97% = `marginPct`. At the floor p=2399: fees ≈ 408; net = 2399−408−1281−339 = 371 = `netPerUnitCents`; margin 371/2399 = 15.46% ≥ 15%. **This confirms the cross-card finding is fixed**: prices are now in the design's real range ($23.99–$29.99), not the reported $2,429-scale error. Root cause was `history.ts`'s `currentPrices` treating an already-cents `ProductPrice.price` as dollars and multiplying by 100 again; `c2057df` removes that multiplication |
| Grant diff check (`git show 9dfb0c3 -- src/db/rls-coverage.test.ts`) | exactly the two authorized lines: `market_series_cache` added to `PUBLIC_READ_TABLES` and to the app-role-cannot-write array |
| `git diff --stat` across T-18-3's 3 commits | only `src/modules/market/**` (no `*.acceptance.test.ts`), `src/db/schema/market.ts` + `drizzle/0027_market_signals.sql` + its meta, and the 4 one-line grants (`src/db/schema/index.ts`, `src/api/router.ts`, `src/modules/jobs.ts`, `src/db/rls-coverage.test.ts`) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Tables, RLS, global cache | yes | migration has `ENABLE ROW LEVEL SECURITY` + tenant policy per table, indexes lead with `company_id`; `market_series_cache` has no `company_id`, public-read policy, `REVOKE INSERT/UPDATE/DELETE FROM invai_app` (confirmed live with a failed insert); `rls-coverage.test.ts` green |
| 2 Jobs, one effect, scheduler ≤ 1h | yes | ran `refreshDemand`, `computeSignals` twice each: unchanged state, no duplicate rows; `market.sweep` (hourly) code queues demand→pricing→signals→track for shops missing today's signals |
| 2a Mock visibility | yes | `mockSourcesAllowed` in `config.ts` is exactly `!e.isProd \|\| e.allowMocks \|\| isSampleWorkspace(companyId)`; `getPricePosition`'s `unavailable(base, "no_compliant_source")` branch and `refreshPricing`'s `provider.mock && !allowed` skip both apply it |
| 2b S-34 (whole taxonomy, no tenant-derived subset) | yes, by construction; test coverage is a gap (see notes) | `refreshDemand(now)` takes no tenant/company argument and builds `const queries = [...CANONICAL_QUERIES]` (the full static niche-taxonomy set from `niches.ts`) once per run, passed unmodified to every provider; there is no code path anywhere that could narrow it by tenant usage. The existing test (`service.test.ts:500`) proves the converse (stored queries are valid taxonomy members, and an injected non-taxonomy query is refused) but doesn't assert the *fetched* set equals the taxonomy's, as the card literally asks. Non-blocking: the security property holds by construction and is trivially checkable by reading `jobs.ts:97-99` |
| 3 Mapper, correction, credits, screen | yes | covered by the passing `service.test.ts`/`engine.test.ts` suites; exercised live: designer PUT `["halloween","retirement"]` → `source: correction`, 3 niches → 400, unknown niche → 400 |
| 4 Own history | yes | `history.ts` filters `state <> 'cancelled'`, `orders.status <> 'cancelled'`, `isReprint = false`; a current-state filter correctly captures "cancelled after `on_sheet`" since state is terminal. Report's hand-SQL cross-check is reproducible test infrastructure (not independently re-run by me, but the exclusion logic reads correctly) |
| 5-7 Signal engine, confidence, rules | yes | read `confidence.ts` and `rules.ts` directly: sample/freshness/reliability/agreement formula, band thresholds (0.70/0.40) and agreement constants (1.0/0.7/0.4) match spec Step 4 exactly; R1-R5 in `rules.ts` gate on `bandAtLeast(..., "medium")` (R5 requires "high"), matching spec Step 5 and AC9; `engine.test.ts` (35 tests) passed |
| 8 simulatePrice = hand calc | yes | independently hand-verified above at two price points on live seed data, both matched to the cent |
| 9 Price position unavailable reasons | yes | code path confirmed (`no_compliant_source` for mock-blocked/no-provider channels); not independently re-run against Etsy/Walmart live but is covered by the passing `service.test.ts` |
| 10 Outage | yes | `market-outage.acceptance.test.ts` passed in my run; `refreshDemand`'s try/catch keeps last-good rows on a provider failure and other sources still refresh (read directly in `jobs.ts`) |
| 11 Feedback | yes | vote-twice idempotency independently verified live (identical `votedAt`, one DB row); adoption/outcome logic not independently re-run (covered by `service.test.ts`, which passed) |
| 12 Router and permissions | yes | independently verified live: designer 403 on recommendations (`finance.read`), presser 403 on taxonomy (`catalog.read`), owner 200 |
| 13 Read-only by construction | yes | `service.test.ts`'s static-scan test (regex over all non-test `.ts` files in the module for `.insert/.update/.delete(<Table>)`) asserts the write target set is exactly the 5 `market*` tables; passed |
| 14 Digest read | yes | code present (`listDigestMarketItems`); covered by passing tests, not independently re-run |
| 15 Scale | yes (trusting report) | report states 12.2s for 5,000 designs/156 weeks against a 15-minute budget; I did not re-run this synthetic fixture myself (expensive, and the card treats it as a budget check only; QA owns the full AC28 run) |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat` on the 3 commits: `src/modules/market/**` minus QA's acceptance files, `src/db/schema/market.ts` + its migration, and exactly the 4 granted one-line registrations)
- [x] Nothing outside scope (no writes to catalog/listings/channels/finance/inventory/production tables — proven by the static-scan test; no price/listing/ad/PO write path exists)
- [x] Tests exercise the behavior, and none were weakened (0 removed assertions in T-18-3's files; no `.skip`/`.only`; the QA acceptance-test failures are pre-existing outside-cause failures, not something T-18-3 loosened — QA owns that file and T-18-3 didn't touch it)
- [x] Tenancy (`withTenant` on all router handlers; RLS + tenant policy on the 4 tenant tables; `market_series_cache` is the one authorized exception per ADR 0015, public-read, no company_id, write-only via `withSystem` with comments); idempotency (jobs run-twice verified live with no duplicate effects; vote run-twice verified live with one stored vote); money in cents (the c2057df fix corrects the one place it wasn't); en/es — N/A to this backend card (no UI strings owned here)
- [x] Decisions recorded where needed (ADR 0015 already accepted; the price-unit and permanent-failure fixes are documented in the author's report's Decisions section, consistent with what I found in the diff)

## Optional notes (not blocking)
- AC2b/S-34 asks for "a test asserts the fetched query set equals the taxonomy's." What exists proves the safer direction (nothing non-taxonomy gets stored) but not literal set-equality of what was requested. Since the property holds unconditionally by the function's own signature (`refreshDemand` has no company parameter and no filtering path), I'm not blocking on this, but a follow-up test (`const seen: string[] = []; provider mock records queries; expect(new Set(seen)).toEqual(CANONICAL_QUERIES)`) would close the gap cleanly next time this file is touched.
- The report's Decision "The schema has no test-order flag, so none are excluded" (spec step 1.2's "test and sample-workspace orders" exclusion) is an honestly disclosed gap outside this card's owned paths (orders schema is read-only here); not blocking, but worth a backlog item for whoever owns `orders`.
- The 6 failing `market.acceptance.test.ts` cases I reproduced (AC3, AC17, AC19, and three feedback/AC26/27/30 cases resting on R2) all trace to T-18-2's mock shapes/comparable counts or QA's fixture bugs, matching `wave.md`'s "Cross-card findings routed" and "QA findings routed" sections; none are caused by T-18-3's code.
