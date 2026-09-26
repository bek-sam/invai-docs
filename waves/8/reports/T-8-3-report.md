# T-8-3: AI cost table and mock hardening (B-45)

## What changed

**`invai-backend/src/ai/models.ts`**
- Added `MODEL_PRICES`, a per-model list-price table (cents per million tokens) covering Opus 5
  (`DEFAULT_MODEL`), Sonnet 5 (`SONNET_MODEL`, new export) and Haiku 4.5 (`HAIKU_MODEL`, new
  export). Each entry has input, output, cache write (5m and 1h TTL) and cache read rates, plus
  Message-Batches input/output rates.
- Source cited in the file: Anthropic's Claude API pricing via the `claude-api` skill's "Current
  Models" reference, skill cache date **2026-06-24**, cross-checked against
  `docs.claude.com/en/docs/about-claude/pricing` on **2026-09-26** (today). Cache write = 1.25x
  input (5m) / 2x input (1h); cache read = 0.1x input; batch = 50% off input/output — Anthropic's
  standard multipliers, applied to each model's base rate.
- `tokensToCostCents` now reads only from `MODEL_PRICES` — no hard-coded Opus 5 numbers remain in
  the function body. Signature is `(usage, model = DEFAULT_MODEL, opts?: { batch?, cacheTtl? })`:
  the extra params are optional and default to the exact prior behavior, so the existing call site
  in `gateway.ts` (`tokensToCostCents(result.usage)`, owned by T-8-2, not touched) still compiles
  and returns identical cents for Opus 5. An unrecognized model id falls back to `DEFAULT_MODEL`'s
  price instead of throwing.

**`invai-backend/src/ai/providers/mock.ts`**
- The mock provider no longer throws on a prompt id it has no fixture for. It now logs a warning
  (via the project's `logger("ai:mock")`, not `console.warn`, so it respects `LOG_LEVEL`) and
  returns a best-effort schema-valid default built by a small generic zod-shape walker
  (`defaultForSchema`), then still runs the real `prompt.schema.parse(...)` on the result — so a
  shape the walker can't handle surfaces as an ordinary parse error, not a silent lie.
- Existing fixtures (`listing_copy`, `trademark_judge`) are unchanged.

**`invai-backend/src/ai/credits.ts`**: no changes needed. `chargeCredits` takes a `credits` count
as input and doesn't itself compute cents; the actual cost-in-cents path (`tokensToCostCents`,
called from `gateway.ts`, owned by T-8-2) already routes through `models.ts`. Verified this by
reading `gateway.ts`'s `finishJob` — it calls `tokensToCredits`/`tokensToCostCents` from
`models.ts` for both `aiJobs.costCents` and the credit ledger.

**`invai-backend/src/ai/ai.test.ts`**: added a new `describe("AI cost table and mock hardening
(T-8-3)")` block (own block, didn't touch T-8-2's `describe("prompt isolation and spend breaker
(T-8-2)")` block) with 9 tests:
- Pins exact cents for Opus 5, Sonnet 5 and Haiku 4.5 (input, output, cache read).
- Pins the 5-minute and 1-hour cache-write multipliers.
- Pins the batch discount.
- Confirms an unrecognized model id falls back to Opus 5 pricing without throwing.
- Confirms `tokensToCostCents(usage)` (no model arg — the shape `gateway.ts` uses) still returns
  the same cents as before.
- Confirms the mock provider returns a schema-valid default (and not a thrown error) for a prompt
  id it has no fixture for.

## Staging note (shared-file surgery)

`ai.test.ts` is being edited concurrently by T-8-2 in the same working tree. Rather than
`git add -p` on the live, interleaved diff, I rebuilt the file as `HEAD + my import line + my new
describe block` in an isolated scratch copy, verified it compiles/lints/tests cleanly **on its
own** in a throwaway `git worktree` of `HEAD` (no T-8-2/T-8-1/T-8-4 code needed), then staged that
exact blob directly into the index (`git hash-object -w` + `git update-index --cacheinfo`) so the
commit contains only my hunk. The live working tree (with everyone's in-progress edits) was left
untouched throughout. `git diff --cached` for `ai.test.ts` shows exactly: the one import line and
the appended describe block — nothing from T-8-2's imports/tests.

Also note: HEAD moved during this task (the architect landed "Wave 8 contract stubs" — the
`productionPartner`/trademark-review columns — partway through), so the diff base was refreshed
before staging; the final staged content is against the current HEAD.

## Verification

- `tsc --noEmit` (whole repo): 0 errors touching my 3 files. (Two pre-existing errors remain in
  T-8-2's in-progress `breaker.ts`, referencing `env.AI_DAILY_*_CAP_CENTS` not yet added to
  `env.ts` — not mine, not in scope.)
- `biome check` on `models.ts`, `providers/mock.ts`, `credits.ts`, `ai.test.ts`: clean.
- `vitest run src/ai/ai.test.ts`: full file (with T-8-2's in-progress work included) — 30/30 pass.
  In the isolated verification worktree (my hunk only, against clean HEAD) — 19/19 pass.
- Test DB `invai_test_t83` and Redis DB `/3` used per the card's numbers; both dropped/flushed
  after each run, including after the isolated-worktree run.

## Known gaps / notes for the reviewer (data-analyst)

- `ROUTES` in `models.ts` still points every route at `DEFAULT_MODEL` (Opus 5) — out of scope for
  this card; the price table just makes a future per-route model change ("a cheaper model for a
  bulk route is a one-line change here") price correctly once made.
- `cacheWriteTokens` is a new optional field I added to `tokensToCostCents`'s usage parameter, not
  to the shared `TokenUsage` type in `providers/types.ts` (not in my file ownership) — no provider
  currently reports cache-write token counts, so this is forward-looking plumbing, exercised only
  by my pinned tests, not by any live call site.
## Commit

`874bb7f` — "AI cost table by model + mock hardening on unknown prompts (T-8-3, B-45)", on top of
`e958638` (architect's Wave 8 contract stubs). Committed to `main` in the shared working tree, not
pushed — per the wave rules, push happens after the co-reviewer (data-analyst) approves.
