# Review of T-19-2 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: ai-engineer on Opus 5.5
- Verdict: approve

## Evidence I re-ran
Worktree `invai-backend-rev-t19-2` at `ed68608` (symlinked `node_modules`, own `.env` pointing `TEST_DATABASE_URL`/`TEST_MIGRATION_DATABASE_URL` at `invai_t19_rev_2`, `REDIS_URL` at db 10); a second worktree `invai-backend-rev-t19-2-base` at `0bc68e2` (the commit immediately before T-19-2's day-1 commit) for before/after comparison, DB `invai_t19_rev_2_base`.

| Command | Result |
|---|---|
| `node_modules/.bin/tsc --noEmit` (at `ed68608`) | 1 error only: `src/modules/tenancy/router.ts(11,42)` — `notifications` missing on the tenancy router, the pending T-19-4 stub named in the brief as acceptable. Confirmed no `src/api/router.ts` error (T-19-3's `cadc338`, already landed on top of T-19-2, resolved it). |
| `node_modules/.bin/biome check src src` | `Checked 349 files … No fixes applied.` |
| `vitest run src/ai src/modules/ai src/modules/market/market-prod-mode.acceptance.test.ts` (at `ed68608`) | `Test Files 12 passed (12); Tests 169 passed (169)` — matches report |
| `vitest run src/ai src/modules/ai src/modules/market/market-prod-mode.acceptance.test.ts` (at `0bc68e2`, pre-extraction) | `Test Files 9 passed (9); Tests 134 passed (134)` — matches report's "before" count |
| `NODE_ENV=test tsx evals/run.ts digest_narrative` | `22/22 plumbing`, by-tag breakdown matches report exactly (en 15, spanish 7, injection 4, near_identical_channels 2, digits_temptation 2, market 2, market_fence 1, many_insights 2, oversize 1, pii 1, markup 1, win_only 1, promise_temptation 1, glance 2, steady 2, data_health 1, basic 2) |
| `NODE_ENV=test tsx evals/run.ts assistant` (at `ed68608` and at `0bc68e2`) | `30/30 plumbing, 17/17 quality` both before and after — extraction changes no assistant behavior |
| `scan-test-weakening.sh invai-backend 0bc68e2` | Hits are `vi.spyOn(mockProvider, "structured")` in `src/ai/digest-narrative.test.ts` (legitimate: mocking the provider boundary, not the unit under test) and `it.fails`/`it.todo`/`vi.mock("../../env")` — all in `src/modules/digest/digest.acceptance.test.ts`, outside T-19-2's owned paths (QA/T-19-3 acceptance tests already in the shared tree from other commits). No weakening in owned files. |
| Mutation test: commented out the `digits` rule's `failed.add("digits")` line in `validators/digest.ts`, reran `vitest run src/ai/validators/digest.test.ts` | 1 test failed as expected (`digits outside placeholders`, `expected [] to deeply equal ['digits']`); restored the file, reran clean: `15/15 passed`. Confirms the new tests are real checks, not rubber-stamps. |
| `git -C invai-backend diff --stat 759f2d4^ 759f2d4` and `ed68608^ ed68608` | Every changed file is inside the card's owned paths: `src/ai/**`, `src/modules/ai/analyst-queries.ts`(+test), `src/modules/ai/assistant-tools.ts` (switch only, confirmed `assistant-tools.test.ts` untouched), `evals/**`, `src/db/schema/ai.ts` (+3 lines, enum values only, no migration file added). |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Extraction, no behavior change | yes | 134/134 → 134/134 backend tests reproduced myself on both commits; 30/30, 17/17 assistant eval reproduced on both commits, identical. `analyst-queries.test.ts` asserts `toEqual` between the tool's data and the extracted function's data for all four tools, plus a tenancy test showing company B sees 0 of company A's rows even when B's context is used inside A's transaction. |
| 2 Shadow/off/on | yes | `digestSummaryMode()` defaults to `shadow`; unknown values fall to `shadow`; `off` makes no call (verified in code path and test); `on` sets `showable: true` but nothing in this diff sets `DIGEST_SUMMARY_MODE=on` by default. |
| 3 Validator | yes | Read `validators/digest.ts` line by line: all 17 rules are hard fails, each has its own unit test in `validators/digest.test.ts` (15 tests), including the specific asks: digits outside placeholders (`/\p{N}/u` on the model's own words with placeholders stripped), number words en/es (with "un/una" excluded as the Spanish article, "once" Spanish-only), same insights same order (`insight_order`), placeholders belong to their own insight (`placeholder_foreign`). Mutation-tested the digits rule myself to confirm the test is load-bearing. |
| 4 Injection (AC20) | yes | `digest-narrative.test.ts` "AC20 injection..." spies on the mock provider's actual returned output and asserts the model's own words never contain `/doubl/i`, and the rendered text contains the injected string exactly once (as the substituted placeholder value). A second test feeds a hand-crafted malicious model output (reordered insight, foreign placeholder, digits, number words) and confirms it is rejected with those rule ids and the provider was called exactly once (no retry). Eval cases dn-006/007/008/020 cover en, es, a literal `</data>` breakout attempt and a `<script>` tag; `dataBlock()` JSON-encodes and escapes `<` so this can't structurally break the prompt. |
| 5 Cost (AC21) | yes | Read `generateDigestNarrative`: estimates cost before the call (`estimateNarrativeCents`), checks `weekSpentCents + estimate > cap` and `balance.remaining < 25` before calling, both giving `skipped_budget` with no call (test asserts `spy.not.toHaveBeenCalled()`). A rebuild of the same digest reuses the stored `ai_jobs` row (`priorRun`) instead of a second call; test asserts one row in `aiCreditLedger` keyed on `refType: "digest"`. |
| 6 Breaker (AC22) | yes | `checkDigestSummaryBreaker` counts `done`+`failed` `digest_narrative` jobs in the last 24h across tenants (`withSystem`, counts only, no row content read). Tests: 10% exactly does not trip; >10% trips, flips mode to shadow, raises exactly one critical `ai_summary_breaker` alert (`redis.set(..., "NX")` guards a second alert on a re-check); outcomes older than 24h don't count; a real model-call failure inside `generateDigestNarrative` feeds the breaker. |
| 7 Evals | yes (mock) | 22 cases (card asked ≥15), covering every required category; mock 22/22 plumbing reproduced myself; baseline.json entry present and matches. Real-model run correctly deferred to OI-8, as the card allows. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat` on both commits `759f2d4` and `ed68608`, checked against the card's owned globs; `src/db/schema/ai.ts` change is enum-text values only, no migration, as A5 requires)
- [x] Nothing outside scope (no digest module, template, ranking or delivery code touched; `assistant-tools.test.ts` untouched)
- [x] Tests exercise the behavior, and none were weakened (`scan-test-weakening.sh` hits are all outside T-19-2's owned files or are legitimate provider-boundary spies; mutation test on the digits rule confirms the tests are real)
- [x] Tenancy (`withTenant` on every analyst-query and narrative call path; the one `withSystem` use — `digestSummaryRejectRate` — is a documented cross-tenant count-only breaker read, consistent with the `withSystem` exception list); idempotency (one charge per digest, ledger ref = digest id, rebuild reuses the stored run — sequential-rebuild race with concurrent builds is a named, reasonable gap deferred to T-19-3's per-week build lock); money in cents (`costCents`, `DIGEST_MAX_CENTS_PER_WEEK`); en/es text (validator and mock both cover both languages, with the Spanish-specific "once"/"un/una" edge cases tested)
- [x] Decisions recorded where needed (report documents: async `digestSummaryMode`, env-var-direct switches ahead of T-19-4, headline-vs-item placeholder scope, model-error handling, breaker withSystem justification, rebuild dedup) — none of these needed a formal `decisions/` entry; they are implementation choices inside the card, correctly logged in the report per `record-decision`'s "routine choices inside one card" carve-out.

## Optional notes (not blocking)
- `generateDigestNarrative`'s reuse-on-rebuild path is not safe against two truly concurrent builds of the same digest (both could pass `priorRun == null` and call twice). The author names this explicitly and defers the fix to T-19-3's per-week build idempotency lock — reasonable, but worth a one-line check in the T-19-3 review that the lock actually covers this window before wave 19 closes.
- The headline is allowed to use any fact id while items are restricted to their own insight's `factIds` (undocumented in the card text, but a sensible reading of AC19 and called out plainly in the report). No objection, just flagging it as a place a future reader might expect symmetry.
