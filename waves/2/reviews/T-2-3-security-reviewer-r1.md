# Review of T-2-3 (round 1)

- Reviewer: security-reviewer on Opus
- Author: backend-foundation on Opus 5.5
- Verdict: approve

Review range: invai-backend `6ff0890` (schema), `3c45e05` (implementation), `240a19e` (`two_factors`
added to `rls-coverage.test.ts`'s `GLOBAL_TABLES`).

## `two_factors` and RLS: decision

**Belongs in `GLOBAL_TABLES`, like `accounts`.** The table is keyed by `user_id`, has no
`company_id`, and every access path to it is Better Auth's own `twoFactor` plugin code, which
always scopes by `getSessionFromCtx(ctx).user.id` — never by a client-supplied user id. I grepped
`src/auth.ts` and the rest of `src` for any handler that queries `twoFactors` directly outside
Better Auth's adapter: none exists (`grep -n "two_factors\|twoFactors" src --include=*.ts` outside
tests and the schema/auth files: nothing). A tenant cannot reach another user's row through any
InvAI procedure, because no procedure takes a `userId` and reads this table.

`240a19e` was already committed (author, with the tech lead's permission) before I started;
committing my own duplicate would be a no-op since `git status` shows `src/db/rls-coverage.test.ts`
clean against `240a19e`. **No new commit made.** Confirmed the fix works: `vitest run` on a fresh
worktree passes all 304 tests including `rls-coverage.test.ts`'s "tables without RLS are only the
Better Auth identity tables."

## `invai_app` has full CRUD on `two_factors` — acceptable for v1

Confirmed: `drizzle/0001_grants_extensions.sql` grants `SELECT, INSERT, UPDATE, DELETE` on `ALL
TABLES` by default (`ALTER DEFAULT PRIVILEGES ... GRANT ... ON TABLES TO invai_app`), and nothing
in `6ff0890`/`3c45e05` revokes any of it from `two_factors`. So yes: `invai_app` — the single
Postgres role the whole API process uses — can `DELETE FROM two_factors` for any user.

This is **not new exposure introduced by this card**. It is the existing, already-accepted trust
model for every Better Auth identity table (`users`, `sessions`, `accounts`, `verifications`), all
of which also have full CRUD and no RLS, documented in `invai-docs/security/v1-review.md:48`
("The only tables without RLS are the 7 Better Auth identity tables, which the tenancy module
scopes explicitly") — `two_factors` is the 8th, added on the same terms. `sessions` in particular
is at least as sensitive (deleting a row there force-logs-out a user; the DB grant already allows
that).

The only way to actually delete or read another user's `two_factors` row is a bug in InvAI's own
application code (not a "tenant" acting through any authorization boundary — a tenant has no direct
DB credential; only the API server does). I checked every `/two-factor/*` endpoint
(`node_modules/better-auth/dist/plugins/two-factor/*.mjs` and `src/auth.ts`'s use of the plugin):
enable, disable, verify-totp, verify-backup-code and generate-backup-codes all resolve the target
row from the caller's own session, never from a request parameter. There is no admin/support
endpoint in this diff that takes an arbitrary user id and touches `two_factors`.

**Verdict: Low, non-blocking, matches existing precedent.** Recommend (not blocking) that
platform-sre's future work to move Better Auth off a single full-privilege role, or to `REVOKE
DELETE` on `two_factors`/`sessions`/`accounts` from `invai_app` and have Better Auth's adapter use
a narrower grant, be tracked as a hardening item — this is a good candidate for a `v1-review.md`
Low finding (defense-in-depth: if a future bug elsewhere ever constructs a raw
`db.delete(twoFactors)`/`db.delete(sessions)` with an attacker-influenced id, there's no DB-level
backstop). I did not find such a bug today, and closing this gap for a single global identity table
without doing it for `sessions`/`accounts` at the same time would be inconsistent, so it's out of
scope for this card.

## Threat model (auth, pii)
Entry points: Better Auth's own routes under `/api/auth/*` (`public`, no prior session — sign-up,
sign-in, verify-email, request/reset-password, two-factor/*), oRPC procedures gated `auth: "user"`
or `"floor"` (`EMAIL_VERIFIED_PROCEDURES`), the central `guard` in `src/api/orpc.ts`. Worst outcome
if broken: account takeover (someone else's password reset or MFA bypass) — **High**-class if
unmitigated. Data touched: password hash (`accounts`), session tokens (`sessions`), TOTP secret and
backup codes (`two_factors`) — the last two are the new PII-adjacent surface this card adds.

## Evidence I re-ran
Same worktree as the primary reviewer (`240a19e`, `node_modules` symlinked, `invai_test_r23`,
`REDIS_URL=redis://localhost:6379/12`).

| Command | Result |
|---|---|
| `node_modules/.bin/vitest run` | 304/304 passed |
| `grep -rn "\bos\." src --include=*.ts \| grep -v orpc.ts \| grep -v .test.ts` | nothing — every router built from `pub`/`authed`, guard cannot be bypassed |
| `grep -n "token=" /tmp/r23-api.log` (live API log, see below) | nothing — no verify/reset token ever logged |
| `grep -n "log\.\(info\|warn\|error\)" <(git show 3c45e05 -- src/auth.ts src/lib/auth-mail.ts)` | 5 calls, all `{userId}` or `{kind}`, no email/token/secret |
| `node -e` script asserting `symmetricEncrypt` use in `node_modules/better-auth/dist/plugins/two-factor/index.mjs` | confirmed: TOTP secret and backup codes are Better-Auth-encrypted (`storeBackupCodes: "encrypted"`, `symmetricEncrypt({key: ctx.context.secretConfig, ...})`, derived from `BETTER_AUTH_SECRET`) before the row is written — not InvAI's own crypto, the library's, correctly wired by config only |
| `grep -n "maxFailedAttempts\|durationMs\|rateLimit" node_modules/better-auth/dist/plugins/two-factor/*.mjs` | confirms the report's claims: 10 wrong codes → 15 min lock (`maxFailedAttempts ?? 10`, `durationSeconds ?? 900`), `/two-factor/*` rate limit 3/10s, 5 attempts per pending challenge (`TOO_MANY_ATTEMPTS_REQUEST_NEW_CODE`) — all Better Auth defaults, not custom code, so no test debt was skipped by relying on them |

## Live exercise (own port 3293, `invai_r23_copy`, Mailpit :8025, Redis db 12; all dropped/flushed
after, port freed)
- Verification token appears in the Mailpit-captured email body only, never in server logs.
- TOTP: `auth.test.ts` asserts `two_factors.secret` and `.backupCodes` in the DB don't contain the
  plaintext secret/codes returned to the client — reran this test live against my own copy DB and
  independently queried the row: ciphertext confirmed, not the `otpauth://` secret.
- Backup code: used once, second use on a fresh sign-in returned 401 (live).
- Rate limiting / lockout not independently brute-forced live (would take 10+ requests against the
  real 15-minute lock); relied on the `node_modules` source check above plus the existing
  `auth.test.ts` "auth rate limits" describe block, which enables Better Auth's rate limiter in a
  dedicated test instance and asserts the 429s.

## Acceptance criteria (security-relevant subset)
| # | Met? | Evidence |
|---|---|---|
| Reset enumeration-safety and timing | Yes | Identical body/status live for known and unknown emails; `auth.test.ts` also asserts comparable timing (mail is fire-and-forget) |
| Reset token single-use, 1 h TTL | Yes | Live reuse → 400; `auth.test.ts` asserts 59–60 min TTL and an explicitly-expired token → 400 `INVALID_TOKEN` |
| MFA: issuer, TOTP, backup codes, lockout | Yes | Issuer "InvAI" confirmed in the URI; backup codes stored encrypted; lockout is Better Auth's own, verified in `node_modules` source, not asserted for real (impractical to brute-force live) |
| Secrets at rest (TOTP secret) | Yes | Encrypted with `BETTER_AUTH_SECRET`-derived key by the library; test proves ciphertext ≠ plaintext |
| No PII/token leakage in logs | Yes | Grep across the diff's log calls and the live API log |
| Central guard can't be bypassed | Yes | Every router built from `pub`/`authed`; no other `os.` usage found |
| `two_factors` RLS allowlist | Yes (already committed, `240a19e`) | See decision above |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed — I made no code edits; `rls-coverage.test.ts` was already at the
      intended state via `240a19e` before I started (see decision above)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; scan (run by the primary reviewer, same repo/range) found no
      weakening
- [x] Tenancy: `two_factors` correctly excluded from the RLS-required set with a written reason;
      `invai_app`'s full CRUD on it is pre-existing precedent, not a new gap (see above);
      idempotency n/a; no PII in logs, prompts or analytics
- [x] Decisions recorded: this file records the `two_factors` RLS decision and the CRUD-scope
      judgment; recommend a `v1-review.md` Low entry for the CRUD hardening item (owner:
      platform-sre or backend-foundation, not blocking this card)

## Optional notes (not blocking)
- Recommend logging a `v1-review.md` Low finding: "`invai_app` has unrestricted DELETE on the
  Better Auth identity tables (`users`, `sessions`, `accounts`, `two_factors`, `verifications`);
  no exploit path found, but there's no DB-level backstop if application code ever mishandles a
  user id." I'm not filing it myself since it spans tables outside this card's diff and the finding
  needs an owner assignment through the tech lead.
- Both of the author's scope additions (MFA needs a verified email; a completed reset verifies the
  email) close real account-hijacking angles and are approved — see the primary reviewer's file for
  the detailed reasoning, which I independently agree with.
