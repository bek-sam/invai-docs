# Review of T-8-3 (round 1)

- Reviewer: reviewer on Claude Sonnet 5
- Author: backend-engineer on Claude Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend worktree add ../invai-backend-review-t83 874bb7f` | clean checkout at the card's SHA |
| `git -C invai-backend-review-t83 diff e958638 874bb7f --stat` | 3 files: `src/ai/models.ts`, `src/ai/providers/mock.ts`, `src/ai/ai.test.ts` — all owned paths, no scope creep |
| `node_modules/.bin/biome check src/ai/models.ts src/ai/providers/mock.ts src/ai/ai.test.ts src/ai/credits.ts` | "Checked 4 files in 5ms. No fixes applied." |
| `node_modules/.bin/tsc --noEmit -p .` (whole repo, worktree) | 0 errors |
| `node_modules/.bin/vitest run src/ai` | 1 file, 19/19 passed |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend-review-t83 e958638` | 1 hit: a `.toBeTruthy()` existence check in a new test (not a loosened assertion — see below); exit 1 |
| Ran the new `ai.test.ts` against pre-change code (`git archive e958638` into `/tmp/review-T-8-3`, copied the new test file in) | 7/19 tests fail as expected (Sonnet/Haiku pricing missing, no fallback, mock still throws) — proves the tests are load-bearing |
| Fetched `platform.claude.com/docs/en/about-claude/pricing` (official pricing page) | confirms every price and multiplier in `MODEL_PRICES` — see criterion 1 |
| `grep -rn "tokensToCostCents\|MODEL_PRICES" src/ai/gateway.ts src/ai/credits.ts` | only `gateway.ts` calls `tokensToCostCents(result.usage)` (no model arg); no other price literals found repo-wide |
| Node/tsx spot checks of `tokensToCostCents` on non-round token counts (333,333 / 666,667 / 1) | 33 / 67 / 0 cents — standard `Math.round`, algebraically identical to the pre-change formula for the no-arg call shape |
| `node -e` against installed `zod@4.6.5` to inspect `_def.type` for object/array/string/nullable/enum | matches every case branch in `defaultForSchema` |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Cost table reads a per-model price table (Opus/Sonnet/Haiku, cache read/write, batch), no hard-coded Opus 5 prices | Yes | `MODEL_PRICES` (models.ts) has all three models with input/output/cache-write-5m/cache-write-1h/cache-read/batch-in/batch-out in cents; `tokensToCostCents` reads only from it. Verified against the live pricing page: Opus 5 $5/$25, 5m write $6.25, 1h write $10, cache read $0.50; Sonnet 5 $2/$10, $2.50/$4/$0.20; Haiku 4.5 $1/$5, $1.25/$2/$0.10 — all exact matches. Batch table ($2.50/$12.50 Opus, $1/$5 Sonnet, $0.50/$2.50 Haiku) also exact. The docs' "discounts can be combined" note (batch × cache stacking) matches the code's `cacheReadPerMTok * batchDiscount` / `cacheWriteRate * batchDiscount` composition. `grep` found no stray hard-coded price literals outside the table. |
| 2. Rounding in cents | Yes | Single `Math.round` at the end, cents-native rates avoid intermediate dollar conversion; algebraically identical to the old formula for the existing call shape (verified by hand and by the unchanged gateway.ts test still passing); fractional-cent spot checks round as expected (33/67/0). |
| 3. Mock returns schema-valid default + warns instead of throwing | Yes | `defaultForSchema` walker verified against installed zod's actual `_def.type` strings; new test exercises an unknown prompt id, gets `{ok:false, tags:[], note:null, rank:"low"}`, and `logger("ai:mock").warn(...)` is called (confirmed real `LOG_LEVEL`-respecting logger, not console.warn). Existing fixtures (`listing_copy`, `trademark_judge`) untouched. |
| 4. Credits: charging uses the table, a test pins cents per model | Yes | `gateway.ts`'s only cost call site (`tokensToCostCents(result.usage)`) is unaffected; `credits.ts` needed no change (it works in credit counts, not cents) — confirmed by reading it, matches the report's explanation; `ai.test.ts` pins exact cents for Opus 5 / Sonnet 5 / Haiku 4.5 input+output+cache-read, both 5m/1h cache-write multipliers, and the batch discount. |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat`)
- [x] Nothing outside scope (`ROUTES` still all-Opus is explicitly out of scope, correctly noted by the author)
- [x] Tests exercise the behavior, and none were weakened — scan hit is a `.toBeTruthy()` existence check (`MODEL_PRICES[id]` truthy) in a *new* test, not a loosened assertion on existing behavior; the actual cent values are separately pinned exactly elsewhere in the same block
- [x] Tenancy / idempotency: n/a (no tenant tables, no side effects touched); money in cents throughout; en/es text: n/a (no user-facing strings added)
- [x] Decisions recorded where needed: n/a, no new decision required

## Optional notes (not blocking)
- `cacheWriteTokens` was added to `tokensToCostCents`'s inline usage param but not to the shared `TokenUsage` type in `providers/types.ts` — reasonable given file ownership, but worth a follow-up card once a provider actually reports cache-write counts, so the field isn't forward-looking plumbing forever.
- The price-table comment cites a skill cache date of 2026-06-24, cross-checked 2026-09-26; consider a lightweight reminder (e.g. a dated TODO or a wave-gate check) to re-verify before the next model swap, since Anthropic pricing does change.
