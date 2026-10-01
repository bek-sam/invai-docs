# Review of T-P7-5 (round 1)

- Reviewer: security-reviewer on Fable 5.1
- Author: ai-engineer on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint`; `pnpm vitest run src/ai --reporter=dot` (invai-backend, 33c09fd) | tsc clean; biome 465 files, no fixes; 7 files, 88 passed |
| `git archive a64533e` → /tmp/review-T-P7-5, new test copied in, `./node_modules/.bin/vitest run src/ai/assistant-rounds.test.ts` | 4 failed, 2 passed (`expected 3 to be 1`, `expected 2 to be 1`, counter-at-request not a number, regeneration called 2 times); copy removed |
| `scan-test-weakening.sh invai-backend origin/main` | hits: `vi.spyOn(anthropicProvider, "assistant")` (a spy on the provider, not on the unit under test, `runAssistant`), two `provider.name === "mock"` branches in gateway.ts (AC5 requires them; same pattern as the existing `MOCK_MODEL` cost rule) |
| Read `breaker.ts:66-92, 180-200`, `credits.ts:57`, `gateway.ts` diff, `BetaToolRunner.mjs:160-235` | see checks below |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `afterRound` (gateway.ts) runs `assertSpendAvailable` + `assertCredits(tokensToCredits(usageSoFar)+1)` only on `tool_use`/`pause_turn`; one place for every provider; AC1 test: 1 request, provider closed |
| 2 | yes | records `tokensToCostCents(cumulative) - recordedCents`; `finishJob` records `max(0, cost - recorded)`; AC2 test: counter == `ai_jobs.costCents` == one price of the whole usage; no per-round rounding sum |
| 3 | yes | `stopMidRun`: `gen.return()` (runner `finally` aborts the stream, `BetaToolRunner.mjs:233`), `finishJob` with real usage (10 cents, 12 credits once), `jobFinished` skips `failJob`, existing `ORPCError AI_SPEND_CAP_REACHED` rethrown, one critical `ai_spend_cap_tenant` alert |
| 4 | yes | check-after with `+1` minimum, stated in the report; AC4 test `CREDITS_EXHAUSTED`, 1 request, 12 credits |
| 5 | yes | mock short-circuits before any Redis call; AC5 test asserts no `mget`, counter untouched |
| 6 | yes | 6 tests; 4 red on a64533e (re-run above), 2 guard unchanged behavior by design |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`src/ai/**`; contract and `modules/ai` untouched, `round` never reaches the service: both loops `continue` on it)
- [x] Nothing outside scope (regeneration cap check is one more model call of the same run; R3 "before every model round" covers it)
- [x] Tests exercise the behavior, none weakened
- [x] Tenancy: counters `ai:spend:tenant:<companyId>:<day>` and `assertCredits` inside `withTenant(meta.companyId)`, companyId from the session meta, never from the run input. Money in integer cents. No new text to the provider.
- [x] Decisions: round event provider-internal and regeneration fallback, in the report; no cross-cutting decision needed

Threat checks asked for: no double count (cumulative-minus-recorded on every path, including abort and capped regeneration where `usageDone = usageSoFar`); Redis error → `assertSpendAvailable` fails open with `ai_breaker_fail_open` alert (throttled per company per hour) and `recordSpend` logs and continues, unchanged policy from wave 17, now exercised per round instead of once; trip path charges real usage (test asserts cost, credits, counter and alert); no cross-tenant mixing (keys and tenant tx above); parallel runs of one tenant can each overshoot by one round (R3, accepted in the report).

## Optional notes (not blocking)
1. A round that ends in `refusal`/`max_tokens` throws in `checkStop` before its `round` event, so its cost is on neither the counters nor `ai_jobs` (job `failed`, cost 0) while earlier rounds are on the counters. The report lists it; a follow-up could yield the round event before `checkStop` so the last round is counted too.
2. `stopMidRun` sets `settled` before `finishJob`; if `finishJob` throws (DB down) the typed cap error is replaced by the DB error and `failJob` runs. Acceptable; a `try/finally` around the rethrow would keep the user-facing `spend_cap` code.
3. Web still shows the English message for `code:"spend_cap"` (R3): backlog row for web-engineer, as the report says.
