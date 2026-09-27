# Wave 18: market signals for the assistant

- Dates: 2026-09-27 →
- Goal (user outcome): an owner or office user asks "Which of my designs are trending?", "Am I priced right?" or "When should I get ready for Halloween?" and gets an answer built only from the shop's own data and compliant sources (mocks labelled "Sample data"), with source, date and confidence on every outside fact, a fixed action per recommendation, and Done / Not useful buttons.
- Spec: `specs/market-signals.md`. Scope: `product/scope.md#market-signals` (item 16) and `#market-and-digest-fences`. Owner approval: OI-6 (2026-09-27). Decision: `decisions/0014`. Backlog: B-117..B-121.
- Taxonomy: `product/market-niches.md` (PM-owned; T-18-3 converts it to a data file).
- Rules: `team/agent-brief.md`. **Every prompt says "Don't push; only the tech lead pushes after the gate."** Every grant is written below in the same step it is given.
- Plan reviewed by: architect (2026-09-27, approve-with-changes; all 8 changes applied), product-manager (2026-09-27, approve; AC1–AC33 all have a home). Spec reviews (designer, QA, customer-success) folded by the PM; both specs `ready`. Reviews in `reviews/plan-pm.md`, `reviews/plan-architect.md`.

## Hard fences (from scope.md; a reviewer blocks any card that crosses one)
- No scraping, scraper APIs, unofficial Trends libraries, or reading marketplace/competitor web pages.
- No cross-shop use of marketplace-origin data. The only table without `company_id` is the global demand cache (ADR 0015), which holds taxonomy queries and public-source series only.
- Nothing writes prices, listings, ads or POs.
- **Mock visibility rule (spec AC29–AC30, architect plan review item 1):** mock sources are used and shown only when `!env.isProd || env.allowMocks || await isSampleWorkspace(companyId)` (`src/modules/tenancy/demo-flag.ts`; not `companies.demo`, which the seeded Desert Bloom has set). Otherwise a mock source is no source: R2/R4 don't fire, `PricePosition.available = false, reason: no_compliant_source`, mock demand rows are skipped. One predicate, `mockSourcesAllowed(companyId)` in `src/modules/market/config.ts` (T-18-3), applied by `computeSignals`, every read and `refreshPricing`. Where mock data is shown, "Sample data" is also in the recommendation's text.
- No Etsy/TikTok/Shopify competitor data. Every outside source runs on its mock; no real keys, accounts or spend. Census: the real client exists but runs only when `CENSUS_API_KEY` is set; tests and dev use the recorded fixture.
- No forecasting model; only the labelled price-response estimate.

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| T-18-1 Market contract + ADR 0015 (global cache) | architect | fable | reviewer (opus) + backend-foundation, web-engineer (consumer), security-reviewer (ADR, tenancy) | tenancy, contract | planned |
| T-18-2 Market providers + deterministic mocks | integrations-engineer | sonnet | reviewer (opus) + security-reviewer, backend-foundation (`env.ts` hunk only) | outbound-http, marketplace-policy | planned |
| T-18-3 Market module: taxonomy, mapper, signals, rules R1–R5, recommendations, jobs, feedback | backend-engineer (market) | opus | reviewer (sonnet) + backend-foundation (migration, new tables, grants), security-reviewer (tenancy), architect (cross-module interfaces) | tenancy, migration, data-integrity | planned |
| T-18-4 Assistant market tools, niche route, prompt v5, validator, evals | ai-engineer | opus | reviewer (sonnet) + security-reviewer (injection, tenancy), qa-engineer (assistant golden-path area) | ai, tenancy | planned |
| T-18-5 Web: chips, starters, sample-data badge, votes, niche chip | web-engineer | sonnet | reviewer (sonnet) + product-designer, qa-engineer (assistant area) | ui | planned |

## Order and ownership
1. **T-18-1** first. QA starts acceptance tests (`acceptance-tests-first`) from the cards at the same time and finishes them against the landed contract.
2. **Stubs day 1** (each provider commits its stub before consumers depend on it; stubs that touch `db/schema` ship with their migration and pass backend tests, lessons 2026-09-26):
   - T-18-2: `src/integrations/market/types.ts` + `index.ts` with the selection functions returning mocks.
   - T-18-3: `src/modules/market/service.ts` exporting the read functions below (may throw `not implemented` until built) and the taxonomy export.
   - T-18-4: `src/modules/ai/niche.ts` exporting `classifyDesignNiche` and `screenMarketTerms` (stub may return `null` / pass-through until built; must be real before review).
3. **T-18-2, T-18-3, T-18-4** build in parallel after T-18-1 lands (3 builders + QA = 4 agents).
4. **T-18-5** starts when T-18-3's router and T-18-4's events work on a dev API.
5. Reviews start as each card reports.

| Card | Owns (exclusive) |
|---|---|
| T-18-1 | `invai-contracts/src/contract/market.ts` (new), `src/schemas/market.ts` (new), `src/contract.ts` (register `market`), `src/schemas/ai.ts` (`AssistantEvent`: tool names + provenance/recommendation fields), `src/roles.ts` + `roles.test.ts` (new permission if chosen), `src/index.ts` exports, `package.json` version, `CHANGELOG.md`, `src/compat.ts` if needed; `invai-docs/decisions/0015-global-market-cache.md` + its index row |
| T-18-2 | `invai-backend/src/integrations/market/**` (new) |
| T-18-3 | `invai-backend/src/modules/market/**` (new; except QA's `src/modules/market/*.acceptance.test.ts`), `invai-backend/src/db/schema/market.ts` (new) + its migration under `invai-backend/drizzle/` |
| T-18-4 | `invai-backend/src/modules/ai/assistant-tools.ts` + test, `src/modules/ai/service.ts` + `service.test.ts` (only the `tool_result` pass-through of provenance/recommendations and `getConversation` returning stored recommendations), `src/modules/ai/niche.ts` (new) + test, `src/ai/**` (niche route, prompt v5, validator, mock provider), `invai-backend/evals/assistant/**`, `invai-backend/evals/market/**` (new), `invai-backend/evals/baseline.json` (assistant + market entries) |
| T-18-5 | `invai-web/src/routes/_app/assistant.tsx` and components it owns, `invai-web/src/routes/_app/catalog/designs.$designId.tsx`, `invai-web/src/i18n/en.ts` + `es.ts` (market and assistant keys only), new web files under `invai-web/src/components/market/**` |
| QA | `invai-backend/src/**/*.acceptance.test.ts` for market, `invai-web/e2e/market*.spec.ts`, `invai-docs/build/qa-report.md` |

## Grants (written when given)
- 2026-09-27 T-18-2: `invai-backend/src/env.ts` and `src/env.test.ts`, only to add market provider keys (`CENSUS_API_KEY`, `GOOGLE_TRENDS_API_KEY`, `PINTEREST_API_KEY`, `JUNGLE_SCOUT_API_KEY`; all optional, none in `PRODUCTION_KEYS`), their `env.mocks` entries and a `MARKET_MOCK_FAIL` test switch. backend-foundation co-reviews that hunk.
- 2026-09-27 T-18-3: one-line registrations in `invai-backend/src/db/schema/index.ts` (export), `src/api/router.ts` (`market: marketRouter`), `src/modules/jobs.ts` (`import "./market/jobs"`). backend-foundation co-reviews.
- 2026-09-27 T-18-3: `invai-backend/src/db/rls-coverage.test.ts`, two edits only: add `market_series_cache` to `PUBLIC_READ_TABLES` and to the "app role cannot write the global catalogs" list (ADR 0015's enforcement test). security-reviewer (owner of RLS suites) and backend-foundation co-review that hunk.
- 2026-09-27 T-18-4: `invai-backend/src/modules/ai/service.ts` + `service.test.ts`, scoped to the `tool_result` pass-through (provenance, recommendations) and `getConversation` returning stored recommendations from `assistant_messages.toolCalls` (jsonb, no migration). Architect plan review item 3.
- 2026-09-27 T-18-4: `invai-backend/src/db/schema/ai.ts`, only to add values to `AI_JOB_KINDS` / credit kinds for the niche route (`enumText`, so no migration). backend-foundation co-reviews that hunk if touched.

- 2026-09-27 T-18-1 (follow-up, with its review round): `invai-contracts/README.md`, add the `market` namespace row and `market.niches.manage` (the repo owner's README).
- 2026-09-27 note: from contract `92b9260` until T-18-3's first commit, `invai-backend` typecheck fails at `src/api/router.ts` ("Property 'market' is missing"). T-18-3's first commit is the stub router + the granted `market: marketRouter` line, so everyone else is green again.

- 2026-09-27 note: `src/modules/privacy/tenant.test.ts` fails with 42P01 in the shared tree because T-18-3's uncommitted `src/db/schema/index.ts` exports `market.ts` before its migration exists (the privacy export enumerates every tenant table). Transient; the gate re-runs the full backend suite on committed code and must see it green.

- 2026-09-27: T-18-3 gains AC 2b (S-34: refresh the whole taxonomy, not a usage-derived subset). No new paths. T-18-1 follow-up (with the README grant): ADR 0015 §4 says the same in one sentence.

- 2026-09-27 T-18-4 (retroactive, requested in its report): one-line `market` registration in `invai-backend/evals/run.ts`; commit `74268c3` (message ordering tie-break inside `ask()` in `src/modules/ai/service.ts`, just outside the scoped grant; fixes a flaky T-17-3 test). Both go through T-18-4's review.
- 2026-09-27 T-18-1 follow-up (architect): add `market_niche` to the contract's AI credit kinds, then T-18-4 switches the niche route's charge from `sku_suggestion` to `market_niche` (small follow-up in T-18-4's round 2).

## Round log (2026-09-27)
- T-18-1: reviewer, security-reviewer, backend-foundation approve (r1). Follow-up `378d6ae` (contracts 0.6.1: README rows, `market_niche` credit kind) and ADR clarification `8c76076`. Consumer co-review (web-engineer) runs as the first step of T-18-5.
- T-18-2: reviewer r1 changes-required (Census fixture, API key in Redis key, `asOf` format) + QA/cross-card mock gaps → round 2 in progress.
- T-18-3: reviewer r1 approve; security r1 changes-required (S-34 equality test) → fixed in `72e3e59`; security r2, backend-foundation and architect co-reviews pending. `simulate_price` 100x bug confirmed fixed by `c2057df` (reviewer hand calculation).
- T-18-4: reviewer r1 changes-required ("Sample data" missing in two code-written answers, so the fail-closed fallback failed its own rule) → fixed in `1b57f13` (also `market_niche` in backend `CREDIT_KINDS`); reviewer r2, security and QA co-reviews pending. The niche route still charges `sku_suggestion` (switch later; small).

- T-18-2 round 2: `0fce415` (census fixture, constant rate-limit keys, ISO `asOf`, n ≥ 8 with a documented thin case, `personalized` + optional `garmentClass`, niche-following mock seasonality and deterministic rising/falling niches). Reviews pending.
- T-18-3 approvals complete: reviewer r1, security r2, backend-foundation r1, architect r1.
- **Decision (tech lead, 2026-09-27) on AC19:** the comparable filter belongs to normalize (spec Step 2.5), i.e. T-18-3's `filterComparables`; providers return the raw mix. QA's AC19 test asserts on the filtered comparables used by price position, not on the provider output.
- Follow-up (PM, backlog B-131): the seasonality index (spec Step 3) is computed from history that isn't detrended, so a steadily rising niche shows up partly as "seasonality" and the deseasonalized trend understates it. Found by T-18-2 while tuning mocks. Per spec as written; not a wave 18 blocker.

- T-18-2: security-reviewer and backend-foundation (env hunk) approve; reviewer r2 changes-required on one new bug (ISO week end in `period.ts`). Round 3, limited to that fix, decided by the tech lead: OI-16 (FYI).

- T-18-1 all approvals (reviewer, security, backend-foundation, web-engineer consumer). T-18-2 approved r3 (`480302c`); security and backend-foundation approve. T-18-4 all approvals (reviewer r2, security, qa-engineer). QA second pass `0bc68e2`: 39/39 acceptance tests green; full backend 928/928.
- T-18-5 built `ab961f3`; reviews pending.
- **Decision (tech lead, 2026-09-27):** every `ai.assistant.ask` stream logs one `net::ERR_ABORTED` in Chrome although the response is 200 and the stream complete (oRPC client cancels its reader after the last event; predates wave 18). QA's `watchPage` may allow-list exactly that request (`POST /rpc/ai/assistant/ask`, `ERR_ABORTED`, only after a `done` event was received); every other failed request still fails the test. Root-cause follow-up: B-132.
- QA follow-ups in `e2e/market.spec.ts` / `e2e/helpers/ui.ts` (QA-owned): exact, container-scoped starter locator; `loginAs` works with the Spanish login label; niche test starts from a known niche state.

## Cross-card findings routed
- From T-18-4's live run: `simulate_price` returns candidate prices 100x too large on the seed ($2,429.00 against a $15.00 floor) → T-18-3 round 2.
- From T-18-3 and T-18-4 runs: T-18-2's mock seasonal shapes are picked by hash, so Halloween queries don't peak in October (spec AC3), and no mock niche series rises or falls ±15% per 4 weeks (AC8/AC10) → T-18-2 round 2b: mock shape follows the niche's peak months from the taxonomy; a deterministic subset of queries rises or falls.
- QA fixture bugs found by T-18-3: product prices entered in dollars (contract is cents, AC26/AC30); a -3-day offset with a Tuesday "now" leaves the last complete ISO week empty (AC17) → QA second pass.
- T-18-4 decision to check in review: market terms are dropped at trademark risk ≥ 60 (the default threshold dropped 25 real niches, e.g. "St. Patrick's Day").

## QA findings routed (acceptance tests first pass, `reports/QA-acceptance.md`)
1. T-18-2 mocks return 3–8 comparables, below the spec's n ≥ 8, so price position and R2 never fire on mocks → T-18-2 round 2 (mocks return enough comparables, some below 8 for the thin case).
2. T-18-2 comparables carry no personalization flag or garment class, so AC19's filter can't be proven → T-18-2 round 2.
3. Seed may give no recommendation for the browser vote test (30-day history) → checked at the gate; R1 on the seed's Halloween designs is the expected source; B-130 for longer history.
4. AC20 "records the failure": T-18-3 states where (job result and a stored field) in its report.
5. Fixture helper requests for backend-foundation (connection status, clock-independent `uniq()`, design/sale helpers) → backlog, not this wave.

## Contract landed (T-18-1)
- `invai-contracts` `92b9260` (0.6.0); ADR [0015](../../decisions/0015-global-market-cache.md) in `invai-docs` `e13cdda`. Exact exported names are in `reports/T-18-1.md`. Routes: `GET /market/niches/taxonomy`, `GET|PUT /market/niches/design`, `GET /market/recommendations/`, `POST /market/recommendations/{id}/vote`.

## Agreed interfaces (names fixed here; the architect's plan review may refine signatures)
**Contract (T-18-1, provider architect; consumers T-18-3, T-18-4, T-18-5):**
- Tool names added to `AssistantEvent.tool_call.name`: `get_market_trend`, `get_seasonality`, `get_price_position`, `simulate_price` (additive, at the end).
- `AssistantEvent.tool_result` gains optional `mock?: boolean`, `sources?: {source: SignalSource, asOf: Timestamp, mock: boolean}[]`, `recommendations?: {id: Id, rule: R1..R5, band: ConfidenceBand, mock: boolean}[]`. No new union member. `AssistantMessage` gains optional `recommendations?` (same item) and `mock?: boolean`. "Shown" = every recommendation carried in a `tool_result` of the turn, capped at 3 per tool; the web renders vote cards from the event, not from the answer text.
- Procedures (router key `market`): `market.niches.taxonomy()` (keys + en/es labels), `market.niches.get({designId})`, `market.niches.set({designId, niches: string[] ≤ 2})`, `market.recommendations.list(Page.extend({designId?, ids? (≤ 20)})) -> paginated(MarketRecommendation)` (cursor pagination per `contract.test.ts`; the service may return an array and the router wraps it), `market.recommendations.vote({id, vote: "done" | "not_useful"})` (idempotent). `MarketRecommendation` carries `vote: done | not_useful | null` and `votedAt`.
- Permissions: `niches.get`/`niches.taxonomy` use `catalog.read` (owner, admin, office, designer); `niches.set` uses a new `market.niches.manage` (all shop admins, `OFFICE`, `DESIGNER`); recommendations list/vote use `finance.read`; presser/packer/receiver/vendor get none (spec AC24).
- Shared Zod schemas the service returns and the web renders: `SignalProvenance {source, licence, asOf, fetchedAt, mock}`, `ConfidenceBand = high | medium | low`, `MarketTrend`, `MarketSeasonality`, `PricePosition`, `PriceSimulation`, `MarketRecommendation`.

**Integrations (T-18-2, provider; consumer T-18-3)** in `src/integrations/market/index.ts`:
- Types per research 14 §4.2: `SignalSource`, `Licence`, `DemandSeries`, `Comparables`, `DemandProvider`, `PricingProvider`.
- `DemandProvider` and `PricingProvider` carry `readonly mock: boolean` so T-18-3 can apply the mock visibility rule without a call.
- `marketDemandProviders() -> DemandProvider[]` (key set → real, else mock, like `carriers/index.ts`; includes Census as source `census`, granularity `month`). The nightly refresh is global, so no per-company rule here.
- `marketPricingProvider(scope: { sampleWorkspace: boolean; channel; connection }) -> PricingProvider | null` (Amazon, Walmart only; `null` for Etsy, TikTok, Shopify; sample workspace → mock).
- `censusRetailSeries({ years }) -> DemandSeries` (convenience; NAICS 448, monthly, NSA; fixture when no key).

**Market module (T-18-3, provider; consumers T-18-4 now, wave 19 digest later)** in `src/modules/market/service.ts`, all `(tx, ctx, input)` inside the caller's `withTenant`:
- `getTrendSignal({designId} | {niche}) -> MarketTrend`
- `getSeasonalitySignal({designId} | {niche}) -> MarketSeasonality`
- `getPricePosition({designId, channel}) -> PricePosition` (`available: false` + reason when no compliant source)
- `simulatePrice({designId, channel, prices?}) -> PriceSimulation`
- `listRecommendations({designId?, minBand?, limit}) -> MarketRecommendation[]`
- `recordRecommendationsShown({ids, shownIn: "assistant" | "digest", refId?})` (`refId` = the assistant `messageId` or the digest id)
- `mockSourcesAllowed(companyId) -> Promise<boolean>` (in `config.ts`; the one mock visibility predicate)
- `listDigestMarketItems({asOf}) -> MarketRecommendation[]` (R1–R5, band ≥ medium, own designs/niches only, trademark-screened, not stale; for wave 19)
- `NICHES` (taxonomy data) and `nicheLabel(key, lang)`.

**AI (T-18-4, provider; consumer T-18-3)** in `src/modules/ai/niche.ts`:
- `classifyDesignNiche(companyId, { designId, name, tags, niches: { key, labelEn }[] }) -> { niche: string | null; confidence: number } | null` (Haiku route through the gateway; `null` when credits are out; accepted by the caller only at ≥ 0.7).
- `screenMarketTerms(companyId, terms: string[]) -> { allowed: string[]; droppedCount: number }` (wraps the existing trademark check; logs a counter for drops).

## Ports, test DBs, Redis DBs (one each, never shared)
| Who | API port | Test DB | Redis DB |
|---|---|---|---|
| T-18-2 | 3121 | `invai_t18_2` | 11 |
| T-18-3 | 3131 | `invai_t18_3` | 12 |
| T-18-4 | 3141 | `invai_t18_4` | 13 |
| T-18-5 | 3151 | (none) | 14 |
| QA | 3161 | `invai_t18_qa` | 15 |
| Reviewers | 3171–3179 | `invai_t18_rev_<card>` | 10 |
Port 3142 is an orphaned API from before this wave (PID 16765); leave it alone. Port 54322 belongs to another project.

## Canary
Not planted. On 2026-09-27 the tech lead's dispatch asking the T-18-3 owner to commit a hidden known defect for the reviewers to find was denied by the session's permission system (auto-mode classifier). The team didn't try another route. Asked the owner how canaries should be run: OI-15.

## Interruptions
- 2026-09-27: the session usage limit stopped every running agent (T-18-2 round 2 mid-way, T-18-4 final checks, T-18-3 reviewer and security co-review before writing anything). After the reset: state checked (only T-18-2's round-2 files were uncommitted; no stray worktrees; listeners on 3000/3142 are `tsx watch` restarts not started by this wave). Resumed with fresh agents carrying the context (T-18-2 round 2 incl. 2b, T-18-3 review, T-18-4 review), 3 at a time.

## Integration gate (2026-09-27, `reviews/gate.md`)
- [x] Contracts links point to `../../../invai-contracts`; `df -h /` 15 GB free
- [x] All repos: contracts 52 tests, backend 928, web 88 + build, floor 96 + build
- [x] Fresh reset, migrate, seed; API golden path 13/13 (film use 0.87), browser golden path 13/13, screens smoke 2/2, market 5/5, floor 3/3. **The full `pnpm e2e` in one run fails** because the suite's assistant traffic drains the per-company `ai` rate bucket (B-133, pre-existing since T-12-3; each suite passes alone on the same seed). Tech lead decision: push; B-133 is a wave 19 candidate (always-in-scope bug).
- [x] Market jobs ran by the worker's own scheduler on the fresh seed (40 niches, 482 signals, 12 R1 recommendations, all labelled sample data); 3 starters in English and 1 in Spanish answered with sources, dates, "Sample data" and vote cards; designer refused
- [x] Key screens looked at by the tech lead (gate-shots 01–03). Found: raw `**` markdown and an English demo footer in Spanish (B-135), an R1 act-by date in the past for a peak already under way (B-136). Low, filed.
- [ ] QA scale run for AC28 (5,000 designs): not run as a separate QA pass in this wave; T-18-3's budget check timed `computeSignals` at 12.2 s for 5,000 designs × 156 weeks (target 15 min). Carried into wave 19's gate checklist.
- [x] Pushed to `main` (commits: see "Pushed")

## Team metrics
| First-pass approvals | Canary caught? | Escaped defects | Reopened | Avg cycle time | Tokens per card |
|---|---|---|---|---|---|
| Primary reviewer r1: 3 of 5 (T-18-1, T-18-3, T-18-5). All required reviewers r1: 2 of 5 (T-18-1, T-18-5). T-18-2 took 3 rounds (OI-16), T-18-3 and T-18-4 took 2 | not planted (denied by the session's permission system; OI-15) | 1 Low found at the gate after approval (B-136, act-by in the past; the spec didn't cover a peak already under way). Plus 1 pre-existing Medium made visible (B-133) | 0 cards reopened after approval | about 10 h wall clock from plan to gate, including two usage-limit stops (about 3 h lost) | builders about 230k–550k per run (T-18-2 about 1.2M over 3 rounds; T-18-3 about 340k; T-18-4 about 520k over 2 rounds; T-18-5 about 470k); each review 75k–230k; gate about 230k |

## Retro
- **What worked:** spec reviews before planning caught the real product risk (customer-success: mock data reaching a real shop → the mock visibility rule, AC29/AC30) and the untestable seed assumptions (QA). The architect's plan review removed three mid-wave grants. Independent reviews caught three real defects the authors' tests missed: Census fixture not used and an API key used as a Redis key (T-18-2), the fail-closed fallback failing its own "Sample data" rule (T-18-4), and an ISO-week bug in the round-2 fix (T-18-2 r2). Cross-card finds (the 100x `simulate_price` prices, mock shapes that never trended) were routed and fixed inside the wave.
- **What slipped:** two usage-limit stops ended every running agent; resuming needed fresh agents because SendMessage wasn't available to the tech lead, and orphaned dev processes had to be found by their env. Docker hung once (OrbStack restart). The first T-18-2 run skipped its stub commit and made two Census calls where the card allowed one (public data, no key; recorded). The full browser suite can't pass in one run until B-133. No canary. The QA scale run for AC28 didn't happen as a separate pass.
- **Recurring:** memory written under `invai-docs/.claude/` again (third time), because this session started inside `invai-docs`, so agents resolve project memory there and the memory guard fails open. Promoted: every agent prompt now names its absolute memory path (`/Users/bekbolsun/invai/.claude/agent-memory/<role>/`), and the owner should start the tech lead from `invai/` (report).
- **Lessons added:** `team/lessons.md` rows dated 2026-09-27 (usage-limit orphans, kill of explicit PIDs as its own command, fail-closed fallback test, canary denied, memory path recurrence).
- **Decisions:** ADR 0015 (global market cache); tech-lead decisions in this file (AC19 filter location, the `ERR_ABORTED` allow-list, OI-16 round 3).
