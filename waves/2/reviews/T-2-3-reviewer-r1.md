# Review of T-2-3 (round 1)

- Reviewer: reviewer on Opus
- Author: backend-foundation on Opus 5.5
- Verdict: approve

Review range: invai-backend `6ff0890` (schema), `3c45e05` (implementation), `240a19e` (RLS
allowlist for `two_factors`, committed by the author with the tech lead's permission after the
report; security-reviewer's co-review covers that line's safety).

## Evidence I re-ran
Clean git worktree at `240a19e`, `node_modules` symlinked (no `pnpm install`), test DB
`invai_test_r23`, `REDIS_URL=redis://localhost:6379/12`.

| Command | Result |
|---|---|
| `node_modules/.bin/tsc --noEmit` | exit 0, no output |
| `node_modules/.bin/biome check .` | Checked 209 files, no fixes needed |
| `node_modules/.bin/tsx src/db/migrate.ts` | up to date |
| `node_modules/.bin/vitest run` | 44 files, **304 passed**, 0 failed (includes `rls-coverage.test.ts`, which failed on the author's copy before `240a19e`) |
| `node_modules/.bin/tsup` | Build success |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend 5d80c52` | Only hit: `vi.mock` of `integrations/vendors/mailer` (a read-only external dependency the card explicitly calls through `sendMail`, not the unit under test) — not weakening. `push-void.test.ts` in the same scan is T-2-5's uncommitted work, out of scope here. |

## Exercised for real
API on `:3293` against `invai_r23_copy` (dropped after), Mailpit on `:8025`, Redis db 12 (flushed
after).

- **Sign up → verify:** signed up, got "Confirm your email for InvAI" in Mailpit with
  `http://localhost:5173/verify-email?token=<jwt>`. No token in server logs (`grep -i "token=" `
  on the API log: nothing). Verify → `{"status":true}`. Reuse → same `{"status":true}` (Better
  Auth's harmless-reuse semantics for a stateless JWT). Garbage token → 401.
- **Reset:** `request-password-reset` for a known and an unknown email both returned the exact
  same `200` body (`"If this email exists in our system..."`) in single-digit ms. Reset succeeded;
  a second call with the same token returned 400 (reuse refused); two sessions that existed before
  the reset (one from sign-up, one from a later sign-in) both went `null` on `get-session`
  afterwards.
- **TOTP:** enabling returned `otpauth://totp/InvAI:<email>?secret=...&issuer=InvAI&...` and 10
  backup codes. Confirmed the first code (generated independently from the URI's secret with a
  hand-rolled RFC 6238 implementation) turned it on. Fresh sign-in returned
  `{"twoFactorRedirect":true,"twoFactorMethods":["totp"]}` with no session cookie; a wrong code
  gave 401; the generated code signed in.
- **`EMAIL_NOT_VERIFIED` gate:** an unverified owner got `EMAIL_NOT_VERIFIED` (403) on
  `billing.checkout` and on `shipping.buy` (called directly, before any order-item lookup — the
  guard runs ahead of the handler). The same unverified user could connect a channel
  (`channels.connect`) with a 200 and a created connection, and could check out successfully once
  verified. Second account tested the same channel-connect-while-unverified case to rule out a
  fluke from the first account's later verification.

I did not stand up a floor PIN session live (would need seed data not present in the DB copy I
made); I relied on the automated coverage instead: `auth.test.ts` "floor PIN sessions keep working
through a reset" and `email-gate.test.ts` "floor sessions: an unverified PIN user can't buy a
label, a verified one can," both in the 304 passing tests, plus the `context.ts` diff (below).

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Email verification | Yes | Live: en/es emails, sign-in while unverified, verify/reuse/garbage-token, unverified channel connect succeeds, checkout blocked then allowed. `auth.test.ts` covers invite-accepted and seed/server-side sign-up verified-by-default cases. |
| 2 Password reset | Yes | Live: identical-answer enumeration safety, 1 h TTL (asserted in `auth.test.ts` 59–60 min), single use, both prior sessions revoked, rate limited (`auth.test.ts` "auth rate limits"). |
| 3 MFA | Yes | Live: issuer InvAI, 10 backup codes, `twoFactorRedirect`, wrong/right code, backup-code single use (`auth.test.ts`). Optional for everyone; no forcing logic found. |
| 4 Change password / sessions | Yes | `auth.test.ts` "change password and sessions": wrong current password rejected, other sessions always revoked even when the client asks otherwise, list/revoke work, another user's token is ignored. |
| 5 Floor PIN unaffected | Yes | `context.ts` diff only adds `emailVerified` to the floor context's live DB read; role/company resolution unchanged. Confirmed via the two named tests above (not live-exercised by me). |
| 6 Full test coverage | Yes | 30 new tests (`auth.test.ts` + `email-gate.test.ts`), including token reuse/expiry and enumeration checks. |

## Central guard (`src/api/orpc.ts`)
`EMAIL_VERIFIED_PROCEDURES.has(path.join("."))` runs inside `guard`, the single `os.middleware`
every module router is built through (`pub` / `authed`, both defined in `orpc.ts`). Checked every
module router file (`grep -rln "from \"../../api/orpc\""`) — all 14 import `pub`/`authed` from
here; `grep -rn "\bos\."` outside `orpc.ts` finds nothing, so no router builds a raw handler that
skips the guard. `path` is oRPC's own route-segment array (`["shipping","buy"]`, etc.), which
matches the router nesting in `src/api/router.ts` one-to-one — verified this isn't confusable with
`meta.permission` (a different string set by `proc("shipping.buy")`, coincidentally similar-looking
but a separate mechanism). No bypass found.

One correct design note, not a finding: `shipping.retry` (retries a tracking-push notification, no
money) and `shipping.void` (refunds a label) both carry the same `permission: "shipping.buy"` but
are deliberately not gated — retrying a push and voiding/refunding a label don't move money, so
gating them behind email verification would only be user-hostile. Confirmed by reading their
contract docstrings, not just by inference.

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`auth.ts`, new `lib/auth-mail.ts`, `context.ts`, `orpc.ts`,
      `lib/errors.ts`, `test/fixtures.ts`, `modules/README.md`, tests next to these — all consistent
      with the card's "also used, inside my role" note in the report; `rls-coverage.test.ts` is
      security-reviewer's own commit, reviewed separately)
- [x] Nothing outside scope; web (T-2-4) and SSO untouched
- [x] Tests exercise the behavior, and none were weakened
- [x] Tenancy: no new `company_id` table; the schema comment explains why the Better Auth tables
      have none; `withSystem`/`withTenant` unaffected. Idempotency: n/a (no webhook/job here).
      Money: n/a. En/es text present for every account email.
- [x] Decisions recorded (in the commit body and `auth.ts` comments): 24 h verification TTL
      (vs. Better Auth's 1 h default), MFA-needs-verified-email, reset-verifies-email

## Optional notes (not blocking)
- The card's two scope additions beyond the letter of the acceptance criteria:
  - **MFA requires a verified email to turn on.** Approve. Otherwise someone who signs up with a
    stranger's or mistyped address could enable MFA and lock the real owner out permanently, even
    after a reset (a reset alone doesn't disable MFA). This closes a real gap the card didn't
    anticipate.
  - **A completed reset marks the email verified.** Approve. Only someone with inbox access can
    complete a reset, so this is at least as strong a verification proof as clicking the
    verification link, and it's a clean self-service recovery path for a legitimate owner whose
    account was created (accidentally or by someone else) with their real email but never
    verified.
- `sendAuthMail`'s health-check flag reports `mocks.mail: true` even when `SMTP_URL` resolves to
  the local Mailpit default (`env.ts:157`) — cosmetic only, mail was actually delivered to Mailpit
  in every live test above. Not this card's code to fix (pre-existing `env.ts` flag), but worth a
  one-line note to whoever owns that health endpoint.
