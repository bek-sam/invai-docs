# Report: T-2-3 Account security (backend)
Author: backend-foundation on Opus 5.5

```
Card: T-2-3  Owner: backend-foundation  Scope ref: always-in-scope: security
Owned (edit): src/auth.ts, auth migration, src/lib/auth-mail.ts, tests next to them
              (also used, inside my role: src/api/{context,orpc}.ts, src/lib/errors.ts,
               src/test/fixtures.ts, src/db/schema/tenancy.ts, src/modules/README.md)
Read-only: integrations/vendors/mailer.ts
Risk flags → co-reviewers: auth, pii → security-reviewer
```

Commits (invai-backend, `main`, not pushed):
- `6ff0890` schema + migration `0011_auth_security` (two_factors table, users.two_factor_enabled, backfill: users with an accepted invite are verified)
- `3c45e05` everything else

## Built
- **Email verification** (`src/auth.ts`, `src/lib/auth-mail.ts`): sign-up emails `${WEB_ORIGIN}/verify-email?token=<jwt>` in en/es (link works for 24 h). Unverified users can sign in. Autosign-in after verification is off, so a leaked link can't skip the password or 2FA.
  - No email is sent for server-side sign-ups (the seed has no request and marks its users verified).
  - No email is sent when the address has a pending invite: accepting the invite verifies it (`afterAcceptInvitation`).
- **`EMAIL_NOT_VERIFIED` gate** (`src/api/orpc.ts` `EMAIL_VERIFIED_PROCEDURES`, checked in the guard after the permission check): `shipping.buy`, `shipping.batchBuy`, `billing.checkout` and `billing.portal` only. It applies to user **and** floor sessions and reads the live DB value per request (`Context.emailVerified`). Connecting a channel is not gated (the PM's change). Module owners must not re-check it in their handlers.
- **Password reset:** link `${WEB_ORIGIN}/reset-password?token=`, 1 h, single use. It deletes every Better Auth session and sends a "password changed" notice. It also verifies the email, since the link reached the inbox.
  - Unknown emails get the same body and status.
  - The mail is sent in the background, so a known email doesn't wait on SMTP (timing test: under 1 s with a 2 s mail server).
- **Two-step sign-in:** the Better Auth `twoFactor` plugin (issuer "InvAI", TOTP plus 10 backup codes, both encrypted with `BETTER_AUTH_SECRET`). It's optional.
  - Turning it on needs a **verified email**. This is my addition: it stops someone who signed up with a stranger's address from locking the real owner out after a reset.
  - "On" and "off" notice emails are sent.
- **Change password:** needs the current password. A `before` hook forces `revokeOtherSessions: true` whatever the client sends. Sends a notice.
- **Sessions:** the standard `listSessions` and `revokeSession`.
- **Rate limits** (per IP): `/request-password-reset` 5/15 min, `/reset-password` 10/15 min, `/send-verification-email` 5/15 min, `/change-password` 10/15 min. Better Auth's own `/two-factor/*` limit is 3 per 10 s, plus 5 codes per challenge and a 15-minute account lock after 10 wrong codes.
- **Language:** `users.locale` is now a Better Auth user field (input allowed, validated `en|es`), so sign-up and `updateUser` can set it. That's what T-2-4 AC4 needs, and it picks the email language.
- **Fixtures:** `createUser` now defaults to `emailVerified: true` (pass `false` to test the gate).

## Client calls for T-2-4 (`better-auth/react`, add `twoFactorClient()` from `better-auth/client/plugins`)
| Flow | Call | Notes |
|---|---|---|
| Sign up | `authClient.signUp.email({ email, password, name, locale })` | `locale` is `"en"` or `"es"` and sets the email language. The verification email goes out on its own. |
| Verify page `/verify-email?token=` | `authClient.verifyEmail({ query: { token } })` | Success returns `{status:true}`. Errors: `TOKEN_EXPIRED`, `INVALID_TOKEN`. It doesn't sign in. Reusing a link returns success. |
| Resend | `authClient.sendVerificationEmail({ email: user.email })` | Signed in, an already-verified user gets `EMAIL_ALREADY_VERIFIED`. |
| Banner state | `useSession().data.user.emailVerified` (also `.twoFactorEnabled`, `.locale`) | `EMAIL_NOT_VERIFIED` (403) from oRPC `billing.checkout` / `billing.portal` / `shipping.buy` / `shipping.batchBuy` should show the prompt. |
| Forgot page | `authClient.requestPasswordReset({ email })` | Always `{status:true}`. Show "If that email has an account, we sent a link". Don't pass `redirectTo`: the email links to `/reset-password?token=` directly. |
| Reset page `/reset-password?token=` | `authClient.resetPassword({ newPassword, token })` | Expired or used tokens give `INVALID_TOKEN` (400). Afterwards, send the user to login (every session was signed out). |
| Login | `authClient.signIn.email({ email, password })` | With 2FA the response is `{ twoFactorRedirect: true, twoFactorMethods: ["totp"] }` and no session. With the plugin's `onTwoFactorRedirect` option, the client calls it. |
| 2FA code | `authClient.twoFactor.verifyTotp({ code, trustDevice? })` | Wrong code: `INVALID_CODE` (401). Too many: `TOO_MANY_ATTEMPTS_REQUEST_NEW_CODE`, then sign in again. The challenge cookie lasts 10 min. |
| Backup code | `authClient.twoFactor.verifyBackupCode({ code })` | Each code works once. |
| Enable 2FA | `authClient.twoFactor.enable({ password })` → `{ totpURI, backupCodes }` | Show a QR of `totpURI` and the backup codes once. Then `authClient.twoFactor.verifyTotp({ code })` turns it on (this rotates the session cookie). An unverified email gets `EMAIL_NOT_VERIFIED` (403). A wrong password gets `INVALID_PASSWORD`. |
| Disable 2FA | `authClient.twoFactor.disable({ password })` | |
| New backup codes | `authClient.twoFactor.generateBackupCodes({ password })` | |
| Change password | `authClient.changePassword({ currentPassword, newPassword })` | Other sessions are always revoked. The current one gets a new cookie. Wrong password: `INVALID_PASSWORD`. |
| Sessions | `authClient.listSessions()` / `authClient.revokeSession({ token })` | `listSessions` needs a session less than 1 day old (`SESSION_NOT_FRESH` 403): ask the user to sign in again. |
| Name / language | `authClient.updateUser({ name, locale })` | A `locale` other than en/es gives 400. |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Verification | Yes | `auth.test.ts` "email verification" (8 tests) and `email-gate.test.ts` (7). Live: Mailpit en and es emails, checkout/portal 403 `EMAIL_NOT_VERIFIED`, Shopify connect 200 while unverified, checkout 200 after verify. Floor packer: 404 (past the gate) when verified, 403 when unverified. Invite accept test. Seed users verified. |
| 2 Reset | Yes | Identical answers for known and unknown emails (live and tested), `/reset-password?token=`, TTL 59–60 min asserted, both sessions `null` after reset, reuse and expired give `INVALID_TOKEN`, 429 on the 6th request per IP (rate-limited instance test). |
| 3 MFA | Yes | Issuer InvAI and 10 backup codes (checked from the live URI). Sign-in returns `{"twoFactorRedirect":true,"twoFactorMethods":["totp"]}` with no session. Wrong code 401. Code generated by an independent RFC 6238 script works. Backup code works once. Disable works. |
| 4 Change password, sessions | Yes | Wrong current 400. Other session revoked even with `revokeOtherSessions:false`. List shows 2 sessions, revoking one works, and another user's token is ignored. |
| 5 Floor PIN unaffected | Yes | Test: a floor token still builds a floor context after a reset. Live: seed packer PIN login still works. |
| 6 Tests cover all paths | Yes | 30 new tests, including token reuse and expiry and the enumeration checks. |

## Checks I ran
I verified on a clean worktree holding HEAD plus only my files, because the shared tree has T-2-1 and T-2-5 work in progress. With pnpm 12, `pnpm run` tries an install in a worktree, so I called the binaries directly.

| Command | Result |
|---|---|
| `tsc --noEmit` | exit 0 |
| `biome check .` | Checked 209 files, no fixes |
| `vitest run` (invai_test_t23) | 43 files passed, 1 failed. **303 passed, 1 failed:** `rls-coverage.test.ts` "tables without RLS are only the Better Auth identity tables" → `expected [ 'two_factors' ] to deeply equal []` (see Blocked) |
| `tsup` | Build success |

In the shared tree, `pnpm typecheck` and `pnpm lint` currently fail only in T-2-5's uncommitted `shipping/router.ts:58` and `shipping/service.ts:1310`.

## Exercised for real
API on :3230 against `invai_t23_copy`, with Mailpit:
- Sign-up sent "Confirm your email for InvAI" with a `localhost:5173/verify-email?token=` link. The Spanish sign-up got "Confirma tu correo en InvAI".
- Verify: 200. Reuse: 200 `{status:true,user:null}`. Garbage token: 401 `INVALID_TOKEN`.
- Reset request: known and unknown emails both answered `200` with the same body in 3–4 ms. The reset link worked, reuse gave 400 `INVALID_TOKEN`, and both old sessions returned `null`. The "password was changed" notice arrived.
- Enabling TOTP gave the URI `otpauth://totp/InvAI:…&issuer=InvAI&digits=6&period=30`. Confirming the code returned 200 and the "Two-step sign-in is on" notice arrived. MFA sign-in → `twoFactorRedirect`, wrong code gave `INVALID_CODE`, the right code signed in.
- Change password: the other session returned `null`, and the session count went from 2 to 1.
- Enabling 2FA while unverified: 403 `EMAIL_NOT_VERIFIED`.

## Decisions
- The gate lives in the central guard as a path list, not in each handler, so T-2-1 and T-2-5 don't need to touch it. It keys on the oRPC path, which the HTTP handler always passes. Direct `call()` without `path` skips it, and that only happens in server code.
- 2FA requires a verified email, and a completed reset verifies the email. Both close the account pre-hijacking path.
- The verification link lasts 24 h (Better Auth's default is 1 h) so a slow or spam-filtered email doesn't strand a new shop. The token is a stateless JWT, so reuse is harmless.
- Mail send failures are logged (without the address) and never thrown. That keeps reset enumeration-safe. The trade-off: signing up can't report a failed send; the user resends.
- Didn't add a dependency: the tests generate TOTP codes with an RFC 6238 implementation built on `node:crypto`, which also proves the URI works in a real authenticator app.

## Known gaps and follow-ups
- Better Auth's rate-limit storage is in memory, per process. Across several API instances the limits multiply; move it to Redis (`secondaryStorage`) before scaling out. The IP comes from `x-forwarded-for`, the same trust assumption as decision 0008.
- Sign-up still reveals whether an email exists (`USER_ALREADY_EXISTS`). This was already there; the card only asked for reset to be enumeration-safe.
- `listSessions` returns the session tokens of the user's own sessions (that's how Better Auth works; `revokeSession` needs them).
- Rotating `BETTER_AUTH_SECRET` makes stored TOTP secrets and backup codes unreadable. That belongs in the runbook's key-rotation notes (docs-writer).
- A TOTP code can be reused within its 30 s window on a fresh challenge. That's Better Auth's behavior; each challenge itself can only be completed once.
- The API worked with every email provider mocked. The only mail was local Mailpit; nothing outbound.

## Blocked by other owners
- `src/db/rls-coverage.test.ts:13-21` (**security-reviewer**): add `"two_factors"` to `GLOBAL_TABLES`. It's a Better Auth identity table (user-keyed, like `accounts`, with no `company_id`) and the two-factor plugin needs it. Until then this one test fails. I didn't edit it.
- The instructions gave `REDIS_URL=redis://localhost:6379/23`, but Valkey only has 16 databases (0–15): `ERR DB index is out of range`. I used `/13` and flushed it afterwards. Other cards given `/2k` indexes will hit the same error.

## Processes and data
- Stopped: my API on :3230 (port free).
- Dropped: `invai_t23_copy`. Redis DB 13 flushed.
- The worktree `../invai-backend-t23wt` is removed.
- Shared dev DB untouched by me. It already had `0011` applied when I checked, so someone else ran the migration.
- Test DB `invai_test_t23` is left for re-runs.
