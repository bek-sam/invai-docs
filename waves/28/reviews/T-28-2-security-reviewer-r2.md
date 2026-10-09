# Review: T-28-2 account security backend (security co-review, round 2)
Reviewer: security-reviewer on opus. Author: backend-foundation on opus. Flags: auth (+ migration).
Inputs: round 1 file, invai-backend `03998af` `95324fe`, invai-docs `f1e34f8` (ADR 0025), report round 2 section.

## Verdict: approve

## Round-1 findings
- **S-57 fixed.** `reserveAttempt` counts in the before-hook (one upsert, `allowed = failures <= threshold`); 423 is thrown there, and Better Auth's `dispatch.mjs` rethrows before-hook errors without running after-hooks, so a refused attempt is never given back. `giveBack` only for non-`INVALID_EMAIL_OR_PASSWORD` API errors (sign-in.mjs: INVALID_EMAIL before the verify; EMAIL_NOT_VERIFIED is off, `requireEmailVerification: false`); a 500 stays counted (fails closed).
- **S-58 fixed.** `restartGraceIfNewlyRequired` restarts only while `users.mfa_required_since` is null and sets it when a required user is demoted or deactivated; `setMemberStatus` now calls it on both transitions. No member-removal path exists (org mutations disabled), so re-invite goes through the same once-only rule.
- **Test flip:** `git show 03998af -- src/modules/tenancy/security.test.ts` is exactly two lines, `it.fails` -> `it` on S-57 and S-58; nothing else in my file changed.
- **Migration 0043:** one `ALTER TABLE "users" ADD COLUMN "mfa_required_since" timestamptz` (nullable, no default: catalog-only, no table rewrite); journal adds idx 43 only.
- **ADR 0025:** items 1 and 3 and the secret-rotation line now say what round 1 asked. Accepted (2026-10-09).

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` | exit 0 |
| `vitest run src/lib/account-security.test.ts src/modules/tenancy src/db/rls-coverage.test.ts src/api --reporter=dot` | 24 files, 167 passed, 0 expected-fail, exit 0 |
| Temporary probe file (8 tests, deleted after the run) via `app.request` | all passed, see below |
| 40 parallel wrong passwords, known vs unknown email | both `{401: 10, 423: 30}`; 1 lock email for the known one, 0 for the unknown one; right password afterwards 423, no cookie |
| Right password at position 0/4/9/20/39 inside a parallel burst of 40 | tested passwords (401 + 200) always <= 10; at 4 and 9 it got 200 (it was among the 10 tested); at 0, 20 and 39 it got 423 with no cookie |
| 20 wrong + 20 whitespace-variant (INVALID_EMAIL) attempts in one burst | `{400: 4, 401: 6, 423: 30}`: the given-back attempts don't widen the burst; right password afterwards 423 |
| MFA cycles: first promotion office -> admin, then deactivate/reactivate, demote/deactivate/reactivate/re-promote, admin -> owner | first promotion gets a fresh grace (AC11); every later cycle leaves the past-deadline user blocked; a legacy (null `mfa_required_since`) admin who is deactivated and reactivated stays blocked |

## Optional notes (not blocking)
- A user who was required before 0043 and never demoted can get one restart via a fresh invite accept. That is bounded at once per user and acceptable.
- `giveBack` after a stale reset (lock expiry while a request is in flight) can undercount by one; it would need a request lasting the whole 30-minute lock. Negligible.

Recorded: `security/v1-review.md` S-57, S-58 Fixed; the DPP lockout and MFA rows are updated (they close on push, and MFA also needs T-28-4); ADR 0025 and its index row are set to accepted.
