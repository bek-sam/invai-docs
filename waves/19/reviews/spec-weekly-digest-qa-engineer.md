# QA review: spec/weekly-digest.md (wave 19)

Reviewer: qa-engineer. Verdict: **changes-required** (one cross-cutting ambiguity about what "the seed" means for frozen-time ACs, plus fixture/schema gaps below).

## AC table

| AC# | Testable? | Level | Fixture/seed needed (gap if missing today) | Note |
|---|---|---|---|---|
| 1 | Ambiguous as written | backend acceptance, frozen time, parity test vs finance service | fixture company shaped like Desert Bloom Tees with explicit `placedAt` dates inside the frozen week — **not** the literal random seed (see Blocking #1) | "seed" and "2026-09-28" can't both hold literally; reword |
| 2 | Yes | backend acceptance (idempotent-job pattern: run twice) | fixture shop + orders for one week | Standard double-run test |
| 3 | Yes | backend acceptance, DST-boundary frozen time | fixture company with `timezone: "America/New_York"` (schema supports `companies.timezone`, confirmed) | Good AC, needs a DST-crossing date picked deliberately (e.g. 2026-11-01 US fall-back) |
| 4 | Yes | backend acceptance, frozen time with two "now" points (07:00 then 21:30) | fixture; needs the sweep job runnable with an injected "now" rather than real time | Confirm with backend-engineer(digest) that the sweep accepts a test clock, not `Date.now()` directly |
| 5 | Yes | backend acceptance, two frozen "now" points (07:05, 09:05) | fixture company with `hour: 9` setting | |
| 6 | Yes | backend acceptance, "matches a hand SQL count" | fixture orders: overdue + Etsy on-time < 95% | Not the literal seed's random data (see Blocking #1) — the AC's own precondition ("Etsy on-time rate below 95%") is a specific, engineered state, best built as a fixture so the count is exact and stable, not "whatever the seeded random data happens to produce this run" |
| 7 | Yes | backend acceptance | fixture: one channel connection with a disconnect event inside the week window | **Fixture gap**: `createConnection` in `fixtures.ts` sets a connection up already-`csv_only`; there is no helper to mark a connection disconnected *at a specific time* — needed by both this AC and D1. Flag to backend-foundation |
| 8 | Yes | backend acceptance | fixture: 1 channel, 0 ad spend, exactly 12 orders | Good minimum-volume-guard AC, cleanly fixture-buildable |
| 9 | Yes | backend acceptance, two consecutive frozen weeks | fixture: zero orders both weeks | Needs the acceptance test to run the build job for week N then week N+1 with time advanced, not sleep — frozen-time advance only |
| 10 | Yes | backend acceptance, reuse the item-state fixtures | seed/fixtures already support cancelled-after-`on_sheet` and a reprint state; confirm "reprint" is queryable as its own flag (same open question noted in the market review, AC17) | Cross-check with backend-engineer(market) since both specs need the same reprint flag |
| 11 | Yes | backend acceptance | fixture: blank below reorder point + a top-5 design that needs it | `stockLevels`/`reorderPoint` exist in schema (seed sets `reorderPoint: 8`); buildable without new schema |
| 12 | Yes | backend acceptance, two/three consecutive weeks with a stored vote | fixture: prior week's digest + a "not relevant" vote record | Needs the digest module's vote-storage shape, which doesn't exist until T-19-3 lands — QA writes this test right after that schema, not before |
| 13 | Yes | backend acceptance (string/format assertions) + browser E2E screenshot at 390px | Spanish-locale recipient fixture | Standard i18n check, matches `write-plain-language-copy` conventions |
| 14 | Yes, once wave 18 lands | backend acceptance | needs wave 18's market module read service + a stored R1 (medium/high) and R4 (low) recommendation for the same fixture shop | **Cross-wave dependency**: cannot be written or run until T-18-3's read-only service exists; QA should hold this test (and 15-17 below) until wave 18 integrates, per the spec's own "T-19-3 depends on wave 18's market read service" |
| 15 | Yes, once wave 18 lands | backend acceptance | same as AC14, plus an R1 tied to a cross-listing gap and one R2 item | |
| 16 | Yes | backend acceptance | fixture: market service mocked to throw, or to return stale (> 2×TTL) signals | This one is buildable **without** waiting for wave 18's real implementation — QA can write it against a stub/interface as long as the interface (read-only service signature) is fixed by T-19-1's contract. Confirm the interface is frozen before wave 18 code lands so this test doesn't churn |
| 17 | Yes, once wave 18 lands | backend acceptance | same dependency as AC14 | |
| 18 | Yes | backend acceptance, mode `shadow` | fixture shop, digest build | |
| 19 | Yes | unit tests per validator rule (digit outside placeholder, reorder, cross-insight reference) | fixture ranked-facts input + a scripted bad model output (via ai-engineer's mock provider) | Same shape as market-signals AC11; builder unit-tests, QA reviews coverage |
| 20 | Yes | eval case | design fixture with the adversarial name | |
| 21 | Yes | backend acceptance, `assertCredits`-style guard forced low / cost estimate forced high | reuse the wave 8 low-credits fixture pattern | |
| 22 | Yes | backend acceptance (breaker logic), unit test on the 24h window calc | fixture: ≥ 10% of a batch of stored summaries marked rejected within 24h | Needs a way to seed "N summaries rejected in the last 24h" without waiting real time — a test-only insert, not a real 24h wait |
| 23 | Yes | backend acceptance + one API call | fixture: office user, opt-in toggle, two digests one week apart | |
| 24 | Yes | backend acceptance, idempotent-side-effect pattern (double POST) + one GET | signed-token helper (T-19-4's `crypto.ts` addition) — doesn't exist yet; QA test written once that helper lands | |
| 25 | Yes | backend acceptance (tenancy/token-binding) | two fixture companies + a tampered token (shop A token, person from shop B) | Security-relevant; also flag to security-reviewer as co-reviewer material, not just QA |
| 26 | Yes | backend acceptance | fixture: sample workspace, unverified email, deactivated member, PIN-only address | **Schema gap**: `companies.type` is only `"shop" | "vendor"` today (`invai-backend/src/db/schema/tenancy.ts` L50) — there is no "sample workspace" concept anywhere in schema. Both this AC and market-signals AC22 need it. See Blocking #2 |
| 27 | Yes | backend acceptance (permission matrix, reuse pattern) | `createUser` roles presser/designer/office/owner | |
| 28 | Yes | backend acceptance (tenancy suite, reuse rls-coverage pattern) | two companies | |
| 29 | Yes, but as a separate run | **scale run**, not the card | 1,000-shop scale seed profile — doesn't exist yet, see below | Same reasoning as market-signals AC28: propose it run as a `scale-test` pass, not inside T-19-3's own acceptance suite |
| 30 | Yes | backend acceptance, rate-limit pattern (3 requests in a minute, frozen/advanced clock) | none beyond seed | Standard rate-limit test shape, likely reuses an existing limiter helper — check `src/lib` for one before writing a new one |

## Blocking

1. **What "the seed" means for frozen-time ACs is ambiguous and needs a stated convention before tests are written.** AC1, AC3-6, and others say "Given the seed at [absolute date/time]" or "the seed week", but the actual demo seed (`invai-backend/src/db/seed/index.ts`/`builder.ts`) generates order dates **relative to real `Date.now()` at seed-run time** (`ageDays = random.next() * 30`, `placedAt = now - ageDays*DAY`), with a fixed RNG seed (`rng(20260924)`) that makes the random *shape* deterministic but not the *calendar dates*. Freezing test time to a fixed date like 2026-09-28 does not make the seed's orders land in the expected ISO week unless the seed itself was generated under that same frozen clock — which the normal `pnpm db:seed` flow doesn't support.
   Proposed reword: change "Given the seed" to "Given a fixture shop built to Desert Bloom Tees' shape (channels, blanks, states)" for every AC that also freezes an absolute date, and reserve literal "the seed" (via `run-golden-path`) only for ACs that don't pin a specific calendar date. Concretely: AC1, 3, 4, 5, 6, 9, 12, 18 (AI summary) should say "fixture shop", not "the seed"; AC2, 7, 8, 10, 11, 13 can stay generic enough to run either way. This mirrors the same issue I'm flagging in the market-signals review (AC3) — recommend the PM apply one consistent rule across both specs rather than deciding per-AC.

2. **"Sample workspace" has no schema representation.** `companies.type` is `["shop", "vendor"]` only (`invai-backend/src/db/schema/tenancy.ts` L50-63). AC26 here and market-signals AC22 both require a sample-workspace concept, and the digest pipeline description ("Sample workspaces and deleted shops are skipped") assumes one exists. This needs an architect/backend-foundation decision (likely a `companies.type` enum addition, or a boolean flag) before either wave's cards can implement or test the skip rule. Recommend: raise to the tech lead now, since it blocks a testable precondition in two waves, not just wording.

## Seed/fixture gaps

| Gap | Needed for | Owner |
|---|---|---|
| No way to build a fixture shop with orders on explicit dates inside a chosen ISO week (current `createOrder` fixture hard-codes `placedAt: new Date()`, `shipBy: now+2d`) | AC1, 3-6, 9, 12 | backend-foundation (`fixtures.ts`): extend `createOrder` to accept `placedAt`/`shipBy` overrides, or add a digest-specific helper in the acceptance-test file itself (QA can do the latter without a grant, since it's QA's own test file, but a shared `placedAt` override on `createOrder` would save every future card the same problem — recommend filing it as a small card) |
| No helper to mark a channel connection "disconnected at time T" | AC7, D1 detector tests | backend-foundation (`fixtures.ts`) — `createConnection` only creates `status: "csv_only"` |
| No "sample workspace" flag on `companies` | AC26, market AC22 | backend-foundation / architect (schema decision) — blocking, see above |
| No signed-token test helper yet (T-19-4 not built) | AC24, AC25 | backend-foundation, once T-19-4 lands; QA test written after |
| No 1,000-shop scale seed profile | AC29 | QA (scale seeds are QA-owned); propose `invai-backend/src/db/seed/scale/` per the `scale-test` skill's proposed convention, shared with market-signals' `large` profile so one scale seed serves both waves' scale ACs where possible |
| No "insert N rejected AI summaries in the last 24h" test-only helper | AC22 | backend-engineer(digest), as part of T-19-2/T-19-3's own test setup; QA reuses it rather than re-deriving |

## What QA will own vs. builder unit tests
- QA owns (acceptance tests, held-back cases): AC1-9, 12, 16 (interface-only stub), 18, 21, 23-28, 30 — anything crossing jobs, scheduling, tenancy, permissions, delivery/consent, or a fixture shop.
- Held back until wave 18 integrates: AC14, 15, 17 (real market-service dependency) — write against the frozen T-19-1 contract interface first so the test exists, then point it at the real service once wave 18 lands.
- Builder unit tests (pure functions, owned by backend-engineer/ai-engineer): AC19 (validator rules), AC10's cancelled/reprint classification if it's a pure function, D1-D8 detector threshold math on fixed inputs.
- Eval cases (ai-engineer's evals/): AC20, plus AC19's injection-shaped variants.
- Scale run (separate from the card, QA-owned): AC29.
