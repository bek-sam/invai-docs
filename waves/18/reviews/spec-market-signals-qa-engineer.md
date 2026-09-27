# QA review: spec/market-signals.md (wave 18)

Reviewer: qa-engineer. Verdict: **changes-required** (seed/fixture gaps block several ACs as written; wording fixes needed for 3 ACs before tests can be written).

## AC table

| AC# | Testable? | Level | Fixture/seed needed (gap if missing today) | Note |
|---|---|---|---|---|
| 1 | Partial | backend acceptance (`market.acceptance.test.ts`) | Fixture: design with tags + a stubbed provider response; seed alone gives only ~30 days of history, not enough for any real trend/seasonality signal | Split: "1-2 niches or unclassified" testable on seed today; "signals exist with source/asOf/n/confidence/mock:true" needs a fixture-built design with enough weekly history, not the raw seed |
| 2 | Yes | API E2E (`api-golden-path` extension) or backend acceptance | none beyond seed + mock provider | Number-match and "sample data" string are both checkable |
| 3 | No, as written | backend acceptance (frozen time) | **Seed gap**: no design has an Amazon **connected** listing — seed's amazon connection is `status: "csv_only"`, never `"connected"` (`invai-backend/src/db/seed/builder.ts` ~L344-352). AC says "while Amazon is connected" | Blocking — see below |
| 4 | Yes | backend acceptance (pure signal engine unit test preferred for the margin math, acceptance test for the R3 wiring) | fixture: design + cost lines giving margin 12% at current price | `simulate_price`/margin table math should also get a pure unit test on a fixed series (owned by the builder, not just QA's acceptance test) |
| 5 | Yes | pure unit test on fixed series, hand-computed expected values | fixture cost lines; explicitly "not the same SQL" | Good AC — forces an independent oracle. QA owns this as a held-back-style check even if builder writes a similar unit test, because it's the one place a shared-formula bug would hide |
| 6 | Yes | backend acceptance | small-shop fixture: 1 channel (Etsy), 10 weeks of orders | Seed doesn't have a "10 weeks, Etsy-only" shop; must build via fixtures, not seed |
| 7 | Yes | pure unit test on the trend function (< 13 points) | fixed series fixture | Cleanest AC in the doc — pure function, fixed input |
| 8 | Yes | backend acceptance with a fixture provider returning a scripted falling series against seed's own rising series (or two fixture series) | needs a provider test double that returns a fixed, opposite-direction series | The "own data rising" side needs real weekly history too (seed gap, see below) |
| 9 | Yes | pure unit test, one per rule R1–R5 | fixed low-band signal fixture per rule | Straightforward; builder should write these, QA holds back 1-2 boundary cases (band exactly at 0.40) |
| 10 | Yes | pure/backend unit test, frozen time | signal row with a controllable `asOf`/TTL | Needs a way to insert a signal row directly with a chosen `asOf` — ask backend-engineer(market) for a test-only insert helper, or QA builds it via `withSystem` insert in the acceptance test file itself (allowed since it's QA's own test file) |
| 11 | Yes | eval case (mock model draft with a bad number) + unit test on the validator function | ai-engineer's mock provider must support "return this exact bad draft" | Standard AI-guardrail pattern, matches wave 17's validator tests |
| 12 | Yes | unit test (niche/query against trademark reference data) + eval case for R4 idea generation | existing trademark check test data; confirm a sports-league/character term is already in the trademark fixture set — if not, that's a gap for whoever owns the trademark fixture (ai-engineer, from wave <17>) | |
| 13 | Yes | eval case, mock fixtures include seller names on purpose | mock provider fixtures must actually embed seller names (an explicit build requirement, not just a test requirement — call this out to integrations-engineer on T-18-2) | |
| 14 | Yes | eval case (prompt injection via tag text) | design fixture with the adversarial tag string | Same shape as wave 17's injection cases — reuse pattern |
| 15 | Yes | eval case + browser E2E screenshot check | Spanish locale session | |
| 16 | Yes | static/procedure-introspection test ("no write reachable") + acceptance test that DB rows outside the recommendation table are unchanged after a market answer | none beyond seed | Good, mechanically checkable AC |
| 17 | Yes | backend acceptance (state-machine level, reuse existing item-state fixtures) | seed has cancelled-after-`on_sheet` and reprint cases already (`builder.ts` finalState includes `cancelled`, and QC-fail/reprint flow exists) — confirm reprint flagging is queryable, not just visually distinct | Check with backend-engineer whether "reprint" is a first-class flag on the item row or only inferable; if only inferable, that's a gap to flag to them, not to fix ourselves |
| 18 | Yes | backend acceptance | **Seed/fixture gap**: no stockout-week history exists in the seed (no time-series stock-level table) — must be built as a fixture: a design + 26 weeks of synthetic weekly rows, 3 marked "blank out of stock" | See Seed/fixture gaps below |
| 19 | Yes | backend acceptance with the Amazon mock provider | fixture: personalized design + mixed personalized/non-personalized mock comparables | |
| 20 | Yes | backend acceptance (job-level), force the Google Trends mock's failure switch | mock provider must expose a "fail" toggle (build requirement on T-18-2, testable once built) | |
| 21 | Yes | backend acceptance, `assertCredits` forced to fail | existing credits-exhaustion fixture pattern from wave 8 (assistant credits) — reuse, don't re-invent | |
| 22 | Yes | backend acceptance | sample-workspace fixture (`companies.type` — confirm a "sample" type/flag exists; seed's `createCompany` fixture only has `type: "shop" | "vendor"`, no "sample") | **Gap**: `createCompany` in fixtures.ts has no sample-workspace type. Flag to backend-foundation if "sample workspace" isn't already a company attribute elsewhere |
| 23 | Yes | backend acceptance, RLS/tenancy suite pattern (reuse `rls-coverage.test.ts` style) | two companies via `createCompany` ×2 | Standard tenancy test; QA owns per `acceptance-tests-first` |
| 24 | Yes | backend acceptance (permission matrix) | `createUser` with roles designer/presser + `tenantContext` | Standard `FORBIDDEN`/`NOT_FOUND` pattern |
| 25 | Yes | backend acceptance | design + manual niche correction, then re-run mapper job | |
| 26 | Yes | backend acceptance, frozen time across 28 days (advance a stored `createdAt`/job "as of" param, don't sleep) | fixture: recommendation record + control-group designs of the same garment class | Needs the job to accept an "as of" time or the test to backdate rows directly — confirm with backend-engineer(market) which pattern the job uses so the test doesn't need real sleeps |
| 27 | Yes | backend acceptance, idempotency pattern (double-tap) | none beyond seed | Standard idempotent-side-effect pattern |
| 28 | Yes, but as a separate run | **scale run**, not the card | large-shop scale seed profile (5,000 designs, 1,000 orders/day, 3 years) — **does not exist**, see below | See "Scale" note below |

## Blocking

1. **AC3 is untestable against the seed as written.** The seed's Amazon channel connection has `status: "csv_only"`, never `"connected"` (`invai-backend/src/db/seed/builder.ts`, channel-connections insert). AC3 says "an Etsy listing only while Amazon is connected" — with the seed as-is, no design meets that precondition today. Proposed reword: either (a) accept that this AC is proven with a **fixture-built** connection (`createConnection(companyId, "amazon")` with a test-only `status: "connected"` override) rather than the seed, and say so explicitly in the AC ("Given a fixture shop with..."), or (b) ask backend-foundation to add one seed connection with `status: "connected"` for a non-Shopify channel so the golden-path/API-E2E layer can also exercise it. Recommend (a) for the acceptance test (fast, isolated) and file (b) as a seed-realism request only if wave 19 or a later wave needs API-E2E coverage of a connected non-Shopify channel too.

2. **AC18's "3 of the last 26 weeks out of stock" has no data shape to test against.** There is no weekly stock-history table/fixture anywhere in the backend (`stockLevels` is a point-in-time table, `invai-backend/src/db/seed/builder.ts` L1494 only sets current `available`). The AC is fine as a *behavior* spec (exclude those weeks from the trend fit) but the test needs the market module's own weekly-series fixture format, which T-18-3 hasn't been built yet to define. Reword or add a note: "the acceptance test builds the 26-week series directly against the market module's own history table, once T-18-3 defines its schema" — otherwise QA can't write this test before the schema exists, which conflicts with "acceptance tests first." Recommend: QA writes this AC's test in the second pass, right after T-18-3's schema migration lands, not before.

3. **AC28 (scale) needs a decision on where it runs.** 5,000 designs × 1,000 orders/day × 3 years of history is a `scale-test` profile, not a card-local fixture. Proposed: it does **not** run inside T-18-3's card. QA runs it once as a separate `scale-test` pass after the card is functionally green, using a new `large` scale seed profile (doesn't exist yet, see below), and reports it in `qa-report.md` rather than in the card's own acceptance-test file. The card's own acceptance test can instead assert the 15-min/500ms budgets are *configured* (e.g., a job time-box constant, a `LIMIT 20` on tool queries) without proving them at 5,000-design scale — that proof is QA's scale run.

## Seed/fixture gaps

| Gap | Needed for | Owner |
|---|---|---|
| No `"connected"`-status Amazon (or any non-Shopify) channel in the seed | AC3 | backend-foundation (seed), or QA fixture-only workaround for the acceptance test (proposed) |
| No weekly-series history longer than ~30 days anywhere in the seed (`ageDays = random.next() * 30` in `builder.ts`) — market signals need 26-156 weeks | AC1, AC6, AC7, AC8, AC10 (partly), AC18 | backend-foundation (seed) if AC1/AC2 must run on the real seed at API-E2E level; QA builds a synthetic weekly-series fixture at the market module's own schema level for AC6-AC18, once T-18-3's schema exists |
| No "sample workspace" attribute on `companies` (fixtures.ts `createCompany` only takes `type: "shop" | "vendor"`) | AC22 | backend-foundation (fixtures.ts), flagged as a card request, not edited by QA |
| No stockout-week (time-series stock) fixture/table | AC18 | backend-engineer (market), as part of T-18-3's schema; QA writes the test once that shape exists |
| No `large` scale seed profile (5,000 designs / 1,000 orders/day / 3 years) | AC28 | QA (scale seeds are QA-owned per CLAUDE.md); proposed location `invai-backend/src/db/seed/scale/` per backend-foundation's agreed convention (`scale-test` skill) |
| No test-only "insert a signal row with a chosen `asOf`/TTL" helper | AC10 | Ask backend-engineer(market) to expose one, or QA inserts directly via `withSystem` in its own acceptance-test file (already permitted since it's QA's file) |

## What QA will own vs. builder unit tests
- QA owns (`**/*.acceptance.test.ts`, held-back cases): AC1-3, 6, 8, 10, 16-28 — anything crossing tenancy, permissions, jobs, feedback, guardrail wiring, or requiring a fixture shop.
- Builder unit tests (pure functions, fixed series, owned by backend-engineer/ai-engineer, reviewed not authored by QA): AC5 (as an *additional* independent check — QA also writes its own oracle-based version per the AC's own instruction "test with fixed fixtures, not the same SQL"), AC7, AC9, AC12 (the pure trademark-threshold check), AC19 (comparable filter as a pure function).
- Eval cases (ai-engineer's evals/, QA reviews for coverage but doesn't author the harness): AC11, AC13, AC14, AC15, AC20's mock-failure eval variant if one exists.
