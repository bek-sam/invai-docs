# Report: wave 18 step 3, acceptance tests first for market signals
Author: qa-engineer on Fable 5.1, 2026-09-27

Intake: Card: none (wave step 3, QA) Owner: qa-engineer Scope ref: `product/scope.md#market-signals`
(item 16), `#market-and-digest-fences`. Owned (edit): `invai-backend/src/modules/market/*.acceptance.test.ts`,
`invai-backend/src/modules/ai/market.acceptance.test.ts`, `invai-web/e2e/market*.spec.ts`,
`invai-docs/build/qa-report.md`. Read-only: everything else (contract, `src/test/**`, all product code).
Risk flags → co-reviewers: my test files are reviewed by the feature owners (intent) plus `reviewer`.

## Built
- `invai-backend/src/modules/market/market.acceptance.test.ts` (22 tests, T-18-3): AC1, AC3, AC6, AC8, AC10,
  AC16, AC17, AC19, AC21, AC23, AC24, AC25, AC26, AC27, AC30, AC32 (backend), AC33 (backend).
- `invai-backend/src/modules/market/market-prod-mode.acceptance.test.ts` (3 tests): AC22, AC29 with
  `env.isProd = true`, `allowMocks = false` (a `vi.mock` of `src/env` for this file only).
- `invai-backend/src/modules/market/market-outage.acceptance.test.ts` (3 tests): AC20 through
  `env.marketMockFail.add("google_trends")`, at the latest clock in the suite (2027-01) so cache
  `fetched_at` comparisons are clean.
- `invai-backend/src/modules/ai/market.acceptance.test.ts` (9 tests, T-18-4): AC2, AC6, AC7 (assistant
  side), AC8, AC10, AC16, AC30, AC31, AC33, on the mock AI provider through `svc.ask`; every number in
  an answer is checked against the replayed tool outputs of the turn (raw, ÷100, ×100 forms).
- `invai-web/e2e/market.spec.ts` (5 tests, T-18-5): chips + badge + vote cards; one vote, second tap,
  reload rebinding by id; Spanish; niche chip 0/1/2 + one picker refusing a third + clear; designer view.
- `invai-docs/build/qa-report.md` §6: suite table, run commands, AC28 scale-run plan.
- Held-back cases (10, outside the repos): `.claude/agent-memory/qa-engineer/held-back/T-18-3.md`.

Fixture shops are built inside the test files with `withSystem` inserts (companies, users, connections
with an explicit status, designs, blanks + stock levels, products, listings, weekly orders/items with
`isReprint` and cancelled-after-`on_sheet` transitions, profit lines). Time is frozen per describe with
`vi.useFakeTimers({ toFake: ["Date"] })` (timers stay real for pg). Companies and users are created
before the clock is frozen: the shared fixtures' `uniq()` uses `Date.now()` and collided across files.

## AC → test
| AC | Layer | File | Test |
|---|---|---|---|
| 1 | backend | market.acceptance | "AC1: after the jobs, every active design has 1–2 taxonomy niches or is unclassified"; "AC1: signals exist … mock: true on outside sources" |
| 2 | assistant | ai/market.acceptance | "AC2: 'Which of my designs are trending?' calls get_market_trend; every number is in a tool output; …" |
| 2 (badge) | browser | e2e/market.spec | "market chips, the Sample data badge and vote cards render from the stream" |
| 3 | backend | market.acceptance | "AC3: on 2026-09-01 a Halloween design gets October as a peak, an act-by date …, and R1 says list on Amazon and stock its blank" |
| 6 | backend + assistant | both | "AC6: price position on Etsy is `available: false` …"; "AC6: 'Am I priced right?' says there is no approved price source for Etsy …" |
| 7 (assistant side) | assistant | ai/market.acceptance | "AC7 (assistant side): with fewer than 13 weeks the trend answer says 'not enough data' …" (the pure-function AC7 test is the builder's) |
| 8 | backend + assistant | both | "AC8: own data and the outside mock pointing different ways sets the disagreement flag …"; "AC8: the answer names both directions …" |
| 10 | backend + assistant | both | "AC10: signals older than 2× their source TTL read as stale …"; "AC10: … keeps the source and date line and adds `stale.note`" |
| 15 | browser | e2e/market.spec | "in Spanish the starter, chips, badge and vote buttons are Spanish" |
| 16 | backend + assistant | both | "AC16: the jobs, the reads and a vote write no business table" (md5 digest of 13 tables); "AC16: the module's source never writes …"; "AC16: three market answers and a vote change no business table" |
| 17 | backend | market.acceptance | "AC17: an item cancelled after on_sheet and a reprint are not sold units (own yoy stays 0)"; "AC17 (hand SQL) …" |
| 18 | backend | pending | second pass, after T-18-3's history schema |
| 19 | backend | market.acceptance | "AC19: a personalized design compares only against personalized comparables (mock Amazon)" |
| 20 | backend | market-outage.acceptance | 3 tests: refresh doesn't throw and records the source; last good rows kept; reads show the older asOf with lower confidence |
| 21 | backend | market.acceptance | "AC21: with no AI credits the model fallback is skipped …" |
| 22 | backend | market-prod-mode.acceptance | "AC22: a sample workspace gets only mocks even in production, even on a 'live' connection" |
| 23 | backend | market.acceptance | "AC23: A's jobs wrote only A's rows …"; "AC23: the global cache has no shop id and holds only taxonomy queries" |
| 24 | backend + browser | market.acceptance, e2e | "AC24: designer sets niches but is refused recommendations; presser is refused everything; another shop's ids are NOT_FOUND"; "a designer can change a niche but sees no votes or prices" |
| 25 | backend | market.acceptance | "AC25: a shop's niche correction survives the next mapper run" |
| 26 | backend | market.acceptance | "AC26: an unvoted R2 is marked adopted when the price moves ≥ 3% up within 14 days, and gets an outcome 28 days after" |
| 27 | backend + browser | market.acceptance, e2e | "AC27: tapping 'Not useful' twice stores one vote, and the vote wins over adoption detection"; "a vote is stored once, a second tap shows the stored state, and it survives a reload" |
| 28 | scale run | qa-report.md §6 | planned after T-18-3 is green (profile `large`, k6 arrival rate, EXPLAIN) |
| 29 | backend | market-prod-mode.acceptance | "AC29: for a real shop, mockSourcesAllowed is false and no signal, tool or recommendation rests on a mock"; "AC29: the assistant's price-position tool answers `available: false` for Amazon in production" |
| 30 | backend + assistant + browser | all three | "AC30 (backend): a recommendation built on mock comparables is flagged mock …"; "AC30: … carries the `rec.sample` sentence in the answer text"; browser checks the sentence next to the badge |
| 31 | assistant | ai/market.acceptance | "AC31: asking about a trademark-dropped niche gets the fixed `tm.dropped` line, no signal, and never 'not enough data'" (en + es) |
| 32 | backend + browser | market.acceptance, e2e | "AC32 (backend): a designer may set up to 2 niches, a third or an unknown key is refused …"; "AC32 (backend): the taxonomy lists 69 niches …"; "the design page shows the niche chip with 0, 1 and 2 niches; one picker edits both and refuses a third" |
| 33 | backend + assistant + browser | all three | "AC33 (backend): `recommendations.list({ids})` …"; "AC33 (backend): recommendations ride the stream with ids, are stored on the message, and a vote after reload binds to the right one"; browser reload test |

Not mine (builder unit tests or evals, per my spec review): AC4, AC5, AC7 (pure), AC9, AC11–AC14.

## Checks I ran
| Repo | Command | Result |
|---|---|---|
| invai-backend | `node_modules/.bin/tsc --noEmit` | no errors in my files (T-18-4's `assistant-tools.ts` WIP has 5 TS7xxx errors at the time of the run) |
| invai-backend | `node_modules/.bin/biome check src/modules/market/*.acceptance.test.ts src/modules/ai/market.acceptance.test.ts` | "Checked 4 files … No fixes applied", 0 warnings |
| invai-backend | `pnpm lint` (whole repo) | fails on T-18-3's WIP (`config.ts`, `mapper.ts`, `signals.ts` format; `rules.ts` useOptionalChain ×2), none mine |
| invai-web | `pnpm typecheck && pnpm lint` | `tsc --noEmit` clean; "Checked 146 files … No fixes applied" |
| invai-backend | acceptance suites on `invai_t18_qa` / Redis 15 (command in qa-report §6) | **expected red**, below |

```
 ❯ src/modules/market/market.acceptance.test.ts (22 tests | 5 failed | 16 skipped)
     × AC16: the jobs, the reads and a vote write no business table        Cannot find module './jobs'
     × AC21: with no AI credits …                                          Cannot find module './jobs'
     × AC25: a shop's niche correction survives the next mapper run        Cannot find module './jobs'
     × AC32 (backend): a designer may set up to 2 niches …                 market.niches.set is not implemented yet
     × AC32 (backend): the taxonomy lists 69 niches …                      market.niches.taxonomy is not implemented yet
 ❯ src/modules/market/market-prod-mode.acceptance.test.ts (3 tests | 3 skipped)   beforeAll: Cannot find module './jobs'
 ❯ src/modules/market/market-outage.acceptance.test.ts (3 tests | 3 skipped)      beforeAll: Cannot find module './jobs'
 ❯ src/modules/ai/market.acceptance.test.ts (9 tests | 9 skipped)                 beforeAll: Cannot find module '../market/jobs'
 Test Files  4 failed (4)    Tests  5 failed | 32 skipped (37)
```
"skipped" here is vitest not running a block whose `beforeAll` failed (the market jobs module does not
exist yet), not a `.skip`: every block runs the moment `src/modules/market/jobs.ts` registers
`market.refreshDemand`, `market.refreshPricing`, `market.computeSignals`, `market.trackRecommendations`.
No test passes today (the one fixture-only check I had written was removed as not a product test).
The browser spec was not run: it needs the stack with the market jobs run (gate step).

## What's red and why (for the builders)
- T-18-3: `jobs.ts` missing (job names and `{ companyId }` / `{}` inputs assumed from the card); service
  stub throws "not implemented"; tables `market_signals`, `market_series_cache` (`fetched_at`, `source`,
  `query` columns) and ≥ 4 `market_%` tenant tables expected by AC23/AC20.
- T-18-4: tool names in `assistantTools`, `tool_result.mock/sources/recommendations`, prompt v5 copy in
  the mock answers (`rec.sample`, `tm.dropped`, `stale.note`, `disagree.note`, band words, source + date
  lines like "Google Trends, week ending 2026-09-20").
- T-18-5: hooks listed at the top of `e2e/market.spec.ts`: chip copy text, visible badge, vote buttons
  whose accessible name ends with the vote word and carry `aria-pressed`, `role=dialog` picker with a
  `role=combobox` search and `role=option` labels, "Save"/"Guardar".

## Gaps found while writing (filed to the tech lead, not fixed by me)
1. **T-18-2 mock comparables: 3–8 offers per own item** (`src/integrations/market/mock.ts`
   `mockRawOffers`: `3 + hash % 6`). The spec's minimum is n = 8, so price position is almost always
   `too_few_comparables` and R2 can never fire on the mock. AC19, AC26, AC27, AC30, AC33 and the
   browser vote tests need ≥ 8 (say 8–20) comparables. Owner: integrations-engineer.
2. **T-18-2 has no personalization flag** on `PricingProvider.comparables(conn, own)` items or on
   `PriceObservation`, so the spec's step 2.5 filter (AC19) has nothing to filter on. My AC19 test
   passes `personalized` on the own item and expects it echoed on each observation. Owner:
   integrations-engineer (interface), architect if the shape should be in research 14 §4.2.
3. **Seed realism for the browser spec**: the vote tests need at least one recommendation on the seeded
   Desert Bloom after the jobs (30 days of history → own trend `insufficient`). R3 (margin < 15%) or R4
   (rising mock niche) may fire; if none does, the seed needs one thin-margin design or a longer history
   (tech lead's backlog item). Owner: backend-foundation.
4. `market.refreshDemand`'s "records the failure" (AC20) is asserted on the job's return value mentioning
   the failed source; if T-18-3 records it elsewhere (a table, the connection row), tell me and I move
   the assertion.

## Fixture requests (for backend-foundation, through the tech lead; none block this pass)
- `createConnection(companyId, channel, { status })`: today the status is always `csv_only`; I insert
  rows directly in my files.
- `createCompany`/`createUser` ids that don't depend on `Date.now()` (`uniq()` collides under
  `vi.setSystemTime` across files sharing one DB). I create them before freezing time as a workaround.
- A `createDesign`/`createSale({ designId, placedAt, state, isReprint })` pair would shrink every
  market/digest acceptance file by ~150 lines; wave 19's digest tests will need the same shape.

## Decisions
- Static imports for the T-18-3 stubs (`./service`, `./config`) since they landed mid-pass; only the
  missing `./jobs` is loaded through a path constant. Assumed job inputs are stated in the file header.
- AC8's opposing series is found at run time (the first of 24 niches whose mock trend is rising or
  falling), since the mock's per-niche shape is hash-seeded; if none has a direction, the block fails
  with a message naming T-18-2 AC1.
- AC30's "text" assertion lives at the assistant (answer) and web layers: the contract's
  `MarketRecommendation` carries no text (apps render `rule` + `params`), so at the module level the
  test asserts `mock: true` plus a mock source.
- No `it.fails` / `test.fail` markers: the tech lead asked for plain failing tests this wave.

## Processes and data
- Started: none (no API or worker; backend tests ran on Redis DB 15 and `invai_t18_qa`). Test DB
  dropped and Redis DB 15 flushed at the end. Shared dev DB untouched.
