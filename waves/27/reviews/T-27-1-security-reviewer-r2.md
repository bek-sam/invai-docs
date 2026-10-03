# Review of T-27-1 (round 2, S-53 only)

- Reviewer: security-reviewer on opus
- Author: ai-engineer on opus
- Verdict: approve

## Evidence I re-ran (invai-backend f65dd4e; OPENAI_API_KEY= ANTHROPIC_API_KEY=; no real call)
| Command / check | Result |
|---|---|
| `pnpm vitest run --reporter=dot src/ai/images` | 2 files, 22 passed (vitest close-timeout warning only) |
| `security.test.ts` marker | flipped: `it` (was `it.fails`); passes: two timed-out paid calls fill tenant counter >= 2x estimate and the 3rd attempt gets `IMAGE_DAILY_CAP_REACHED` |
| `caps.ts` `failedCallCents` | timeout, 5xx, empty/non-PNG body, unknown error -> `estimateCents(size)`; refusal, 4xx, 429, unsent, mock -> 0 |
| `caps.ts` `imagesUsedToday` | counts `done` OR `cost_cents > 0`: slow-OpenAI loop now fills the shop cap |
| `recordSpend(companyId, costCents)` after commit | same `tenantSpendKey` that `assertSpendAvailable` reads (`breaker.ts:78`): slow loop now trips the tenant/platform breaker |
| `images.test.ts:607,641` | estimate recorded (counter 33, used 3) and `mayBeBilled` true only for hang/500/bad body |

## Optional notes (not blocking)
- A 5xx retried once then succeeding records one row: the first attempt may be billed uncounted (bounded, at most 2x per row).
- `sizePx` defaults to 1024 on failure: T-27-3 must pass the real size to `recordImageGen`. I'll check on T-27-3, with concurrency and blank-base notes from r1.

S-53 marked Fixed in `security/v1-review.md`.
