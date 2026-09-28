# Review of T-19-4 (round 1, mailer.ts hunk only)

- Reviewer: integrations-engineer on Sonnet 5
- Author: backend-foundation (fable)
- Verdict: approve

Scope of this co-review: only `invai-backend/src/integrations/vendors/mailer.ts` under the grant
(optional extra headers `List-Unsubscribe`/`List-Unsubscribe-Post`/`Message-ID`, keep the
placeholder/PIN-only skip; round 2 extended the grant to the "mail sent" log line for S-36).

## Evidence I re-ran
| Command | Result |
|---|---|
| `node_modules/.bin/vitest run src/integrations/vendors` | 1 file, 2 tests passed |
| `node_modules/.bin/vitest run src/modules/tenancy/demo-guards.test.ts src/modules/tenancy/pin-only.test.ts` (existing callers' skip-string assertions) | 2 files, 15 tests passed |
| `diff <(git show 8b9b6f0:src/integrations/vendors/mailer.ts) src/integrations/vendors/mailer.ts` | empty — working tree matches HEAD, nothing uncommitted in this file |
| Read `nodemailer@10.0.10` dist/cjs `mail-composer/index.js` (`compile()`) and `mime-node/index.js` (`setHeader`, `messageId()`) | confirms header/id handling below |

## Findings, by grant item
1. **Extra headers (List-Unsubscribe, List-Unsubscribe-Post, Message-ID).** `Mail` gained optional
   `headers?: Record<string,string>` and `messageId?: string` (0af819a). Traced through
   `nodemailer`'s `MailComposer.compile()`: custom `mail.headers` are added first via `addHeader`,
   then the fixed list (`from…message-id…date`) is applied via `setHeader`, which normalizes the
   key and **replaces** any existing entry for that key rather than appending — so a caller could
   not accidentally get two `Message-ID` headers even if it duplicated the key in both `headers`
   and `messageId`. `notify.ts` doesn't do that: it puts `List-Unsubscribe`/`-Post` in `headers`
   and the id in the dedicated `messageId` field, so there is no overlap to begin with. Finally
   `message.messageId()` only generates a random id `if (!messageId)` (i.e., if the header isn't
   already set) — confirmed in `mime-node/index.js:939-946`. Net: no duplication, no override,
   deterministic id passed through unmolested. Callers that don't set these fields (vendor portal
   `email/index.ts:29`, `portal/index.ts:21`, `invites.ts` `deliverInviteMail`, `auth-mail.ts`
   `sendAuthMail`) get nodemailer's own random Message-ID and no extra headers, exactly as before
   — their `mail` argument types (`{to,subject,text,html?}` / `AuthMail`) don't even have a
   `headers` or `messageId` field, so this isn't just "unused today", it's structurally unreachable
   for them.
2. **Placeholder/PIN-only skip kept intact.** `isPlaceholderEmail`/sample-workspace checks and
   their early returns are untouched in shape (same order, same log lines, same guard). The one
   change (776697b) replaced the inline literals `"skipped:sample-workspace"`/`"skipped:pin-only"`
   and the 0af819a-introduced `skipped?: MailSkipReason` return field with a named `MAIL_SKIPPED`
   map plus a `mailSkipReason(result)` reader, and reverted `sendMail`'s return type back to
   exactly `{ messageId: string }` (its pre-T-19-4 shape). This is a smaller blast radius than the
   round-1 version, not a bigger one: the sentinel string *values* are unchanged (verified against
   `demo-guards.test.ts:291` and `pin-only.test.ts:90`, which hard-code the literals and still pass
   unmodified), and no caller's return-type contract changes. `notify.ts` reads the skip reason via
   `mailSkipReason(sent)` rather than a `.skipped` field — a legitimate way to satisfy AC2 ("returns
   `skipped` with the reason") without widening `sendMail`'s signature. I'd call this in-grant: it's
   the same skip mechanism, exported for reuse, not a new skip path.
3. **Round 2 — "mail sent" log line (S-36).** Confirmed the log no longer contains `mail.to`
   anywhere on the send path (grep of the diff and the current file: the only remaining `to`
   reference is `transport.sendMail({ from: MAIL_FROM, ...mail })`, which is the actual SMTP call,
   not a log). It now logs `companyId` (undefined for `"account"` sends — correct, account mail
   isn't tied to a tenant) and `toHash` (`sha256Hex(address).slice(0, 16)`), plus the pre-existing
   `subject` and `messageId`. Ops still gets: which tenant, a stable per-address correlator for a
   support ticket, the subject line, and the id — enough to answer "did shop X's mail send" without
   writing a real address to disk. `mailer.test.ts` proves the negative directly (asserts no log
   line contains the raw `to`) for both a company send and an `"account"` send, and proves the
   positive (a "mail sent" line still carries `companyId`). Both tests passed when I re-ran them.
   The "mail skipped" lines (sample-workspace, PIN-only) never logged an address before or after —
   no regression there.

## Acceptance criteria (card-level AC2/AC3, mailer.ts's share of them)
| # | Met? | Evidence |
|---|---|---|
| AC2 (skip returns a readable reason, deterministic Message-ID) | yes | `mailSkipReason()` + `messageId` field, traced above |
| AC3 (List-Unsubscribe / List-Unsubscribe-Post headers) | yes | `headers` passthrough traced through nodemailer, no override |
| S-36 (no raw recipient in logs) | yes | `mailer.test.ts` both tests pass; grep confirms no other log call sites |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat` — file matches HEAD exactly; the three commits
      touching it are each mailer.ts-only diffs, all inside the grant)
- [x] Nothing outside scope (no unrelated refactors, no touch to transport setup, no new deps)
- [x] Tests exercise the behavior, and none were weakened (new `mailer.test.ts` is additive; the
      pre-existing skip-string tests elsewhere pass unmodified)
- [x] Idempotency n/a here (mailer.ts has no side-effect key of its own; that's `notify.ts`'s
      `dedupeKey`, out of my scope); money n/a; en/es n/a (mailer.ts carries caller-built copy only)
- [ ] Decisions recorded where needed — n/a, no cross-cutting decision from this hunk

## Optional notes (not blocking)
- `subject` is still logged verbatim on "mail sent". Today's subjects (gang-sheet names, shop
  names, auth notices, invite copy) don't carry buyer PII, but that log field predates T-19-4 and
  is outside this grant — flagging only so a future caller with a personalized subject line doesn't
  reintroduce a leak through a door S-36 didn't cover. Not asking for a change here.
