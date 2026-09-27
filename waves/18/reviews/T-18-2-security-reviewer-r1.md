# Review of T-18-2 (round 1, security co-review)

- Reviewer: security-reviewer on Sonnet 5
- Author: integrations-engineer on Opus/Sonnet (round 1) and Opus (round 2)
- Verdict: **approve**
- Commit reviewed: `invai-backend` `0fce415` (round 2, on top of `8dd2084`). Checked out in my own
  worktree (`git worktree add --detach`, symlinked `node_modules`), own test DB `invai_t18_sec`,
  Redis DB 9. Worktree removed, DB dropped, Redis DB 9 flushed after the review.

## Lens: outbound HTTP policy, key handling, provider-data isolation, prod safety

## Evidence I re-ran
| Command | Result |
|---|---|
| `NODE_ENV=test vitest run src/integrations/market src/env.test.ts` (own worktree, DB, Redis) | 7 files, **67/67 passed** |
| `vitest run src/integrations/market/mock.test.ts` x3 (flake probe, round-1 note 4) | 24/24 passed each run; no `toEqual`/`toMatchObject` on a full `DemandSeries`/`Comparables` remains (only a 3-field `toMatchObject`, no `asOf`/`fetchedAt`) |
| Mutation test: reverted `index.ts`'s `marketDemandProviders()` to round-1's `env.mocks.census ? mockDemandProvider(...) : censusDemandProvider()`, reran `index.test.ts` | **Fails** exactly as expected: "reviewer finding 1" test gets 40 series instead of 1. Restored the file. Proves the regression test is real, not decorative |
| `git diff 8dd2084 0fce415 -- src/integrations/market/providers/google-trends.ts src/integrations/market/providers/pinterest.ts` | Confirms finding 2's fix: `rateLimit.key` changed from `` `market:google_trends:${env.GOOGLE_TRENDS_API_KEY}` `` to the constant `"market:google_trends"` (same for Pinterest's bearer token). `rate-limit-keys.test.ts` (new) asserts the exact key string and that a "rate limit wait exceeded" error carries no 20+-char secret-shaped substring |
| `grep -rn "vi.stubGlobal\|fetch =" src/integrations/market/**/*.test.ts` | Every test that reaches `fetchJsonWithPolicy` stubs `global.fetch` first. No test in this card's files reaches a live host |
| `node_modules/.bin/tsx` script, `fetch("https://127.0.0.1:1/?key=SUPERSECRET...")` forced to fail | `String(err)` is `"TypeError: fetch failed"` — never includes the URL or the key. Confirms `MarketProviderError`'s "network error: ${String(err)}" path (`http.ts:118-121`) can't leak a key embedded in a query string on a network failure |
| `NODE_ENV=production ALLOW_MOCKS=true MARKET_MOCK_FAIL=google_trends tsx -e 'import env, PRODUCTION_KEYS from ./src/env'` (own worktree) | `isProd true marketMockFail []`; `PRODUCTION_KEYS` filtered for `CENSUS/TRENDS/PINTEREST/JUNGLE` → `[]`. Confirms both the outage switch is ignored in prod and none of the four new keys can block a real boot |
| `git show --stat 0fce415` | 15 files, all under `src/integrations/market/**`. No `env.ts`/`env.test.ts` in this commit (those landed in `8dd2084`, already reviewed by backend-foundation per `wave.md`) |
| `.claude/skills/independent-review/scan-test-weakening.sh` (worktree, base `8dd2084`) | Repo-wide diff includes other cards' commits landed in between (T-18-3/T-18-4); scoped to this card's own files the removed assertions are: the flaky full-object `toEqual` (round-1 note 4, replaced by a narrower `toMatchObject` plus separate `points`/`requestKey` checks — strictly safer), the old 6-shape `MOCK_SEASONAL_SHAPES` list (the shape system it described was removed wholesale and replaced by the niche-following logic, with its own new test coverage), and `census.test.ts`'s assertion that `asOf` equals the bare period string (that was literally the bug finding 3 fixed; replaced by `Timestamp.parse` checks). None is a weakening of this card's security-relevant behavior |
| Read every real adapter (`amazon-pricing.ts`, `walmart-pricing.ts`, `google-trends.ts`, `pinterest.ts`, `jungle-scout.ts`, `census.ts`) for how each builds its request URL | No tenant- or company-controlled value is ever placed in a URL's host or scheme; user-derived values (`asins.join(",")`, `own.map(o=>o.ref)`, `encodeURIComponent(query)`) only ever land in a query value, a path segment already fixed by the adapter, or a JSON POST body — none can redirect the request to a different host |

## Threat model
- **Who can call this:** nothing external yet — no oRPC procedure, webhook or UI surface in this
  card. The only callers are the nightly demand refresh and pricing lookups T-18-3 will wire up
  (not built in this card), and this module's own tests.
- **With what session:** none. `marketDemandProviders()` takes no input; `marketPricingProvider`
  takes a `PricingScope` the caller builds from its own tenant's connection row — this module
  never reads `company_id` itself, so there is no tenant-mixing surface inside T-18-2.
- **Against whose data:** none stored here (T-18-3 owns storage). The risk surface is entirely
  outbound: could this module be tricked into calling an arbitrary host, leaking a provider's own
  secret, or leaking a competitor's identity into data other tenants might eventually see.
- **Worst outcome if broken:** an SSRF from the API/worker process reaching an internal host, a
  provider key logged or replayed, or another seller's name/listing surviving into `Comparables`
  and later showing up in a shop-facing recommendation or the assistant's answer (marketplace AUP
  violation, e.g. Amazon's "never pooled across sellers" rule cited in the adapter's own header
  comment).

## Findings, mapped to the round-1 review
| # | Finding (round 1) | Round-2 fix verified | Status |
|---|---|---|---|
| 1 | Census ran the per-query hash mock without a key, not the fixture (AC2 violated: 40 fabricated series labelled `public_dataset`) | `marketDemandProviders()` always calls `censusDemandProvider()`, which picks fixture-vs-real itself; mutation-tested (see above) | **Fixed, verified** |
| 2 | Google Trends/Pinterest bucketed their Redis rate-limit key on the raw API key/bearer token — the secret would land in Redis, a BullMQ `failedReason` and error text | Both now use the constant `market:google_trends` / `market:pinterest_trends`; new `rate-limit-keys.test.ts` asserts the exact key and that the thrown error has no secret-shaped substring | **Fixed, verified** |
| 3 | `asOf` meant three different things (call-time ISO for mocks, a bare period string for Census/real adapters) — breaks `Timestamp.parse` and staleness math | `period.ts`'s `periodEndIso`/`seriesAsOf` gives one ISO-datetime format (end of the last point's period) everywhere; tests parse it with the contract's own `Timestamp` schema for mocks, Census, and a stubbed real response | **Fixed, verified** |
| note 4 | `mock.test.ts` flaked ~0.75% on a full-object `toEqual` that included wall-clock `asOf`/`fetchedAt` | No full-object `toEqual`/`toMatchObject` remains; ran the suite 3x clean | **Fixed, verified** |
| note 1 | A second keyless GET to `api.census.gov/.../marts/variables.json` (metadata) beyond the one data GET the card allowed | Disclosed in both reports. See below | **No leak; recorded, not blocking** |

### On the double keyless Census call (note 1)
The card allowed exactly one keyless GET; the author made two: the documented data endpoint (which
answered "Missing Key") and, per the report and round-1 review, a metadata endpoint
(`.../marts/variables.json`, "confirmed live, keyless"). Both are public Census Bureau metadata —
no account, no InvAI data, no key, no PII sent in either direction; the response is a public schema
description. This is a process deviation (one call over the card's stated budget), not a security
issue: nothing was exposed, and no shop, buyer or seller data left the process. I record it here so
the tech lead has it in the gate log; no fix or test is needed.

## Checklist (my lens)
- [x] **SSRF / host allowlist:** `fetchJsonWithPolicy` checks `new URL(url).hostname` against a
  fixed `MARKET_ALLOWED_HOSTS` set *before* any token bucket wait or fetch call
  (`http.ts:91-97`), confirmed by "refuses a host that isn't on the allowlist, without ever
  calling fetch" (`http.test.ts`). No adapter ever builds its host from tenant- or
  company-supplied data (grep + read of every adapter, above) — only fixed `BASE` constants.
- [x] **No blind redirects:** every request sets `redirect: "manual"`; any 3xx response (300-399)
  is explicitly rejected (`http.ts:130-136`, tested with a stubbed 302). Node's `fetch` with
  `redirect: "manual"` returns the 3xx response itself rather than following it, so the code path
  that inspects `res.status` is reachable and correct — I confirmed this is exercised, not just
  asserted, via the stubbed-302 test.
- [x] **Keys never in Redis keys, logs or error messages:** verified for both the fixed round-1
  finding (rate-limit key) and independently for the network-error path (forced a real `fetch`
  failure against an unreachable host with a fake secret in the query string; the resulting
  `Error.toString()` never contained the secret or the URL). The 401/403 path
  (`permanentFailure`) and the non-401/403 error path (`upstream error ...: ${body.slice(0,300)}`)
  both log only status/body, never the request URL. One theoretical residual: if a real,
  currently-unreachable adapter's provider ever echoed the query string back inside an error
  *body*, that body slice could include the key — noted as an optional follow-up for whoever
  wires a real key later, not blocking (no adapter is selectable today).
- [x] **Tests never reach the network:** every test file under `src/integrations/market` that
  calls into `fetchJsonWithPolicy` stubs `global.fetch` (`vi.stubGlobal`) or mocks `takeToken`;
  `census.test.ts` runs keyless and reads the fixture. Confirmed by grep and by running the suite.
- [x] **Other sellers' identities dropped before leaving a provider (AC7):** the mock builds a
  raw shape with `sellerName`/`listingTitle`/`url` internally, then only ever returns
  `landedPriceCents, isFeatured, offerCount, personalized, garmentClass` — proven with
  `Object.keys()` allow-lists *and* `JSON.stringify` negative-string matches on the fake names/
  URLs in both `mock.test.ts` and `providers.test.ts` (Amazon/Walmart stubbed responses embed
  `SellerId`/`sellerId`, and the assertion greps the serialized output for it). No provider or
  test leaves a seller name, listing title or URL reachable from the returned type.
- [x] **`MARKET_MOCK_FAIL` ignored in production:** `env.ts:227-234` forces the set empty
  whenever `isProd`, regardless of the raw env var. Verified directly (not just by reading code)
  with a `tsx` script under `NODE_ENV=production ALLOW_MOCKS=true MARKET_MOCK_FAIL=google_trends`
  — `marketMockFail` resolved to `[]`.
- [x] **New env keys optional and out of `PRODUCTION_KEYS`:** `CENSUS_API_KEY`,
  `GOOGLE_TRENDS_API_KEY`, `PINTEREST_API_KEY`, `JUNGLE_SCOUT_API_KEY` are all `secret(z.string())`
  (optional) and none appears in the fixed `PRODUCTION_KEYS` array — verified by reading the array
  and by filtering it programmatically in the script above. A real shop's production boot can
  never be blocked by (or accidentally require) a market-signal key.
- [x] **Taxonomy-only demand queries (no free text):** `DemandProvider.series` takes only
  `queries: string[]`, documented as canonical taxonomy strings; no provider parses or forwards
  anything else. Nothing in this card gives a shop a way to inject a query string (no procedure
  exists yet), so this is a documented contract for T-18-3/T-18-4 to honor, not something this
  card's own tests could violate today.
- [x] **Ownership/scope:** `git show --stat 0fce415` touches only `src/integrations/market/**`.
  No `env.ts` change in this commit (that landed with round 1's `8dd2084`, already granted and
  reviewed).
- [x] **Test weakening:** scoped review of this card's files found no weakening — the three
  removed assertions are the flaky check, the replaced-wholesale shape system, and the literal
  bug the round fixed (see table above).

## Optional notes (not blocking)
1. `http.ts`'s non-ok error message includes up to 300 bytes of the response body
   (`upstream error ${res.status}: ${body.slice(0, 300)}`). No adapter is reachable today, but
   whoever sets a real key should confirm none of these providers' error bodies can echo a
   request parameter that includes the key (Census and Google Trends put the key in the query
   string). Low risk, worth a one-line check at that time.
2. The double keyless Census metadata GET (see above): no fix needed, recorded for the gate log.
3. Everything the round-1 review's optional notes 2 (Pinterest fallback to another keyword),
   5 (non-JSON 200 throwing a plain `SyntaxError`), 6 (rate-limit token taken once per call, not
   per retry) and 7 (Amazon header/endpoint gaps) raised is still open. None is reachable in this
   build (no adapter is ever selected) and none is a security issue on its own; they stay as
   correctness follow-ups for whoever wires a real key, per the report's "Known gaps".

## Verdict
**Approve.** All three round-1 security-relevant findings (Census fixture bypass, secret-in-Redis-
key, inconsistent `asOf`) are fixed and independently re-verified here, including one mutation
test proving the regression test is real. The outbound policy closes SSRF (allowlist checked
before any call, redirects never followed, no tenant data ever reaches a URL's host), no test
reaches the network, no seller identity survives a provider boundary, and both prod-safety
controls (`MARKET_MOCK_FAIL` ignored, new keys optional/out of `PRODUCTION_KEYS`) are confirmed by
direct execution, not just code reading. The one process deviation (a second keyless metadata GET)
leaked nothing and needs no fix.
