# Review of T-18-2 (round 1)

- Reviewer: reviewer on opus
- Author: integrations-engineer on sonnet (the report's header says "Opus 5.5". Either way this review ran on a different model.)
- Verdict: **changes-required**
- Commit reviewed: `invai-backend` `8dd2084`. I checked it out in my own worktree, used test DB `invai_t18_rev_2` and Redis DB 10, and have since removed the worktree and dropped the DB.

## Evidence I re-ran
| Command | Result |
|---|---|
| `node_modules/.bin/tsc --noEmit` (worktree at 8dd2084) | exit 0 |
| `node_modules/.bin/biome check .` | "Checked 317 files … No fixes applied." (clean) |
| `vitest run src/integrations/market src/env.test.ts` | 6 files, **45/45 passed** |
| `vitest run` (full suite, own DB and Redis) | **103 files, 750/750 passed** (QA's acceptance tests land in 9ed71b9, after this commit) |
| `grep -rn "fetch(" src/integrations/market` (non-test) | 1 hit: `http.ts:103`, the shared policy. It sits behind the allowlist (`MARKET_ALLOWED_HOSTS`), and every adapter that reaches it is chosen only when its key is set (or, for pricing, when the connection is `provider: "live"`) |
| Network in tests | Every test that reaches `fetchJsonWithPolicy` stubs `fetch` (`vi.stubGlobal`) first. `census.test.ts` runs without a key, so it reads the fixture. No live host is reached |
| `scan-test-weakening.sh <worktree> 8dd2084~1` | Assertions removed=0, added=79. The only hits are the word "retries" in test names, plus a `log.debug` in census.ts that doesn't change any behavior. `env.test.ts` changes one expected string (4 mock keys added), which isn't a loosening. No skip, only or snapshot changes |
| Exercise script (tsx, my copy), "teacher shirt" called twice per source | All 4 demand sources return `mock true`, `identical true`. The Census fixture has 120 points, first `2016-01=12324, 2016-02=11850, 2016-03=13430`, last `2025-10=16764, 2025-11=20002, 2025-12=29527`. A sample-workspace Amazon pricing call returns `mock true` with only `landedPriceCents/isFeatured/offerCount`. Etsy returns `null` |
| Same script with `MARKET_MOCK_FAIL=google_trends` | `google_trends threw MarketProviderError google_trends mock is failing (MARKET_MOCK_FAIL)`. census, pinterest_trends and jungle_scout still work |
| Same script with `NODE_ENV=production ALLOW_MOCKS=true MARKET_MOCK_FAIL=google_trends` | `isProd true marketMockFail []`, and google_trends returns data. The switch is ignored in production ✔ |
| Flake probe: `mockPricingProvider(...).comparables` called twice, 20,000 times | `asOf` differed in 149 of 20,000 pairs, so the `toEqual` in `mock.test.ts:103` flakes about 0.75% of the time (note 4) |
| `git show --stat 8dd2084` | 18 files, all under `src/integrations/market/**` plus the granted `src/env.ts` and `src/env.test.ts` |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Deterministic, seasonal mocks, `mock: true` | yes | sha256 seeding and 6 shapes in `mock.ts`. The same query called twice gives identical points (my script and `mock.test.ts`). The window ends at "now", so the points are identical within a month; see note 3 |
| 2 Census: real client with key, fixture without | **no** | `censusRetailSeries` uses the fixture correctly, but `marketDemandProviders()` never does (finding 1). The keyless GET was attempted and got a "Missing Key" page, so the fixture was built from the documented shape, which the card allows. Disclosed |
| 3 Selection | yes | `index.ts:53-68` and `index.test.ts`: null for Etsy, TikTok and Shopify and for a missing or inactive connection. A sample workspace gets the mock even with `provider: "live"`. The function takes a `sampleWorkspace` boolean, so the caller (T-18-3) owns the `isSampleWorkspace` call; nothing here reads `companies.demo` |
| 4 Real adapters are skeletons: timeout, rate limit, retry with jitter, `UnrecoverableError` on 401/403 | partly | The policy in `http.ts` is correct and tested (8 tests, plus 5 adapter 401/403 tests). But the Google Trends and Pinterest rate limiters are keyed on the secret itself (finding 2) |
| 5 `MARKET_MOCK_FAIL` | yes | Test plus my three runs above (dev, failing dev, prod) |
| 6 Provenance on every datum | **no** | All six fields are present, but `asOf` means three different things depending on the provider (finding 3) |
| 7 No seller identity | yes | The mock builds seller name, title and URL, then drops them. `mock.test.ts:82-96` allows only the 3 observation keys and greps the JSON for the names. The adapter tests do the same for `SellerId` |
| 8 Taxonomy queries only | yes | `types.ts:64-72` documents it, and `series` takes only `queries: string[]` |

## Blocking findings
1. **`src/integrations/market/index.ts:30`: without `CENSUS_API_KEY`, Census makes up a series for each query instead of using the recorded fixture (AC2), and the mock and real paths return different shapes.** Without the key, `marketDemandProviders()` returns `mockDemandProvider("census", "public_dataset")`. That produces a random, hash-seeded series for every taxonomy query, labelled `source: "census", licence: "public_dataset"`. My run shows `census … query teacher shirt … first 2025-10=100 last 2026-09=79`: a made-up "teacher shirt" series presented as a government public dataset. With the key, `censusDemandProvider()` ignores `queries` and returns exactly one NAICS-448 series (`query: "naics_448_clothing_retail"`, absolute scale). Failure scenario: T-18-3's nightly refresh calls `marketDemandProviders()` for 40 niches. In dev and staging it stores 40 "census" series with `relative_0_100` values and seasonal shapes Census doesn't publish, and `computeSignals` can fire R1 or R2 from them. The day a key is set, the same code gets 1 series per call, not 40, and a different scale. Fix: without the key, the census entry should be `censusDemandProvider()` reading the fixture (it already sets `mock: env.mocks.census`), and `index.test.ts` should assert that census returns the fixture (1 series, NAICS 448), not a per-query mock.
2. **`src/integrations/market/providers/google-trends.ts:33` and `providers/pinterest.ts:39`: the API key is used as the Redis rate-limit key, so it ends up in Redis and in error messages.** `rateLimit.key = \`market:google_trends:${env.GOOGLE_TRENDS_API_KEY}\`` (Pinterest does the same with its bearer token). `takeToken` stores the Redis key `ratelimit:market:google_trends:<secret>` and throws `rate limit wait exceeded for market:google_trends:<secret>` (`src/integrations/suppliers/ratelimit.ts:40`). Failure scenario: once a key is set, a nightly refresh with parallel workers queues past the 30 s wait. The job fails with the secret in its BullMQ `failedReason` (kept 7 days in Valkey) and in the worker's error log, and anyone who can read Valkey (`SCAN`, `MONITOR`) sees it too. Fix: use a constant key (`market:google_trends`, `market:pinterest_trends`), as Census and Jungle Scout already do.
3. **`src/integrations/market/mock.ts:139-148` compared with `providers/census.ts:105`, `google-trends.ts:48`, `pinterest.ts:57` and `jungle-scout.ts`: `asOf` means different things depending on the provider (AC6).** `types.ts:32` documents `asOf` as "the date the series describes (its last point), not the call time". The mocks set `asOf` to the call time (an ISO datetime). Census and the real adapters set it to a period string (`"2025-12"`, and `"2026-W38"` for weekly series). The contract's `SignalProvenance.asOf` is `Timestamp = z.iso.datetime({offset:true})`. Failure scenarios: (a) T-18-3's `isStale(source, asOf: Date, now)` (`src/modules/market/confidence.ts:27`, work in progress) is never true for mock data, so "stale source" behavior can't be tested on mocks. (b) `new Date("2026-W38")` is an Invalid Date, so a weekly real series gives a `NaN` age and is never stale. (c) Passing `"2025-12"` into `SignalProvenance.asOf` fails the contract's output validation. Fix: one format for every provider, an ISO datetime for the last point's period (for example the end of that month or ISO week, in UTC). The mocks should derive it from their last point, and a test should assert `Timestamp.parse(series.asOf)` for the mock, the Census fixture and a stubbed real response.

## Checks
- [x] Only owned paths changed (`git show --stat 8dd2084`: `src/integrations/market/**` plus the granted `env.ts` and `env.test.ts`. The env hunk only adds 4 optional keys, none in `PRODUCTION_KEYS`, their `env.mocks` entries, and `marketMockFail`, which is empty in production, verified above)
- [x] Nothing outside scope (no tables, jobs, UI or scraping; the pricing provider returns `null` for Etsy, TikTok and Shopify)
- [x] Tests exercise the behavior and none were weakened (scan clean; `env.test.ts` only extends an expected string). Gap: nothing tests that `marketDemandProviders()` returns the Census fixture (finding 1), and `mock.test.ts:103` is flaky (note 4)
- [x] Tenancy, idempotency, money, en/es: there are no tables or request paths. Money is integer cents (`Math.round(amount*100)`). Pricing rate-limit keys are per connection. No UI strings
- [x] Decisions recorded where needed (selection by the connection's `provider: "live"` is explained in the report; nothing crosses modules beyond `wave.md`)

## Optional notes (not blocking)
1. Fence: the report says the author also fetched `api.census.gov/.../marts/variables.json` ("confirmed live, keyless") besides the one data GET. That is a second keyless call to the Census API. It was harmless (public metadata, nothing sent), but the card allows exactly one. The tech lead should note it for the gate; nothing in the code needs fixing.
2. `providers/pinterest.ts:44`: `?? res.trends[0]` falls back to another keyword's series under the requested query's name. It should return an empty series or throw instead. Nothing selects this adapter today.
3. `mock.ts:132`: the mock window ends at the wall clock (`new Date()`), so a series changes at month and week boundaries, and the `declining` shape re-bases every month. "Across processes" holds within a month. It's acceptable if the window end is treated as `asOf`, which finding 3's fix does.
4. `mock.test.ts:98-104`: `expect(first).toEqual(second)` compares `asOf` and `fetchedAt` at millisecond precision, and I measured a flake rate of about 0.75%. Compare `observations` and `requestKey` only, as the demand test does.
5. `http.ts:151`: a 200 response that isn't JSON (Census's HTML "Missing Key" page is one) throws a plain `SyntaxError`, not `MarketProviderError`. Wrapping it would keep T-18-3's error handling typed.
6. `http.ts:98`: the rate-limit token is taken once per call, so retries don't consume tokens. For Amazon (1 request per 30 s) a 429 retry after about 0.5–1 s will probably get another 429. Consider taking a token on each attempt.
7. `amazon-pricing.ts`: there is no `x-amz-access-token` header, and `competitiveSummary` is really the batch POST endpoint. It's a skeleton marked as never reachable, so fix it when an adapter goes live.
8. Process: the card asked for a stub commit first, and the report says why there isn't one. It had no effect: T-18-3's stub came first and doesn't import this module.
