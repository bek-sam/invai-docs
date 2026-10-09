# Review: T-28-2 account security backend (security co-review, round 1)
Reviewer: security-reviewer on opus. Author: backend-foundation on opus. Flags: auth (+ migration).
Inputs: card, report, invai-backend `074c922` `e42b38d`, invai-docs `d57c482` (ADR 0025), plan-architect item 4.

## Verdict: changes-required (2 blocking, both Medium)

## Blocking findings
1. **S-57 Medium, lockout race.** `src/auth.ts` before-hook `lockedFor` + after-hook `recordFailure` (`src/lib/account-lockout.ts`): the lock is checked before the endpoint and the failure is counted only after the scrypt verify, so a parallel burst all passes the check. Proof: `src/modules/tenancy/security.test.ts` "S-57 …" (`it.fails`; without marker: 40 of 40 parallel wrong sign-ins got 401, none 423, "expected 40 to be <= 10"). Scenario: an attacker with K IPs fires K x 20 guesses in one burst per 30-min window instead of 10; a right password in the burst still gets a session. Fix: reserve the attempt atomically in the before-hook (upsert `failures + 1 RETURNING`, 423 when over threshold or locked), clear on success, give the count back on non-password errors; keep the one-email rule.
2. **S-58 Medium, MFA postponed forever.** `src/lib/mfa.ts` `restartGraceIfNewlyRequired` via `tenancy/service.ts` `changeRole`/`setMemberStatus` (also invite accept, remove + re-invite): every not-required -> required transition restarts the grace, including demote-then-promote of the same user. Proof: same file "S-58 …" (`it.fails`; without marker: "still blocked after re-promotion: expected false to be true"). Scenario: two admins demote/re-promote each other every 6 days; neither ever turns on two-step, B-188 never holds. Fix: at most one restart per user (`users.mfa_required_since`, set the first time, never cleared; restart only while null). AC11 still holds.

## Threat model walked (no finding)
- Email variants: Better Auth `sign-in.mjs:314-315` rejects non-emails (whitespace) with INVALID_EMAIL (not counted) and looks up `email.toLowerCase()`; our key is trim+lowercase of the same JS string, so every variant that reaches a user maps to its key. Unicode: exact match in PG, no folding gap.
- Other sign-in paths: only `/sign-in/email` verifies a password and makes a session (plugins: organization, invite-preview, twoFactor). Email OTP not configured (`OTP_NOT_CONFIGURED`), no magic link/social. Two-factor verify has Better Auth's own 10-code lock. Reset needs the inbox and clears the lock (correct). Invite accept needs a session.
- Account-exists: unknown users get Better Auth's dummy hash; 423 path identical for both; lock email is `void`ed and goes to the real inbox only. Lock-email flood bounded to 1 per 30 min per address.
- HMAC: `hmacHex(BETTER_AUTH_SECRET, "sign-in-lock:"+email)`, stored only, never returned; rotating the secret resets counters (harmless). Optional: derive a purpose key like `links.ts`.
- Password history: change checks only after the current password verifies; reset needs a live token; at most 10 scrypt verifies behind 10/15 min per-IP limits; no admin set-password path exists. Not counted toward lockout: `/change-password` current-password guesses (session needed). Optional.
- MFA guard: all `user`/`floor` procedures for user sessions; exempt set is `me.get`, `me.switchOrg` only; per-user rule so org switching can't dodge; demo flag `input: false`; `twoFactorEnabled` is `input: false` (no `/update-user` route to it); `/two-factor/enable` on a verified TOTP throws `TOTP_ALREADY_ENABLED`; disable refused while required; backup-code regeneration needs password + enabled 2FA. REST `/api/v1` uses the same router and guard. Past-deadline `/organization/create` doesn't restart (still required).

## ADR 0025: not accepted yet
Must change before acceptance: item 1 "counted before the password check, so a burst tests at most 10" (S-57); item 3 "the grace restarts at most once per user" (S-58); one line that rotating `BETTER_AUTH_SECRET` resets all counters. Everything else is accepted as written.

## RLS coverage grant: agreed
`sign_in_failures` (pre-auth, HMAC key, no user or company) and `password_history` (per user, like `accounts`) are correctly global; added to `GLOBAL_TABLES` with a reason.

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` | exit 0 |
| `biome check` on my 2 test files | no fixes |
| `vitest run src/lib/account-security.test.ts src/db/rls-coverage.test.ts src/modules/tenancy/security.test.ts src/api --reporter=dot` | 16 files passed; 109 passed, 2 expected fail (S-57, S-58) |
| S-57/S-58 without `.fails` | both red for the stated assertion |
| `scan-test-weakening.sh invai-backend 074c922~1` | mailer `vi.mock` (dependency, fine); `it.fails` hits are S-57/S-58 and T-28-3's S-56 |

Recorded: `security/v1-review.md` S-57, S-58 (owner backend-foundation, due 2026-11-08); DPP rows updated (password history verified; lockout and MFA wait on S-57/S-58).
Round 2: flip both tests to `it`; I re-run them and accept 0025.
