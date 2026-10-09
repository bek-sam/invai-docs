# Review of T-29-2 (round 1), co-review for risk flag `auth`

- Reviewer: security-reviewer on opus · Author: backend-foundation on opus
- Verdict: **approve** (invai-backend@384ef6f, decision 0028 at invai-docs@fd3caf7, now accepted)

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm vitest run src/lib/account-lockout-notify.test.ts src/lib/account-security.test.ts src/lib/mfa.test.ts src/modules/tenancy src/db/rls-coverage.test.ts src/api/authz.test.ts --reporter=dot` | 13 files, 100 tests passed, exit 0 |
| Same notify test against `git archive 384ef6f^` | FAIL (no `errorKind` and unguarded `void notifyLocked`), so it fails without the change |
| New `src/modules/tenancy/security.test.ts` "T-29-2 two-step sample rule" (2 tests) | 11/11 passed; biome clean; typecheck clean for my file |
| Own API on :3124 (REDIS db 11), dev DB read-only: sign in, `me.get` | owner@ and admin@ `required: true`, deadline 2026-10-16; office@ `required: false`; owner `orders.list` 200 (before the deadline). PID 48836 stopped |

## Threat model
- **Can an owner/admin make a real shop look like a sample?** No. `demoOwnerUserId` is written only by `createDemoCompany` (a new row with the caller's id) and is cleared by retire and purge. `demoRetiredAt` is written only by `retireDemoCompany`, whose target always comes from `findDemoCompany(userId)` and never from input. `me.updateOrg` builds an explicit settings patch and its contract input strips unknown keys. `today.dismissChecklist` writes only `onboardingDismissedAt`. A new regression test calls `me.updateOrg` with smuggled `demoOwnerUserId`/`demoRetiredAt`/`settings`, then `dismissChecklist`: the row is unchanged and the owner is still required.
- **Wider or narrower?** Strictly narrower. Every sample org has `demo = true` (insert sets both), so every org that was exempt before is still exempt. Desert Bloom (`demo` with no sample marker) is now required. The rule is `some()` over memberships, so joining a sample org never removes a real owner's requirement (test added). `tenancy.demo.*` is not in `MFA_EXEMPT_PROCEDURES`.
- **unhandledRejection log-and-continue.** Before this change Node 24 crashed and printed the same message and stack to stderr, so no new data reaches the logs; the S-29 drizzle-params gap is unchanged, not widened. Both handlers are registered after the top-level startup awaits, so a failed boot still exits. `uncaughtException` keeps crashing. The stray promises are fire-and-forget side effects (lock email, `onJobFailed`), whose failure leaves no half-written transaction. Accepted.
- **Lock email failure path.** The call is still not awaited, so the response time and body are the same for existing and unknown emails (401 `INVALID_EMAIL_OR_PASSWORD`). `errorKind` logs only the error class and the Postgres code; the test checks the email never appears in the captured logs.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | live `me.get` above; isSampleRow live/retired/seeded cases in account-security.test |
| 2 | yes | vendor and office cases in account-security.test; office@ live `required: false` |
| 3 | yes | notify test (fails on the old code), handlers in server.ts:56 and worker/index.ts:99 |
| 4 | yes | reactivation-once test plus S-58 tests green |
| 5 | n/a here | E2E runs at the gate; the report states reseed or enroll |

## Blocking findings
none. No new S-id.

## Optional notes (not blocking)
- `sendAuthMail` logs `String(err)` on SMTP failure, which can contain the recipient's address. This belongs to the S-29 class; backend-foundation follow-up (the author flagged it too).
- Alert on `"unhandled rejection"` when alerts exist (platform-sre). A fail-open path needs a log and an alert (research 12 A10).
- Residual (existing design, decision 0025): a user could CSV-import real orders into their own sample workspace, which has no two-step requirement. Reassess before the SP-API application.
- Not this card: HEAD 2872c59 (T-29-4 r2) fails `pnpm typecheck` at `src/modules/channels/webhook-auto-import.test.ts:205` (TS2322, nullable row). Tech lead to route this to the T-29-4 owner before the gate.
