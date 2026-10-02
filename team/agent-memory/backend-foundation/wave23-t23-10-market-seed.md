---
name: wave23-t23-10-market-seed
description: T-23-10 market-demand seed card — self-inflicted concurrent-test-run flakiness, and env vars a manual scratch API/worker/web stack needs that dev:all supplies for free
metadata:
  type: project
---

Card: T-23-10 (seed calls `refreshDemand()` + `computeSignalsForShop()` for the demo shop, the
same way `market.sweep` would, so `market.spec.ts`'s "Sample data" badge has outside demand data
right after `pnpm db:seed`). Backend commit `61c6396`.

**Never run two `pnpm test` (or `pnpm test <paths>`) invocations against the same
`TEST_DATABASE_URL`/`TEST_REDIS_URL` at the same time, even in separate background shells.**
`global-setup.ts`'s `truncateAll()` runs once per *invocation*, so two overlapping invocations
truncate and write through each other mid-run. I launched three overlapping background loops
(a 4x flake-check, a 3x baseline, and the required gate check) all pinned to the same
`invai_test`/Redis DB 9, and got a real Postgres `deadlock detected` on `market_series_cache`, a
`0 rows` assertion (another process's truncate ran mid-test), and a stray `1970-01-01` timestamp —
none of which reproduced when I re-ran the exact same command alone. This is the same class of
mistake as [wave22-t22-2-composite-fks.md](wave22-t22-2-composite-fks.md)'s "check `pg_stat_activity`
before a full suite" note, but this time self-inflicted by *me*, not a leftover from another agent:
before trusting any test failure, run `ps aux | grep -E "vitest|pnpm test"` and make sure exactly
one such process exists.

Once truly isolated, `src/db/seed/market-demand.test.ts`'s own idempotency assertion was still
occasionally flaky for a *different*, pre-existing reason: `market_series_cache` is a genuinely
global table (ADR 0015), and several `src/modules/market/**` test files (their own, read-only to
this card) write to it under `vi.setSystemTime`-frozen past dates without a `clearCache()` in
every `afterAll` (`market.acceptance.test.ts` in particular). A leftover row can be fresher or
staler than the real clock this test runs under depending on file execution order, changing
whether `refreshDemand()`'s TTL skip fires. Fix on my side only: `withSystem((tx) =>
tx.delete(marketSeriesCache))` at the top of my own test, the same thing those files' own
`clearCache()` helper does — don't assert on the skip/fetch optimization itself (fragile), assert
the real idempotency invariant instead (row count unchanged across two calls).

A hand-run scratch API + worker + web stack (not `invai-infra`'s `dev:all`) needs three env vars
`dev:all`/CI set for you, or golden-path/E2E steps fail in ways that look like product bugs:
- `MOCK_CARRIER_TRANSIT_HOURS=0.001` (and `_DELIVERY_HOURS`) — unset, the mock carrier's transit
  scan is scheduled a real 2 hours out (`src/modules/shipping/service.ts`), so golden-path test 9
  ("items shipped") always times out at 60s. CI sets this (`invai-web/.github/workflows/e2e.yml`);
  `.env`/`.env.example` do not.
- `WEB_ORIGIN=http://<your web port>` — Better Auth's `trustedOrigins` is `[env.WEB_ORIGIN,
  env.FLOOR_ORIGIN]` (`src/auth.ts`); sign-in from a web dev server on any port other than
  `.env`'s default gets a flat `403 INVALID_ORIGIN`, which surfaces in Playwright as a
  `loginAs` `waitForURL` timeout on *every* test, not an auth-looking error.
- A worker process, not just the API — `production.buildSheets`/`personalization.renderArtwork`/
  `shipping.mockTracking` etc. only run once something drains the queues; without one, golden-path
  steps 4+ time out waiting for state that a job would have set.

`seedMarketDemand()` (for AC5 "no outbound call") relies on `env.mocks.ai`/`env.mocks.census`/
`env.mocks.googleTrends`/etc. all being true locally — confirmed by grepping `.env` for
`ANTHROPIC_API_KEY`/`CENSUS_API_KEY`/`GOOGLE_TRENDS_API_KEY`/`PINTEREST_API_KEY`/
`JUNGLE_SCOUT_API_KEY`, all unset. Recommendations are written inside `computeSignalsForShop`
itself (`compute.ts`'s `computeInTx`), not by the separate `market.trackRecommendations` job — so
calling just `refreshDemand()` + `computeSignalsForShop()` is enough to populate both
`market_signals` and `market_recommendations`; no need to also call `refreshPricing`/
`trackRecommendations` for this card's acceptance criteria.
