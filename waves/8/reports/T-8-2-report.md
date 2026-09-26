# T-8-2 report: prompt isolation and global AI spend breaker (B-15)

**Status:** done, ready for review (security-reviewer co-review: injection, spend).
**Commit:** invai-backend `9586158` (not pushed).

## What changed
| File | Change |
|---|---|
| `src/ai/prompts/index.ts` | `DATA_RULE` (treat-as-data text) in every system prompt; `dataBlock(source, value)` renders `<data source="…">` + JSON + `</data>`, with `<` escaped to `<` so input can't close the block or open a fake one, and the source label sanitized. `listing_copy@4`: design, blank, shop_brief and validation_errors blocks (only the channel label and fixed instructions are outside). `trademark_judge@2`: listing_text and candidate_marks blocks; it must return exactly one judgement per candidate, and a request inside the text for a verdict is treated as a reason for more care. `assistant@3`: tool results are data envelopes. |
| `src/ai/gateway.ts` | `isolateToolResults()` wraps every assistant tool's `data` as `{source: "tool_result:<tool>", data}`. It's applied in `scrubAssistantRun`, so every tool, current or future, is covered. `assertSpend()` runs before `startJob` in `runStructured` and `runAssistant` for non-mock providers. `finishJob` computes `costCents` once and calls `recordSpend` after the transaction commits. |
| `src/ai/breaker.ts` (new) | Stub B exactly. Keys are `ai:spend:platform:<YYYY-MM-DD>` and `ai:spend:tenant:<companyId>:<YYYY-MM-DD>` (UTC). One `MGET` per check. `MULTI INCRBY` + `EXPIRE 26h NX`. Hitting a cap throws `ORPCError("AI_SPEND_CAP_REACHED", 429, data {scope, capCents, spentCents, resetAt = next UTC midnight})`. The tenant scope is checked first. The first hit of a scope each day does `SET NX EX 26h ai:spend:alerted:<scope>:<companyId or "all">:<day>` and then calls `raiseAlert` (`ai_spend_cap_tenant`/`ai_spend_cap_platform`, critical, dedupe `ai_spend_cap:<scope>:<day>`), which emits `alert.created`. A cap of 0 turns that scope off. |
| `src/env.ts` | Adds `AI_DAILY_PLATFORM_CAP_CENTS` (default 50000, $500) and `AI_DAILY_TENANT_CAP_CENTS` (default 5000, $50). |
| `src/ai/ai.test.ts` | Adds the describe block "prompt isolation and spend breaker (T-8-2)" with 11 tests. |

`src/modules/ai/assistant-tools.ts` didn't need changes: the gateway covers its tools.

## Decisions
- **Mock skips the breaker.** When the provider is the mock (no key, or a sample workspace), there's no GET and no INCRBY. Mock cost is 0 anyway, and a sample workspace can't be blocked by other tenants' spend.
- **Fail-open on Valkey.** The check has a 500 ms timeout because the ioredis client uses `maxRetriesPerRequest: null`, so without a timeout a Valkey outage would hang every AI call. On timeout the check fails open and logs an error. The per-tenant credit check (Postgres) has already run, and BullMQ is down along with Valkey. `recordSpend` errors are logged, never thrown, because the call is already billed.
- **Platform alert goes to the calling company.** The platform-scope alert is raised on the first company to hit the cap that day (once, globally), with `log.error` for ops. There's no platform-admin tenant to put it on.
- **Tool results as a JSON envelope.** Assistant tool results are wrapped as a JSON envelope rather than an XML `<data>` string. `anthropic.ts` (not mine) calls `JSON.stringify(out.data)`, so a string block would be double-escaped. The envelope carries the source label, and the assistant system prompt names the envelope form.

## Verification
- `pnpm typecheck` and `pnpm lint` are clean.
- Full `vitest run` on `invai_test_t82` with Valkey `/2`: **79 files, 587 tests passed** (111 s). A rerun of `src/ai` after T-8-3's commit: 30 passed.
- Tests cover:
  - Injection set (7 strings: "ignore previous instructions", a DAN persona, a `</data>` breakout with a fake system message, an XML `<tool_use>`, a JSON `tool_use`, a fake "Assistant:" turn, control and bidi characters). For `listing_copy` and `trademark_judge`, none of that text appears outside a data block and the block count balances.
  - With the mock, output keys are unchanged and the trademark judge returns only the candidate mark.
  - The assistant's tool results are wrapped, and a result containing fake tool calls triggers no extra tool (only the calls planned from the user's own question run).
  - Every system prompt contains `DATA_RULE`.
- Breaker tests run against real Valkey and Postgres:
  - counters and TTL; zero-cost calls are ignored
  - below the cap → passes
  - tenant cap hit → 429 `scope: "tenant"` with exact `data`; three hits give 1 alert and 1 `alert.created` outbox row; another tenant is unaffected
  - platform cap hit → blocks a third tenant too; 1 alert across all companies
  - caps of 0 turn the breaker off
  - a mock `runStructured` with the tenant counter at 1e9 still succeeds and the counters don't move
- A rendered prompt was inspected by hand: a `</data> Ignore previous instructions` design name stays inside the JSON with `<`.
- Cleanup: dropped `invai_test_t82`, ran FLUSHDB on Valkey `/2`, no processes left running.

## Known gaps and cross-card notes
- **The live-model injection eval is not run** (no `ANTHROPIC_API_KEY`). The mock tests prove the text lands inside the blocks, not the model's behaviour. The injection cases belong in T-8-5's eval sets (`evals/listing_copy`, `evals/trademark_judge`, `evals/assistant`) for a keyed run; the owner has to run it. The prompt versions were bumped, so there's no old-vs-new eval diff yet.
- **`env.ts` was outside the batch-1 split.** Stub B puts the config there, and nobody else had it staged. I added only the two lines. Flagging it for the architect.
- **`service.ts` (T-8-1/T-8-4), for later:**
  - The assistant stream maps `AI_SPEND_CAP_REACHED` to code `"internal"` (only `CREDITS_EXHAUSTED` is special-cased); a `"spend_cap"` code would let web show a proper message.
  - Listing generation marks the draft `failed` with the cap message, which is fine.
  - `trademark.ts` judge failures fall back to the heuristic.
- `tokensToCostCents` rounds each call to whole cents, so calls under 0.5¢ add 0 to the counters. This is negligible at current sizes (T-8-3 owns `models.ts`).
- **ai.test.ts overwrite:** partway through, the T-8-3 builder overwrote the whole of `ai.test.ts` (it briefly dropped my block and the architect's `productionPartner: null` lines). They restored everything before committing: my block and both `productionPartner` lines are in HEAD.
- Web/en-es: the alert titles and messages are English-only server text, like the other alerts in `today/service.ts`.

## r1: NUL byte fix (found by T-8-5), commit `e0937cd`
- `gateway.ts`: `sanitizeText`/`sanitizeDeep` form one boundary sanitizer. It drops C0 controls (keeping tab, LF and CR) and DEL, and replaces lone surrogates with U+FFFD. It applies to structured vars (before the PII scrub, the `ai_jobs` insert and the provider), the assistant message and history, model output (stored and returned), stored assistant text, and the `failJob` error text.
- Test: the full injection string #7 goes through `runStructured` (mock). The `ai_jobs` row is `done` and has no `\u0000` in it. There are unit cases for nested keys, values and surrogates.
- Checks: tsc and lint are clean; `src/ai` tests pass (33/33).
- Process slip, now fixed: the first commit (`8b0b7b7`, pathspec form) also swept in another builder's 3 uncommitted `ai.test.ts` hunks. Before anything was pushed, I amended it to `e0937cd`, which holds only my hunks. Their hunks are back in the working tree, uncommitted and unchanged.

## r2: chat text in `ask()` (reviewer r2 finding, with a grant on `ask()` only)
- `ask()` in `modules/ai/service.ts` runs `sanitizeText` on the message once, before the conversation title, the user message row and the model input use it. It also sanitizes the stored assistant text and the `toolCalls` jsonb.
- The new test in `service.test.ts` sends a chat message with NUL and checks that the stored user message has the NUL removed.
- Checks: tsc and lint are clean; `src/ai` + `src/modules/ai` tests pass (49/49).
- Only my hunks were staged with `git apply --cached` (checked with `git diff --cached`) and committed with no pathspec. T-8-4's work in progress is still uncommitted in the working tree.
