# Review of T-8-2 (round 2)

- Reviewer: security-reviewer on Sonnet 5
- Author: ai-engineer on Opus (report says Opus 5.5)
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend worktree add ../invai-backend-review-t82-r2 e0937cd` | worktree at the fix SHA |
| `git diff d3bbc80 e0937cd --stat` | only `src/ai/ai.test.ts` and `src/ai/gateway.ts` — both T-8-2-owned |
| `tsc --noEmit`, `biome check .` | both clean |
| `vitest run` (full suite) | 79/79 files, 588/588 tests on a clean rerun (an earlier run had 7 unrelated flaky failures in Shopify-OAuth tests, confirmed unrelated by an isolated rerun that passed 11/11) |
| Live repro (throwaway test, not committed): `ask(ctx, { message: "hello\u0000world" })` | throws `DrizzleQueryError`, Postgres `22021 invalid byte sequence for encoding "UTF8": 0x00`, on the `assistant_conversations` insert — before the gateway sanitizer runs |
| `docker exec local-postgres-1 psql ...` inserting `chr(0)` into a plain `text` column | confirms this isn't jsonb-specific: any raw NUL byte reaching any Postgres `text`/`jsonb` column crashes the query, so every insertion point matters, not just `ai_jobs` |
| Read `sanitizeText`/`sanitizeDeep`, `UNSTORABLE`, `LONE_SURROGATE` in full | see findings below |

## Threat-model checklist (availability / input-handling angle, `ai` flag)

1. **Coverage claim ("vars, assistant input, model output, stored text").** Verified true for `runStructured` (`vars` sanitized before both the `ai_jobs` insert and the model call) and for what `runAssistant` itself stores into `ai_jobs.input`/`.output` (`scrubAssistantRun`, and `sanitizeText(text.slice(0,4000))` on both the normal and aborted-stream paths). **Not true for the assistant's own conversation storage** in `src/modules/ai/service.ts`: `ask()` inserts the raw `input.message` into `assistant_conversations.title` and `assistant_messages.text` *before* `runAssistant` is even called, and later writes the raw accumulated stream text (not the gateway's sanitized copy) into `assistant_messages.text`. Confirmed by live reproduction above — a NUL byte in a chat message still 500s the request, unchanged from the bug this fix set out to close. This is an availability gap (any authenticated user of any tenant can 500 their own chat endpoint with an accidental or deliberate stray NUL byte — trivial DoS-by-typo against their own session, not cross-tenant), not a data-exposure one, but it's exactly the surface named in the ask ("assistant input"), so I can't sign off on that line item.
2. **Doesn't alter legitimate Unicode.** Confirmed correct. `LONE_SURROGATE`'s lookahead/lookbehind pair only strips an unpaired half-surrogate, never a real paired supplementary character (verified against the test's own emoji case, and by reading the regex: a genuine surrogate pair never satisfies either alternative's negative assertion). `UNSTORABLE` is scoped to C0 controls (minus tab/LF/CR) and DEL only — nothing that carries real linguistic or symbolic meaning is in range. No over-broad stripping that could corrupt buyer names, non-Latin scripts, or emoji in shop content.
3. **Scope.** The commit is exactly two files, both card-owned (`gateway.ts`, `ai.test.ts`); no drive-by change to another card's files, no contracts touch. Confirmed via diff against the immediately preceding commit (`d3bbc80`, T-8-5), so only this fix's own hunks were compared.
4. **The new test's honesty.** It's a real assertion against real code (`sanitizeText`/`sanitizeDeep` unit-level, plus a real `runStructured` call whose `ai_jobs` row is fetched back and checked), not a mock of the unit under test. It just doesn't reach far enough — it stops at the gateway boundary and never calls `ask()`, which is where the actual bug still lives.

## Blocking findings
1. **`src/modules/ai/service.ts:1006,1020` — the assistant chat route still crashes on a NUL byte**, reproduced live (see evidence). The fix's sanitizer is real and correctly scoped for everything that flows through `gateway.ts`, but the assistant feature's own conversation-persistence code (owned outside this card, per wave.md's split) writes the user's raw message — and later the raw streamed model text — straight to Postgres `text` columns without ever passing through `sanitizeText`. This needs to be closed (either by sanitizing at the top of `ask()`, or by widening this card's owned-file grant to include the two `service.ts` insert/update sites) before this can be called fixed for the surface the tech lead specifically asked about.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope
- [x] Tests exercise real behavior; not weakened — but incomplete (misses the actual crash path)
- [x] No tenancy/idempotency/money regressions introduced by this diff
- [x] Decision recorded (commit message)

## Optional notes (not blocking)
- Once closed, the r1 review's still-open note about the breaker's Valkey fail-open path lacking an alert remains outstanding and is unaffected by this fix.
