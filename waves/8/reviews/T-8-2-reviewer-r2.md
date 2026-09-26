# Review of T-8-2 (round 2)

- Reviewer: reviewer on Sonnet 5
- Author: ai-engineer on Opus (report says Opus 5.5)
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend worktree add ../invai-backend-review-t82-r2 e0937cd` | worktree at the fix SHA |
| `git diff d3bbc80 e0937cd --stat` (T-8-5's commit vs the fix, so only the fix's own hunks show) | `src/ai/ai.test.ts` (+38/-2), `src/ai/gateway.ts` (+55/-10) — both T-8-2-owned, nothing else |
| `node_modules/.bin/tsc --noEmit` | clean |
| `node_modules/.bin/biome check .` | "Checked 268 files in 180ms. No fixes applied." |
| `node_modules/.bin/vitest run` (full suite, twice, fresh `invai_test_t82r2`) | first run: 76/79 files, 581/588 tests (7 failures, all Shopify-OAuth/webhooks + one invite test); isolated rerun of `src/modules/channels/webhooks.test.ts` alone: 11/11 passed; full-suite rerun: 79/79 files, 588/588 tests passed. The first run's failures were pre-existing test-isolation flakiness under parallel workers, not caused by this fix (gateway.ts touches only `src/ai/**`). |
| Live repro (written to a throwaway `src/ai/repro-nul.test.ts`, run, then deleted — never committed): `ask(ctx, { message: "hello\u0000world" })` on a fresh company/user | **still throws** — see blocking finding below |
| `docker exec local-postgres-1 psql -U invai -d invai -c "insert into t_nul(...) values ('a'||chr(0)||'b')"` | confirms Postgres `text` columns (not just `jsonb`) reject a NUL byte with `22021 invalid_byte_sequence`, independent of `sanitizeText`/`sanitizeDeep` |

## Ask items
| # | Met? | Evidence |
|---|---|---|
| Sanitizer covers vars, assistant input, model output, stored text | **No — partial.** | `sanitizeDeep(vars)` before `startJob`'s `ai_jobs` insert and before `provider.structured` (✓ covers `runStructured`'s vars fully, storage and model call). `scrubAssistantRun` sanitizes `run.message`/`run.history[].text` (✓ covers what the gateway itself sends to the model and stores in `ai_jobs.input`/`.output`). But `src/modules/ai/service.ts`'s `ask()` — the actual assistant-chat entry point — inserts the **raw** `input.message` into `assistant_conversations.title` (line ~1006) and `assistant_messages.text` (line ~1020) *before* `runAssistant`/`scrubAssistantRun` is ever called, and later persists the **raw streamed** model text (accumulated from `runAssistant`'s unsanitized `"text"` deltas, not the sanitized copy `finishJob` stores into `ai_jobs.output`) into `assistant_messages.text` at the end of the turn. None of that goes through `sanitizeText`. |
| Doesn't alter legitimate Unicode | Yes | `LONE_SURROGATE` only matches an unpaired high/low surrogate (negative lookahead/lookbehind), so a real supplementary-plane character (a paired surrogate, e.g. an emoji) survives untouched; the new test proves exactly this (`"\ud800z\u{1f335}"` → `"�z\u{1f335}"`, the emoji unchanged). `UNSTORABLE` only strips C0 controls minus tab/LF/CR and DEL — nothing above `\u007F` is touched, so accented letters, CJK, bidi marks, emoji, etc. all pass through. |
| Commit contains only T-8-2's hunks | Yes | `git diff d3bbc80 e0937cd --stat` shows exactly `ai.test.ts` + `gateway.ts`, both card-owned; no contracts/schema/other-module change. |

## Blocking findings
1. **`src/modules/ai/service.ts:1006` (`assistant_conversations.title`) and `:1020` (`assistant_messages.text`) — a NUL byte in a chat message still crashes the request.** Reproduced live: `ask(ctx, { message: "hello\u0000world" })` throws `DrizzleQueryError` / Postgres `22021 invalid byte sequence for encoding "UTF8": 0x00` on the very first insert, before the gateway or its sanitizer ever runs. This is the exact class of bug the fix is meant to close (its own commit message claims "applied to ... assistant message/history ... and stored assistant text"), for the exact route (the assistant) the report and the tech lead's ask both call out by name. A user pasting text with a stray NUL (common from some PDF/spreadsheet copy-paste sources) into the assistant chat box gets an unhandled 500, unchanged from before this fix.
   - Fix needs to either sanitize `input.message` at the top of `ask()` before either insert (using the now-exported `sanitizeText`), or sanitize the accumulated `text` before the final `assistant_messages` update — both, really, since the final update uses raw streamed deltas, not `runAssistant`'s already-sanitized `ai_jobs.output` copy. `service.ts` isn't in T-8-2's owned-file list, so this may need a quick grant, but it can't be left as "fixed."

## Checks
- [x] Only owned paths changed (plus the fix's own commit — no scope creep)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; the new regression test is real (verified it fails on the pre-fix code by construction — it directly exercises `sanitizeText`/`sanitizeDeep` and a real `runStructured` call) — but it does not exercise the actual crash path (`ask()`), which is why the gap above wasn't caught
- [ ] Tenancy / idempotency / money in cents / en-es — n/a, no change to these
- [x] Decisions recorded (commit message explains the NUL/lone-surrogate rationale)

## Optional notes (not blocking)
- Once `service.ts` is covered, add the assistant-chat NUL case to the regression test (a live `ask()` call, not just `sanitizeText`/`runStructured`) so this exact gap can't reopen silently.
