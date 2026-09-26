# Review of T-8-2 (round 3)

- Reviewer: reviewer on Sonnet 5
- Author: ai-engineer on Opus (report says Opus 5.5)
- Verdict: escalate

Per `independent-review`'s rules ("MUST NOT go past 2 rounds. Round 3 is always escalate"), this
is a process escalation, not a new blocking finding against the round-2 fix — see the assessment
below for what I'd have said if a third round were allowed to approve.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend worktree add ../invai-backend-review-t82-r3 a32b682` | worktree at the round-2-fix SHA |
| `git diff bb075e8 a32b682 -- src/modules/ai/service.ts` | hunk-only inside `ask()`: sanitizes `input.message` once (`message`), used for the conversation title, the user-message row, and `runAssistant`'s input; sanitizes the final stored `text` and `toolCalls` via `sanitizeDeep`. No touch outside `ask()` — respects the wave.md grant ("T-8-2 may edit `ask()`... hunk-only, while T-8-4 edits the rest of the file") |
| `tsc --noEmit`, `biome check .` | both clean |
| `vitest run` (full suite, fresh `invai_test_t82r3`) | 79/79 files pass, 593/593 real tests pass (a 594th test was my own throwaway repro, deleted after use, whose one intentional failure is discussed below) |
| **Live repro 1** — `ask(ctx, { message: "hello\u0000world" })` on a fresh company/user, in a throwaway test file (deleted, never committed) | **no longer crashes** — completes normally, `"done"` event yielded. The round-2 finding is fixed. |
| **Live repro 2** — scanning for another pre-gateway text/jsonb write, I found `createDrafts`/`regenerateDraft` (`src/modules/ai/service.ts:249`/`277`) write a caller-supplied `brief` straight into `listing_drafts.brief` (a plain `text()` column) before any draft generation or gateway call. Reproduced live: `createDrafts(tx, ctx, { designId, channels: ["etsy"], brief: "warm tone\u0000 for gift buyers" })` throws `DrizzleQueryError` / Postgres `22021 invalid byte sequence for encoding "UTF8": 0x00` on the `listing_drafts` insert. | **confirmed, not theoretical** — same crash class as the two rounds already fixed, on a third, still-open entry point. |

## Ask items
| # | Answer |
|---|---|
| Re-run the live NUL chat repro | Fixed — confirmed above. |
| Scan for any other pre-sanitizer path | Found one, confirmed live: `createDrafts` and `regenerateDraft` in `src/modules/ai/service.ts` write `brief` to `listing_drafts.brief` (text) before `generateDraft` ever calls the gateway. (`updateDraft`'s content-patch and `rejectDraft`'s `reason` write user text to the same table too; I did not reproduce those — naming them as the same shape, not as confirmed findings, per "don't block on theoretical cases.") |

## Blocking findings
None against the round-2 fix itself — it does exactly what it claims for the assistant-chat surface, confirmed live, cleanly scoped, with a real regression test.

One new, confirmed gap outside this round's fix: **`src/modules/ai/service.ts:249,287` — a NUL byte in a listing draft's `brief` still crashes `createDrafts`/`regenerateDraft`.** Whether this blocks T-8-2 r3 specifically or becomes a fast-follow (like the r1 breaker-alert note that went to wave.md's backlog) is the tech lead's call — flagging per the escalate path rather than deciding it myself, since we're past round 2.

## Checks
- [x] Only owned/granted paths changed (`ask()` hunk-only, per wave.md's grant)
- [x] Nothing outside scope
- [x] New test is real (a genuine chat message with embedded NUL through `svc.ask`, asserting the stored text is clean and the turn completes)
- [x] Tenancy/idempotency/money/en-es — no regression
- [x] Decisions recorded (commit message)

## Optional notes (not blocking)
- If `createDrafts`/`regenerateDraft`'s `brief` gets a similar one-line `sanitizeText` fix, the same pattern (sanitize immediately before the first raw insert of caller text) closes it the same way this round did.
