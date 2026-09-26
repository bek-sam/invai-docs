# Review of T-8-3 (round 1)

- Reviewer: data-analyst (co-reviewer) on Claude Sonnet 5
- Author: backend-engineer on Claude Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| Fetched `platform.claude.com/docs/en/about-claude/pricing` and cross-checked every cell of `MODEL_PRICES` (models.ts) | Opus 5 $5.00/$25.00 in/out, 5m write $6.25 (1.25x), 1h write $10 (2x), cache read $0.50 (0.1x); Sonnet 5 $2.00/$10.00, $2.50/$4/$0.20; Haiku 4.5 $1.00/$5.00, $1.25/$2/$0.10 — all cells match to the cent |
| Same page, "Batch processing" table | Opus 5 batch $2.50/$12.50, Sonnet 5 $1/$5, Haiku 4.5 $0.50/$2.50 — matches `batchInputPerMTok`/`batchOutputPerMTok` for all three models |
| Same page, "How do discounts stack?" / "These multipliers stack with other pricing modifiers, including the Batch API discount" | Confirms the code's compounding (`cacheReadPerMTok * batchDiscount`, `cacheWriteRate * batchDiscount` where the write rate is itself derived from the base input rate) is the documented behavior, not an invented interaction |
| Hand-recomputed all 7 pinned test values from the price table | Opus 3050, Sonnet 1220, Haiku 610 (input+output+cache-read on 1M tokens each); 5m cache write 625/250/125; 1h cache write 1000; batch 1525 (Opus)/610 (Sonnet) — all reproduce the test file's expectations exactly |
| `node_modules/.bin/vitest run src/ai` (in the `874bb7f` worktree, node_modules symlinked from `invai-backend`) | 19/19 pass |
| Re-ran the same pinned-cents tests against `e958638` (pre-change) via a scratch checkout | 7 fail (Sonnet/Haiku price table and batch/fallback paths don't exist yet) — the tests are real evidence, not tautologies |
| Spot-checked `tokensToCredits` (unchanged) | still a simple 1-per-1,000-billable-tokens ratio, unrelated to `MODEL_PRICES` — out of scope for this card, no regression |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Prices match current official Anthropic pricing, including cache read/write multipliers and the batch discount | Yes | Verified line-by-line against the live pricing doc (not the skill's cached table alone, which is dated 2026-06-24 but happened not to have drifted for these three models). Cache write 1.25x(5m)/2x(1h) and cache read 0.1x are the documented base multipliers for Opus 5/Sonnet 5/Haiku 4.5 (none of the three uses the reduced 0.025x/0.05x multiplier reserved for Fable 5.1/Mythos 5.1/Opus 5.5). Batch = 50% off input/output, and it also discounts the cache-derived rates when combined, per the docs' explicit stacking note — the code does this correctly (verified by hand recompute of the batch test case: 1M×250 + 1M×1250 + 1M×50×0.5 = 1,525,000 → 1525 cents, matching the test). |
| 2. Rounding in cents | Yes | Single integer `Math.round` on a cents-denominated computation (rates stored as cents/MTok, not dollars), removing a dollars→cents round-trip that existed pre-change. Confirmed algebraically equivalent to the old formula for the unchanged `gateway.ts` call site, and confirmed by direct spot-checks on non-round token counts. |
| 3. Mock default is schema-valid and logs a warning | Yes | `defaultForSchema` handles every zod node type actually used in the codebase's prompt schemas (object/array/record/string/number/boolean/literal/enum/nullable/optional/default/null), verified against the installed `zod@4.6.5` `_def.type` values directly (not assumed from memory). The result still runs through `schema.parse`, so an unhandled shape fails loud, not silent. `logger("ai:mock").warn(...)` fires before the fallback and honors `LOG_LEVEL` (confirmed by reading `src/lib/log.ts`). |
| 4. No hard-coded prices remain | Yes | Repo-wide grep for `tokensToCostCents`/`MODEL_PRICES` usage found exactly one call site (`gateway.ts`, unchanged, no model arg) and no other numeric price literals; `credits.ts` was correctly left untouched since its ratio is credits-per-token, not a dollar price. |

## Blocking findings
none

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened
- [x] Money in cents (no dollars→cents round-trip in the new code, unlike the old formula); tenancy/idempotency n/a; en/es n/a
- [x] Decisions recorded where needed: n/a

## Optional notes (not blocking)
- The in-file comment's cited "skill cache date 2026-06-24" is a good practice worth keeping, but it should be paired with the live-doc cross-check date (2026-09-26, which the author already added) on every future repricing, since the skill's cached table can lag a real Anthropic price change (it didn't here, but it's not guaranteed next time).
- Consider a cheap CI/wave-gate reminder to re-diff `MODEL_PRICES` against the pricing page whenever `DEFAULT_MODEL`/`SONNET_MODEL`/`HAIKU_MODEL` change, so a future model swap doesn't silently carry stale rates.
