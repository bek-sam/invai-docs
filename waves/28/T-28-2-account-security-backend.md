# T-28-2: Account security for the Amazon DPP: lockout, password history, required two-step sign-in (backend)

| Field | Value |
|---|---|
| Wave | 28 |
| Scope ref | `always-in-scope: compliance` (Amazon DPP 2025-11-25, `security/v1-review.md` DPP table; backlog B-185, B-186, B-188 backend half) |
| Spec | the DPP gap table in `security/v1-review.md` plus this card |
| Owner | backend-foundation |
| Reviewer | `reviewer` (fable, a different model from the author) |
| Co-reviewers | security-reviewer (opus; auth). The migration is the author's own area, so no separate backend-foundation co-review |
| Risk flags | auth, migration |
| Model | opus |

## Owned paths (edit)
- `invai-backend/src/auth.ts`, `invai-backend/src/api/**` (except `src/api/webhooks.ts`), `invai-backend/src/lib/**`, `invai-backend/src/env.ts`
- `invai-backend/src/db/schema/auth.ts` and `src/db/schema/tenancy.ts` (wherever `users`, `accounts` and the new global tables live) and one generated migration (`pnpm db:generate --name auth_lockout_password_history_mfa`)
- `invai-backend/src/modules/tenancy/**` (the `me.get` handler for `Me.mfa`, grace restart on role change, invitation and org creation; tests)
- `invai-backend/src/test/**` only if a fixture needs a helper (for example backdating a user's grace)
- `invai-backend/.env.example`, `invai-backend/README.md` (auth section)
- `invai-docs/decisions/0025-account-lockout-password-history-mfa.md` plus its index row in `decisions/README.md` (type security, status proposed; the security-reviewer accepts it in review). T-28-3 adds a row too: stage only your hunk (`git add -p`)

## Read-only paths
- `invai-contracts/**` (T-28-1 provides `MFA_REQUIRED`, `Me.mfa`, `AUTH_ERROR_CODES`, `AccountLockedBody`), every other backend module, `src/api/webhooks.ts`, `invai-web/**`

## Depends on
- T-28-1 (contract). Start now; the contract lands within the first hour. Until then build against the agreed shape below.

## Interfaces promised
- Better Auth sign-in refusal while locked: `ACCOUNT_LOCKED`, HTTP 423, body `AccountLockedBody` (with `retryAfterSec`).
- Better Auth change/reset refusal: `PASSWORD_REUSED`, HTTP 400. Refusal to turn off two-step sign-in: `MFA_DISABLE_NOT_ALLOWED`, HTTP 403. Codes come from the contract's `AUTH_ERROR_CODES`.
- oRPC: `MFA_REQUIRED` (403, `data.deadline`) from every procedure except `MFA_EXEMPT_PROCEDURES = {me.get, me.switchOrg}`.
- `me.get` returns `mfa: { required, enabled, deadline }` for web sessions (omitted for floor sessions).

## Definitions (one rule everywhere)
- **Required** = the user holds an active `owner` or `admin` membership in any org whose `companies.demo` is false (`MFA_REQUIRED_ROLES = ["owner", "admin"]`). Vendor orgs only have the `vendor` role and are excluded (no buyer PII in the portal). Sample workspaces (`startDemo` makes every user owner, `modules/tenancy/demo.ts:81`) never count; add the demo flag to `Membership` in `src/api/context.ts` if needed. Required is per user, not per active org, so `me.switchOrg` can't dodge it.
- **Grace start** = `users.mfa_grace_starts_at timestamptz NOT NULL DEFAULT now()` (no backfill: existing rows get the migration time). It is reset to now() when a user who is not yet required **becomes** required (role change to owner/admin, invitation accepted as owner/admin, creating a real org). **Deadline** = start + `MFA_GRACE_DAYS` (default 7, allowed 0–14).

## Acceptance criteria
Lockout (B-185):
1. Given an email address (normalized: trimmed, lowercased), when 10 consecutive wrong-password sign-ins happen for it (any IP), then it is locked for 30 minutes (`ACCOUNT_LOCK_THRESHOLD=10`, `ACCOUNT_LOCK_MINUTES=30` in `env.ts`): every sign-in for it, even with the right password, gets `ACCOUNT_LOCKED` (423) with `retryAfterSec`, and no session is created. The counter is keyed on an HMAC of the normalized email (never the address) in a global table, for example `sign_in_failures(email_hmac pk, failures, locked_until, notified_at)`, counted atomically with `INSERT … ON CONFLICT DO UPDATE SET failures = failures + 1 RETURNING`.
2. A successful sign-in clears the row. The lock ends on its own after 30 minutes. Completing a password reset clears it.
3. When the count crosses the threshold and a user with that email exists, the user gets one "account locked" email (existing mailer and notify pattern, en/es; Mailpit locally) saying how long the lock lasts and that a password reset unlocks it now; a warn log with the user id only. No second email for the same lock.
4. Unknown emails lock exactly the same way (same 423, same timing class), so the lock gives no account-exists signal. The per-IP limit (decision 0008) is unchanged.
5. 20 parallel wrong attempts lock once and send one email (a test proves it).

Password history (B-186):
6. Given a user who changes or resets the password, when the new password equals the current one or any of the previous 9 (last 10 in total), then it is refused with `PASSWORD_REUSED` (400) and nothing changes. Only hashes are stored (Better Auth's own hasher; verify with `ctx.context.password.verify`), at most 10 per user, deleted with the user. Suggested: append in `databaseHooks.account.create/update.after`; refuse in the before-hook (for a reset, find the user from the token).
7. The first password set at sign-up, by invite acceptance and by the seed enters the history.

Required two-step sign-in (B-188):
8. Given a required user without two-step sign-in, when the deadline has passed, then every oRPC procedure except `MFA_EXEMPT_PROCEDURES` returns `MFA_REQUIRED` with the deadline, whatever org is active. Placement: in `guard` (`src/api/orpc.ts`), after the permission check and before `EMAIL_NOT_VERIFIED`, only for `sessionKind === "user"`, never for public or station procedures.
9. Better Auth routes (two-factor enable/verify, sign-out, password reset, email verification resend), floor PIN/station sessions, webhooks, SSE `/events` and `/l` links are not affected (the last two sit outside oRPC; say so in 0025).
10. Inside the grace period nothing is blocked, and `me.get` returns `mfa.required=true, enabled=false, deadline=<iso>`. Users who are not required get `required=false, deadline=null`.
11. Given a long-time office user promoted to admin after their own grace would have ended, when they next call the API, then they are not blocked: their grace restarted at the promotion and `me.get` shows the new deadline (a test proves it). A user whose only owner membership is a sample workspace is never required (a test proves it).
12. While a user is required, `/two-factor/disable` is refused with `MFA_DISABLE_NOT_ALLOWED` (403).
13. The demo seed and the golden path keep working: seeded users are inside their grace, so `pnpm db:seed` and the E2E suites need no change. Test fixtures create users inside the grace; tests that need the past-deadline case backdate `mfa_grace_starts_at` explicitly.

Records:
14. `decisions/0025-...` states the exact values (10 / 30 min / HMAC-keyed per email, unknown emails too / last 10 / 7-day grace restarted on promotion / owner+admin in non-sample orgs / vendors excluded / exempt procedures and the non-oRPC paths) and the trade-off that anyone can lock an email for 30 minutes by guessing (the reset link and the time limit are the mitigation). Updating the DPP table text in `security/v1-review.md` is the security-reviewer's job; say in the report what changed.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test` in invai-backend (full suite once at the end; `set -o pipefail`, log to a file, print FAIL/Error lines and the tail).
- Exercise for real on your own API: `PORT=3121 pnpm dev:api` (do not use 3000; check `lsof -iTCP:3121 -sTCP:LISTEN` first). Script (curl or `tsx`), against the shared dev DB but **only with a user you create for the run** (sign up `t282-<ts>@desertbloom.test`; never lock or change a seeded login):
  1. 10 wrong passwords → 11th with the right password gets 423 `ACCOUNT_LOCKED`; Mailpit (`localhost:8025/api/v1/messages`) shows one lock email. 10 wrong passwords for a never-registered email → the same 423.
  2. Change password to the current one → 400 `PASSWORD_REUSED`; to a new one → 200; back to the first → 400.
  3. Make the user an owner (create an org) with `mfa_grace_starts_at` backdated in the DB → any oRPC call (for example `orders.list`) → 403 `MFA_REQUIRED`; `me.get` → 200 with `mfa`; enable TOTP (compute the code in the script) → the same call → 200; `/two-factor/disable` → 403 `MFA_DISABLE_NOT_ALLOWED`.
  4. Refused case: presser PIN session on the floor API still works (`me.get` with the station token).
- Scratch DB or seed work: pin `REDIS_URL` to Valkey DB 12 and `SEED_OUTPUT_FILE` to `/tmp/t282-seed.json` before any `db:reset`, migrate or seed of a scratch database (lessons 2026-09-29, 2026-10-01). Do not reset the shared dev DB.

## Out of scope
- Web screens (T-28-4). Floor PIN lockout (exists, S-06). API-key rotation (part of the DPP row, separate backlog item). WebAuthn or SMS factors. Changing the per-IP limit. Requiring two-step for vendor users.

## Budget
- About 3 hours. Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned (for example Better Auth gives no hook that can refuse a sign-in before the session is created).
