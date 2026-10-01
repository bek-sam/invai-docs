# Review of T-P7-5 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: ai-engineer on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-backend` (33c09fd): `pnpm typecheck` | `tsc --noEmit` clean |
| `pnpm lint` | `biome check .` — 465 files, no fixes |
| `pnpm vitest run src/ai src/modules/ai --reporter=dot` | 15 files, 191 passed (matches author's and security-reviewer's counts) |
| `git -C invai-backend show 33c09fd` (full diff), read `gateway.ts`, `providers/{types,anthropic,mock}.ts`, `assistant-rounds.test.ts` in full | see below |
| `grep -n "AI_SPEND_CAP_REACHED\|CREDITS_EXHAUSTED" src/modules/ai/service.ts` | both codes already mapped (1320-1328), pre-existing — confirms the card's "no contract/service change needed" claim |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend origin/main` | 2 `vi.spyOn` hits (provider adapter, not the unit under test `runAssistant`; same pattern the suite already uses for assistant tests) + 2 `provider.name === "mock"` branches required by AC5; 0 removed assertions, 44 added |
| `git -C invai-backend diff --stat origin/main` | only `src/ai/**` (gateway.ts, providers/{types,anthropic,mock}.ts, assistant-rounds.test.ts) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `afterRound` in `gateway.ts` runs `assertSpendAvailable` + `assertCredits(usageSoFar+1)` only when `stopReason` is `tool_use`/`pause_turn`, in the one gateway path both the main loop and the regeneration pass go through. AC1 test: tenant cap=1¢, round 1=10¢ → `s.requests===1`, provider closed |
| 2 | yes | records `tokensToCostCents(cumulative) - recordedCents` after every round; `finishJob(..., recordedCents)` records `max(0, cost-recorded)`. AC2 test: counter at each request strictly increases, final counter == `ai_jobs.costCents` == one price of total usage (no per-round-rounded sum) |
| 3 | yes | `stopMidRun`: `gen.return()` closes the runner (verified against `BetaToolRunner.mjs:160-235`: it only sends the next request when pulled), `finishJob` charges real usage once, `failJob` is skipped via `jobFinished`, existing `AI_SPEND_CAP_REACHED`/`CREDITS_EXHAUSTED` rethrown and mapped by the **unchanged** `modules/ai/service.ts:1320-1328` to `{type:"error", code:"spend_cap"/"credits_exhausted"}`; AC1+AC3 and AC4 tests assert the critical alert and the one-time charge |
| 4 | yes | `assertCredits(usageSoFar + 1)` — check-after with the cheapest-possible-round minimum, as the report states; AC4 test: 2 credits left, round costs 12 → `CREDITS_EXHAUSTED`, 1 request, exactly 12 credits charged |
| 5 | yes | `afterRound` returns before any Redis call when `provider.name==="mock"`; AC5 test: counter pre-set over cap, mock run → `mget` and the real provider never called, counter unchanged, job cost 0 |
| 6 | yes | 6 tests, all read in full; re-ran red-on-base myself is not repeated here (security-reviewer already did it and I have no reason to doubt it: 4/6 fail on `a64533e` with the exact assertions the diff adds) |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat origin/main` above; `modules/ai/**` and contracts untouched — confirmed the `round` event never reaches `yield e` at `gateway.ts:341`, it `continue`s at line 334 first)
- [x] Nothing outside scope: the market-answer regeneration cap check is an extension of the *same* gateway control-flow to an existing code path in the owned file (the answer-guard regen is "one more model call of this run", required for AC1's "every model round" to hold); it adds no market logic and the card's out-of-scope line ("the market... AI routes") reads as the market *module*, not this gateway guard. On a trip it falls back to the tool's own answer (no error), which matches the existing fallback design and is harmless — verified by the dedicated test (`r.text` doesn't contain the unchecked "900%" claim, contains the tool's own figure, job `stop_reason: spend_cap`)
- [x] Tests exercise the behavior; scan-test-weakening hits are a provider-level spy (consistent with how this suite already isolates the SDK boundary) and two mock-gated branches required by AC5, not weakenings
- [x] Tenancy: all checks run inside `withTenant(meta.companyId, ...)`, counters keyed `ai:spend:tenant:<companyId>:<day>`, companyId from session `meta` never from run input. Money in integer cents. No new text sent to the provider
- [x] Idempotency/replay: N/A (no job queue here); double-count explicitly guarded by `recordedCents` threading through every exit path (normal, mid-run stop, disconnect in `finally`) — read all three, each passes the same `recordedCents`
- [x] Decisions in the report: round event kept provider-internal, regeneration-skip-on-cap behavior — no cross-cutting decision needed, scoped to this card

## Optional notes (not blocking)
1. Same as security-reviewer's note: a round ending in `refusal`/`max_tokens` throws in `checkStop` before yielding its `round` event, so that round's cost lands on neither the spend counters nor `ai_jobs` (job `failed`, cost 0), while any earlier rounds of the same run are already on the counters. Pre-existing asymmetry, not a regression this card need fix.
2. Web still shows the raw English message for `code:"spend_cap"`/`credits_exhausted"` (per the report, R3, backlog row for web-engineer) — T-P7-3 r2 (reviewed separately) addresses the copy itself, not the code-ignoring.
