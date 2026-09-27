# Review of T-18-3 (round 1)

- Reviewer: architect on claude-sonnet-5
- Author: backend-engineer (market) on claude-opus-5-5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend diff --stat origin/main..72e3e59 -- src/modules/market src/db/schema/market.ts drizzle/0027_market_signals.sql src/db/schema/index.ts src/api/router.ts src/modules/jobs.ts src/db/rls-coverage.test.ts` | 25 files, all inside owned paths / named grants; includes QA's `*.acceptance.test.ts` files only because they already exist on the branch, not authored here |
| `git worktree add -d /tmp/invai-review-t183-1 72e3e59` (symlinked `node_modules`, own `.env`), `tsc --noEmit -p .` | Only error is pre-existing `src/modules/ai/service.ts(1461,38)` (T-18-4 WIP, unrelated overload on `ai_credit_ledger.kind`); nothing in `src/modules/market/**` or `src/integrations/market/**`. Worktree removed after. |
| `grep -n "from \"\.\./\.\./integrations\|from \"\.\./\.\./ai"` in `src/modules/market/*.ts` (non-test) | Only `deps.ts` imports `../../integrations/market` (the index) and `../ai/niche`; `jobs.ts` imports a type only, also from the same index. No internals reached. |
| `grep -rln "from \"\.\./market/service\|\.\./\.\./market/service"` in `src/modules/ai/*.ts` | `assistant-tools.ts` and `service.ts` import only `../market/service` (public); nothing reaches `market/compute.ts`, `jobs.ts`, `read.ts` etc. |
| `grep -n "mockSourcesAllowed" src/modules/market/*.ts` | Defined once in `config.ts`; `compute.ts`, `jobs.ts`, `service.ts` (5 call sites) all call the same function — one predicate, no duplicate logic. |
| Read `service.ts`, `read.ts`, `router.ts`, `jobs.ts` (`asOfDate`), contracts `src/schemas/market.ts`, `src/schemas/common.ts` | All exported functions are `(tx, ctx, input)`; router matches contract exactly incl. cursor pagination (`listRecommendationsPage`/`keyset`) and `ids`; `SignalProvenance.asOf` is written via `row.asOf.toISOString()` at read time, and stored via `asOfDate(s.asOf)` (`new Date(...)`) at write time from T-18-2's now-ISO-datetime provider `asOf` — round-trips through `Timestamp = z.iso.datetime({offset:true})` cleanly (`Z` suffix satisfies `offset:true`). |

## Acceptance criteria (cross-module interface subset)
| # | Met? | Evidence |
|---|---|---|
| `service.ts` exports exactly the agreed functions, `(tx,ctx,input)`, contract-shaped output | yes | `getTrendSignal`, `getSeasonalitySignal`, `getPricePosition`, `simulatePrice`, `listRecommendations`, `listRecommendationsPage`, `voteRecommendation`, `recordRecommendationsShown`, `listDigestMarketItems`, `getDesignNiches`, `setDesignNiches`, `nicheTaxonomy`, re-exports `NICHES`/`nicheLabel`/`mockSourcesAllowed` — matches `wave.md` "Agreed interfaces" line for line |
| Output passes contract Zod parse, incl. `SignalProvenance.asOf` after T-18-2 r2's ISO-datetime change | yes | `provenanceOf()` / `toRecommendation()` build `MarketTrend`/`MarketSeasonality`/`PricePosition`/`MarketRecommendation` with `.toISOString()` on stored `Date` columns; write path normalizes any provider `asOf` string through `asOfDate()` before storage, so the schema shape is decoupled from the provider's string format |
| `listDigestMarketItems` fit for wave 19 | yes | filters `band ∈ {high, medium}` via `bandAtLeast`, `!stale`, tenant-scoped (own designs/niches by construction), applies `mockSourcesAllowed`, trademark-screens niche labels and idea terms before returning; each item carries `sources` (source+asOf), `band`, `mock` per `MarketRecommendation` schema |
| Router implements contract incl. cursor pagination and `ids` | yes | `router.ts` `market.niches.{taxonomy,get,set}` / `market.recommendations.{list,vote}`, `list` delegates to `listRecommendationsPage` (keyset pagination), `RecommendationListInput.ids` wired through to the `inArray` filter |
| Market → T-18-2 only via `src/integrations/market/index.ts`; → T-18-4 only via `src/modules/ai/niche.ts` | yes | `deps.ts` is the sole funnel; no other file in `src/modules/market/**` imports integrations or ai internals |
| No import from market into other modules' internals beyond their public services | yes | `src/modules/ai/{service,assistant-tools}.ts` import only `../market/service`; no other module references `market/*` at all |
| `mockSourcesAllowed` single predicate used everywhere | yes | one definition, 5+ call sites, no parallel mock-visibility check found |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat`)
- [x] Nothing outside scope (cross-module interfaces match `wave.md`'s "Agreed interfaces" verbatim)
- [x] Tests exercise the behavior; round 2's `service.test.ts` change (S-34) strengthens an assertion, doesn't weaken anything I can see
- [x] Tenancy / RLS is backend-foundation's and security-reviewer's call (both already approved); I checked only that `market_series_cache` stays reachable solely through `deps.ts`/`jobs.ts` under `withSystem`, consistent with ADR 0015
- [ ] Decisions recorded where needed — n/a, no new cross-cutting decision beyond ADR 0015 (already recorded by T-18-1)

## Optional notes (not blocking)
- `asOfDate()` (`jobs.ts:51`) keeps a dead `^\d{4}-\d{2}$` branch for a Census month-only `asOf` format that the provider no longer emits (T-18-2 now sends full ISO datetimes for Census too, per `census.ts:106`). Harmless — the `new Date(s)` fallback handles the current format — but worth deleting next time this file is touched, so a future reader doesn't assume that shape still arrives.
