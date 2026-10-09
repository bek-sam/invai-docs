# Review of T-28-2 (round 1)

- Reviewer: reviewer on fable
- Author: backend-foundation on opus (backend 074c922 + e42b38d, docs d57c482; contract dc62328)
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` / `pnpm lint` (invai-backend) | both exit 0 (biome: 507 files, no fixes) |
| `pnpm exec vitest run src/lib/account-security.test.ts src/api src/modules/tenancy --reporter=dot` | 23 files, 156 passed, exit 0 |
| `pnpm exec vitest run` (full suite, clean tree) | 196 files passed, 1 failed, 1665 tests passed: only `rls-coverage` "tables without RLS" -> `password_history`, `sign_in_failures` (same as the report) |
| `scan-test-weakening.sh invai-backend d5e8fd1` | hits: `vi.mock` of the mailer (a dependency, fine); the other two hits are T-28-3 files |
| `pg_attribute` on invai_test: `users.mfa_grace_starts_at` | `atthasmissing = t`, missing value = migration time: catalog fast path, no table rewrite; `invai_app` has CRUD on both new tables |
| Scratch probe test (git-archive copy of HEAD, 5 tests, deleted after) | 5 passed: change-password P->S->T then T->S = 400 `PASSWORD_REUSED` with 3 history rows; `auth.api.signUpEmail` (seed path) writes 1 row; known vs unknown email give the identical 11-status sequence (10x401, 423) and identical 423 body keys/message; locked right password adds no `sessions` row and sets no cookie; vendor user backdated 90 d -> `required=false`; blocked owner: `orders.list`/`billing.checkout` -> `MFA_REQUIRED`, `floor.login` (station mode) -> `UNAUTHORIZED`; demotion owner->office leaves `mfa_grace_starts_at` untouched, office->admin restarts it |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1, 2, 4, 5 | yes | author tests + probe: 10x401 then 423 with `retryAfterSec`/`Retry-After`, no session row; identical sequence and 423 body for a never-registered email (both thrown in the before-hook, before any password work); `clearAfterSuccess` keeps a live lock; `onPasswordReset` -> `clearLock`; one `INSERT … ON CONFLICT … RETURNING` keyed by `hmacHex(BETTER_AUTH_SECRET, "sign-in-lock:"+normalized)` (`account-lockout.ts:36`); 20-parallel and N-concurrent tests ran green; decision 0008 bucket untouched |
| 3 | yes | `accountLockedEmail` en/es with minutes + `/forgot-password`; `notified_at` claim + `crossed` guard; `log.warn("sign-in locked", { userId })` only |
| 6, 7 | yes | change (`updateAccount` -> `account.update.after`), reset (`onPasswordReset`, since BA's reset uses `updateMany`), sign-up/invite/seed (`account.create.after`, probe) all record; `isReusedPassword` uses `ctx.context.password.verify`; cap 10, FK cascade (test) |
| 8, 9 | yes | `orpc.ts:131-139`: after the permission check, before `EMAIL_NOT_VERIFIED`, `sessionKind === "user"`, mode user/floor only, exempt set exactly `{me.get, me.switchOrg}`; floor PIN test + probe (station mode never reaches the guard); SSE/`/l` are Hono routes outside oRPC and 0025 says so |
| 10, 11, 12 | yes | author tests ran green: in grace `orders.list` OK and `me.get.mfa = {true,false,deadline}`, office user `{false,false,null}`, promoted office user gets a fresh grace, sample-only owner never required, `/two-factor/disable` -> 403 `MFA_DISABLE_NOT_ALLOWED`; probe adds vendor-excluded and demotion-keeps-start |
| 13 | yes | fixtures/seed insert users with the column default; seed unchanged; full suite green apart from the owned-elsewhere `GLOBAL_TABLES` row. Note: the seeded Desert Bloom/Sun City companies are `demo: true` (seed/index.ts:116,130), so seeded logins are never required, not merely "inside grace" |
| 14 | yes | `decisions/0025` has every value, the exempt list, the non-oRPC paths and the lock-anyone trade-off; `v1-review.md` untouched (security-reviewer's) |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat`): yes, plus one helper row in `src/modules/README.md` (not on the card; backend-foundation has edited that table on T-2-3/T-19-4/T-20-5/T-22-2; not blocking)
- [x] Nothing outside scope
- [x] Tests exercise the behavior through the real HTTP surface, none weakened; the new file fails trivially on base (new modules), so I used the scratch probes above instead of step 8
- [x] Tenancy: both new tables are rightly global (pre-tenant sign-in keyed by HMAC; per-user hashes like `accounts`), reached only from `src/auth.ts` hooks over `db`, never from a procedure; adding them to `GLOBAL_TABLES` is correct. Idempotency: one atomic upsert, `notified_at` claim. en/es strings present. No PII in logs.
- [x] Decision 0025 recorded (proposed; security-reviewer accepts)

## Optional notes (not blocking)
- `src/auth.ts:388` `void notifyLocked(email)` has no `.catch`; `src/` registers no `unhandledRejection` handler, so a DB error inside `notifyLocked` (after `recordFailure` succeeded) would crash the API process. Suggest `.catch((err) => log.error(...))`.
- `setMemberStatus` reactivation restarts the grace (probe: true): deactivate+reactivate by a second admin refreshes a blocked admin's 7 days, same class as re-invite, which the card allows. Worth a line in 0025. The Notion test-guide row for MFA needs a freshly signed-up shop, since seeded logins are sample-workspace owners.
