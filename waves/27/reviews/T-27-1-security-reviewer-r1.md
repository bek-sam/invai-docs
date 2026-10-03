# Review of T-27-1 (round 1)

- Reviewer: security-reviewer on opus
- Author: ai-engineer on opus
- Verdict: changes-required

## Evidence I re-ran (invai-backend 83ca734 + 927ad35 + cfd35ea; OPENAI_API_KEY= ANTHROPIC_API_KEY=; no real call)
| Command | Result |
|---|---|
| `pnpm vitest run --reporter=dot src/ai/images src/env.test.ts` | 3 files, 40 passed + 1 expected fail (my S-53 proof) |
| `src/ai/images/security.test.ts` without `.fails` | fails: `expected 0 to be greater than or equal to 22` (two timed-out paid calls recorded 0¢) |
| `NODE_ENV=development IMAGE_GEN_MOCK_DRIFT=1` import env | refuses: "test-only switch"; `imageGenMockDrift` also ANDed with `isTest` (`env.ts:370`) |
| grep `IMAGE_GEN_PROVIDER` backend src/scripts/evals, infra, `.env` | set nowhere outside tests; `.env` has no IMAGE_GEN line |

## Acceptance criteria (security view)
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `index.ts:28` flag + key + not sample; `secret()` trims blank; prod refusal `env.ts:264` (env.test); tests get no key (`env.ts:327`) |
| 2 | yes | only base + mask + fixed-vocabulary prompt, `n:1`, no `user`; key only from `env` (S-49 safe), `maxRetries:0`, one 5xx retry, timeouts not retried; logs carry status only |
| 4 | **no** | caps run before the call, but a billed-but-failed call escapes both the shop cap and the spend breaker (finding 1) |
| 3, 5, 6 | yes | as in the primary review; prompt never interpolates design text (`scene-prompt.ts` vocab only) |

## Blocking findings
1. `src/ai/images/caps.ts:124` and `:44` — S-53 (Medium). A timed-out OpenAI edit (120 s) may be billed, but `recordImageGen` records 0¢ and `imagesUsedToday` counts only `done` rows. While OpenAI is slow, every photo job (and each job retry) is a billed call that no cap sees: the shop cap never fills and the tenant/platform breaker stays at 0, so spend on the owner's key is unbounded. Fix: on timeout (or failure after send without a definite 4xx) record `estimateCents(size)` on the row and counters, and count rows with `cost_cents > 0` toward the shop cap; then flip `security.test.ts` to `it`. Due 2026-11-02, before OI-25.

## Checks
- [x] Only owned paths changed (`src/ai/**`, `evals/**`, schema enum, env lines)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened
- [x] Tenancy: count and insert inside `withTenant`/caller tx, no new table; money in cents (prices rounded up)
- [x] Decisions: ADR 0023; cap-not-reserved stated in the report

## Optional notes (not blocking)
- Shop cap and spend estimate are read, not reserved: parallel jobs pass both by their concurrency. T-27-3 must bound photo-job concurrency per company (or take an advisory lock around check + insert of a `running` row). I'll check it on T-27-3.
- T-27-1 cannot verify the base image is blank: T-27-3 must pass only imaging's `/photo/scene-base` output, never design pixels. I'll check that on T-27-3 too.
