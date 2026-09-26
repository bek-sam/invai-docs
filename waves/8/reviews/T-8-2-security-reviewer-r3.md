# Review of T-8-2 (round 3)

- Reviewer: security-reviewer on Sonnet 5
- Author: ai-engineer on Opus (report says Opus 5.5)
- Verdict: escalate

Per `independent-review`'s rules ("MUST NOT go past 2 rounds. Round 3 is always escalate"), this
is a process escalation. My technical read of the round-2 fix and the new scan follow, for the
tech lead to act on directly rather than a fourth review round.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend worktree add ../invai-backend-review-t82-r3 a32b682` | worktree at the fix SHA |
| `git diff bb075e8 a32b682 --stat` | `src/modules/ai/service.ts` (+16/-5) and `src/modules/ai/service.test.ts` (+10) only — `service.ts` is outside T-8-2's original owned-file list but matches wave.md's explicit grant ("T-8-2 may edit `ask()`... hunk-only, while T-8-4 edits the rest of the file"); the diff is entirely inside `ask()` plus one import line, confirming the grant was honored |
| `tsc --noEmit`, `biome check .`, full `vitest run` | clean; 79 files / 593 real tests pass |
| Live repro: `ask(ctx, { message: "hello\u0000world" })` | no longer throws — round-2 finding is closed |
| Scan for other pre-sanitizer stores of user text in text/jsonb columns, focused on `src/modules/ai/**` (the surface this card and its fixes touch) | `createDrafts`/`regenerateDraft` write `brief` into `listing_drafts.brief` (`text()`) before the gateway ever runs; reproduced live with the same Postgres `22021` error as the two prior rounds |

## Assessment

1. **The round-2 fix is sound and correctly scoped.** `sanitizeText` runs once on the incoming message before either of the two raw inserts that used to crash (`assistant_conversations.title`, `assistant_messages.text`), and the final assistant-turn persist now sanitizes both `text` and `toolCalls` (via `sanitizeDeep`, so nested tool-call `input`/`summary` strings are covered too) instead of the raw streamed accumulator. This matches exactly what round 2 asked for, and I couldn't make it crash.
2. **The requested scan surfaced a real instance of the same bug class, not a theoretical one.** `createDrafts` (`service.ts:249`) and `regenerateDraft` (`service.ts:277`) both write a caller-supplied `brief` straight to `listing_drafts.brief`, a plain Postgres `text` column, before `generateDraft` ever runs (draft generation is queued and processed later — by the time the gateway's sanitizer would see `vars.brief`, the crash has already happened on the insert). I reproduced it directly against `createDrafts`. This is the same shape, same root cause, same fix pattern (`sanitizeText` on the string before the first write) as the two rounds already closed — just a third entry point into the same underlying gap: **any place that persists caller-supplied AI-related text before the gateway is, by construction, outside the gateway's sanitizer.**
3. Not claiming this list is exhaustive — `updateDraft`'s content patch and `rejectDraft`'s `reason` write user text to the same table and likely share the shape, but I didn't reproduce them and won't block on that without evidence, per this round's own instruction.
4. No new tenancy, idempotency, or spend-breaker regression from this fix; the r1/r2 findings already on record (breaker fail-open alerting, now tracked in wave.md against B-17/B-18) are unaffected and unresolved by this round.

## Blocking findings
None against `a32b682` itself. The `createDrafts`/`regenerateDraft` `brief` gap is a new, confirmed finding outside this round's diff — recording it for the tech lead rather than blocking this round's fix on it, since escalation is where round-3 decisions belong.

## Checks
- [x] Only the granted `ask()` hunk changed
- [x] Nothing outside scope
- [x] New test is real, not weakened
- [x] No tenancy/idempotency/money regression
- [x] Decision recorded (commit message)

## Optional notes (not blocking)
- Same fix shape as rounds 1–2 would close this: `sanitizeText(brief)` immediately before `createDrafts`'s insert and `regenerateDraft`'s update.
