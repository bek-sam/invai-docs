# Review of T-27-1 (round 1)

- Reviewer: reviewer on fable
- Author: ai-engineer on opus
- Verdict: approve

## Evidence I re-ran (invai-backend 83ca734 + 927ad35 + cfd35ea, OPENAI_API_KEY= ANTHROPIC_API_KEY= blanked)
| Command | Result |
|---|---|
| `pnpm typecheck` | exit 0 |
| `pnpm lint` | 494 files, clean |
| `pnpm vitest run --reporter=dot src/ai src/env.test.ts` | 11 files, 163 passed |
| `pnpm evals scene-prompts` | mode mock, 14/14 plumbing, 14/14 quality, 0¢ |
| `scan-test-weakening.sh invai-backend 3f4deae` | no deleted/skipped tests; removed=0 added=106 assertions; prod "test-only branch" hits are the mock/openai provider switches, by design |
| `git show --stat` of the 3 commits | only `src/ai/**`, `evals/**`, `src/db/schema/ai.ts`, `src/env.ts`, `src/env.test.ts`, `.env.example` |
| grep `IMAGE_GEN_PROVIDER` in backend, infra, `.env` | set to `openai` only in-process in `images.test.ts` (fake key) and `env.test.ts` boot probes; `.env` and `.env.example` leave it mock |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `index.ts:28` mock unless flag + key + `!isSampleWorkspace`; `secret()` trims blank → undefined (`env.ts:17`); prod refusal `env.ts:264`; env.test "blank key counts as unset" passes |
| 2 | yes | `openai.ts`: `images.edit`, base + mask, `n:1`, fixed size/quality, no `user`, no `input_fidelity`; tests stub `fetch` and inspect the multipart form (mask bytes, base bytes, `n`, prompt rules). Price table `models.ts` with source URL + 2026-10-03. Retry only once on 5xx; 429 retryable, timeout/other 4xx not; moderation 400 → refusal |
| 3 | yes | `mock.ts`: sha256(base, mask, prompt) seeds mulberry32; protected mask pixels keep the base; whole-frame falloff + ±2 noise; drift only via `env.imageGenMockDrift` (test env only, `env.ts:270`); `costCents 0`; `containsPerson` from the prompt (scene kind) for both providers |
| 4 | yes | `caps.ts`: shop cap (done `image_scene` rows, UTC day, mock counts) → `assertCredits` with held → `assertSpendAvailable` with estimate, real provider only; `recordImageGen` writes the row then `recordSpend` (0 for mock → early return at `breaker.ts:185`). 4 DB tests pass |
| 5 | yes | `scene-prompt.ts` fixed vocabulary only, analysis text only matched; rules block last; eval 14/14 incl. brands, evasions, celebrity, children, injection, PII |
| 6 | yes | grep above; runbook rows say owner-only (OI-25) |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat`)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened
- [x] Tenancy (`imagesUsedToday` filters `company_id` inside the caller's tenant tx; `recordImageGen` uses `withTenant`; no new table), money in integer cents, no PII in prompt/log/row
- [x] Decisions: model choice and cap-not-reserved recorded in the report; ADR 0023 covers the feature

## Optional notes (not blocking)
- `caps.ts:124` a failed call records `costCents 0`, yet a timeout may already be billed (the author says so). Spend counters can undercount by one image per timed-out call; bounded because timeouts are non-retryable. Security co-reviewer may want a conservative charge on timeout.
- Wave "Agreed interfaces" says the mock "never touches masked-off pixels"; the card's AC3 asks for a whole-frame perturbation and the code follows the card (protected pixels keep the base colour, then ±2 noise). T-27-2/T-27-3 lock checks must tolerate that noise.
- Shop daily cap is counted, not reserved (documented): parallel jobs can pass it by their concurrency.
