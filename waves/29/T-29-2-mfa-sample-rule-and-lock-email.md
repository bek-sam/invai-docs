# T-29-2: Two-step rule uses `isSampleWorkspace`; the lock email can't crash the API

| Field | Value |
|---|---|
| Wave | 29 |
| Scope ref | `always-in-scope: bug / security` (B-299 wave 28 rule bug, B-297 reviewer note; decision 0025) |
| Spec | none; source: backlog B-299, B-297; `waves/28/reviews/T-28-2-reviewer-r1.md` notes 1–2; decision 0025 |
| Owner | backend-foundation |
| Reviewer | reviewer (fable) |
| Co-reviewers | security-reviewer (opus) |
| Risk flags | auth |
| Model | opus |

## Owned paths (edit)
- `invai-backend/src/lib/mfa.ts` and its tests
- `invai-backend/src/auth.ts` (the `notifyLocked` call), `invai-backend/src/lib/account-lockout.ts` (where `notifyLocked` lives) and its tests, `invai-backend/src/lib/account-security.test.ts` (the `MfaMembership` cases ~:346-352)
- `invai-backend/src/api/server.ts`, `invai-backend/src/worker/index.ts` (process-level `unhandledRejection` logging)
- `invai-backend/src/modules/tenancy/**` except `security.test.ts` (only if a caller of the MFA helpers needs the new field)
- `invai-backend/src/db/seed*` only if the plan review asks the seed to set something
- `invai-docs/decisions/0028-mfa-sample-rule.md` (new, type security, status proposed; security-reviewer accepts) plus its index row in `invai-docs/decisions/README.md`. Decision 0025's body stays unchanged

## Read-only paths
- `invai-backend/src/modules/privacy/**`, `orders/**`, `personalization/**` (T-29-1 works there), `invai-contracts/**`, `invai-web/**`

## Depends on
- Decision 0029 (product, accepted 2026-10-09): the seeded shop follows the real two-step rule; the only exemption is `isSampleRow`; no seed bypass. Decision 0028 links 0029.

## Interfaces promised
- `isMfaRequired(memberships)` keeps its signature; `MfaMembership` replaces `demo: boolean` with `sample: boolean` computed by `isSampleRow` (`modules/tenancy/demo-flag.ts`) from `demoOwnerUserId` and `settings.demoRetiredAt`, selected inside the `activeMemberships` join (one query, not the `isSampleWorkspace` cache per org).

## Acceptance criteria
1. Given the seeded Desert Bloom (`demo = true`, not a sample workspace), when `owner@` or `admin@` signs in, then `me.get` returns `mfa.required = true` with a deadline 7 days after the grace start (fresh seed: about now + 7 days), and the API refuses non-exempt calls with `MFA_REQUIRED` only after that deadline. A user's own sample workspace (`tenancy.demo`, `demoOwnerUserId` set) and a retired one still never make anyone required.
2. Vendors stay excluded (vendor org type); office/designer/presser roles stay excluded.
3. **B-297.** A failure inside the lock email (DB error, SMTP error, thrown in `notifyLocked`) is caught and logged with no buyer or user email in the log, and never becomes an unhandled rejection. The API and worker processes log any other `unhandledRejection` with `logger` and keep running (decide and record: log-and-continue for rejections; `uncaughtException` behavior unchanged). A test forces `notifyLocked` to reject and shows the sign-in answer is unchanged and the process handler is not hit.
4. **Grace restart on reactivation** (B-297 note 2): state in decision 0028 that reactivation through `setMemberStatus` counts as the one allowed restart under the S-58 rule (no code change unless the rule doesn't hold; prove it with the existing S-58 tests passing).
5. The E2E and API golden paths still pass on a fresh seed, because the deadline is 7 days out; say in the report whether any test, seed step or the gate needs the seeded owner to be enrolled, and how the owner sees the banner in the browser. `users.mfa_grace_starts_at` defaults to user creation (`db/schema/tenancy.ts:55`) and nothing restarts grace when the rule flips, so on any DB seeded more than 7 days ago `owner@` and `admin@` get MFA_REQUIRED at once. The report and the feature-test-guide row say: reseed or enroll. (The dev DB was seeded 2026-10-09, so the live check is safe.)

## Verification
- `pnpm typecheck && pnpm lint && pnpm test` in `invai-backend`.
- Exercise for real on your own API (`PORT=3122`, `REDIS_URL=redis://localhost:6379/13`) against the shared dev DB read-only (no reset): sign in as `owner@desertbloom.test`, call `me.get`, show `mfa.required: true` and the deadline; sign in as `office@`, show `required: false`. Then with a test-time clock or a scratch DB, show a past-deadline owner gets `MFA_REQUIRED` on `orders.list` and not on `me.get`.
- Record every PID you start and stop it.

## Out of scope
- Any web change (the banner already exists, T-28-4).
- Changing lockout values, grace length or exempt procedures.
- B-294 web notes.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
