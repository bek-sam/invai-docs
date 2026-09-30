# Review of T-23-10 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: backend-foundation on Opus 5.5 (card says sonnet)
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git show --stat 61c6396` | 3 files, all `src/db/seed/**` (+97, no deletions) |
| `pnpm typecheck && pnpm lint` | exit 0; biome 424 files clean |
| `pnpm test --reporter=dot src/db/seed` (own DB `invai_t2310r_test`, Redis 11) | 4 files / 6 tests passed, 22 s wall |
| scratch DB after it: `market_series_cache` by source | 139,984 rows, 4 sources (census 52, 3 x 46,644), all `mock=t` |
| `vitest run src/modules/market` alone | 5 passed, 1 skipped / 93+1 (green this time) |
| `vitest run src/db/seed/market-demand.test.ts src/modules/market` x2 | 94 tests, all green both runs |
| `--sequence.shuffle.files` seeds 1-8 (seed test + 3 market acceptance files) | 8/8 green; seeds 4-6 ran the seed test first, before `market.acceptance` |
| `scan-test-weakening.sh invai-backend 61c6396~1` | no hits |
| cleanup | scratch DB dropped, Redis DB 11 flushed. Dev `invai` and `invai_test` not touched |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes (code and unit test) | `market-demand.ts:24-33` calls the real `refreshDemand()` and `computeSignalsForShop()`. No inserted rows. The test shows every source ran and every row has `mock=true`. Browser "Sample data" is from the author's report; E2E runs at the gate (0019) |
| 2 | yes | the test calls it twice and the row count doesn't change. `refreshDemand` also skips sources whose cache is still fresh (`jobs.ts` TTL guard), and signals and recommendations are upserts |
| 3 | author only | golden path 13/13 and digest are in the report; left for the gate |
| 4 | author only | 5/5 and 7/7 (+1 skipped) are in the report; left for the gate |
| 5 | yes | `marketDemandProviders()` picks the mock whenever a key is unset (`integrations/market/index.ts:34-44`). Census uses its recorded fixture. The classifier uses the AI gateway, which has a mock when there's no key |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`src/db/seed/{index,market-demand,market-demand.test}.ts`)
- [x] Nothing outside scope (market module untouched)
- [x] Tests exercise the behavior, none weakened. On pollution, `fileParallelism: false` (vitest.config.ts:10) means the new test's first-line `delete(marketSeriesCache)` can't race another file. The ~140k rows it leaves behind didn't break any market file in 10 orderings, including seed-first. Each `pnpm test` truncates at start. So this commit doesn't make the existing pollution worse.
- [x] Tenancy: `withSystem` only inside `refreshDemand` (global cache, ADR 0015). Per-shop compute uses the existing path. No money, UI text or schema changes
- [x] Decisions: none needed

## Optional notes (not blocking)
- The new test doesn't clear `market_series_cache` in `afterAll`. Adding that would match `service.test.ts:465`.
- The seed's classify step charges `sku_suggestion` credits to Desert Bloom (40 designs), and it would make real AI calls if an Anthropic key were ever set locally. That's fine today, but worth a line in the runbook.
- Seed volume is about 140k cache rows, the same as one nightly sweep. The test's insert took about 3 s.
