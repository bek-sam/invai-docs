# Review of T-1-4 (round 2)

- Reviewer: security-reviewer on Opus
- Author: backend-foundation on Opus 5.5
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend show 659f1bc` (full diff) | read in full: `tenancy/{invites,invites.test,router,service}.ts`, `vendors/{invite.test,router,service}.ts` |
| Clean worktree at `659f1bc`, `node_modules` symlinked, no `pnpm install`, own test DB `invai_test_r14b` | as instructed |
| `./node_modules/.bin/vitest run --passWithNoTests` | `Test Files 39 passed (39) / Tests 231 passed (231)` — includes the permission-matrix and RLS-coverage suites, unaffected by this diff |
| Reintroduced the round-1 bug (send inside `withTenant`) in `inviteTeammate`, reran `invites.test.ts` | both new pool/transaction tests fail immediately with the exact expected mismatch (`busy: 1` vs `busy: 0`); reverted, clean diff, tests green again — this is the finding's own regression test proven to bite |
| Live: API on `PORT=3195` against a throwaway copy of the dev DB | see below |
| Re-invite under a simulated outage (`SMTP_URL=smtp://localhost:1`) of an already-invited email, attempting a role change (`office` → `presser`) | `502 UPSTREAM_FAILED`; DB shows only the original invitation, unchanged role and status; `invite-preview` on it still returns `{status:"pending", role:"office", …}` |
| Fresh staff invite and fresh vendor invite under the same outage | both `502 UPSTREAM_FAILED`; zero rows left in `invitations`, `companies` (vendor org), `vendor_connections` for those identities |
| `pg_stat_activity` on the throwaway DB after all of the above | no `idle in transaction` rows at any point |
| Cleanup | dropped both throwaway databases, removed the worktree, API stopped, port 3195 free |

## Round 1 finding, re-verified
Round 1 blocked on `inviteUser`/`inviteVendor` sending SMTP while the tenant transaction was open (pool exhaustion / cross-tenant availability risk, `idempotent-side-effect`'s MUST NOT rule). This is fixed:
- `team.invite` is now `inviteTeammate`: a short `withTenant` commits the pending invitation, the send happens with **no transaction open**, then a second short `withTenant` either finishes (replace older invitations, audit) or a third short `withTenant` deletes the just-created invitation on failure.
- `vendors.invite`/`inviteVendor`: same shape — a short `withSystem` commits the new vendor org + invitation (only when needed), the send happens outside any transaction, then a short `withTenant` finishes or the vendor org is deleted on failure (`removeNewOrg`, correctly gated so an *existing* vendor org is never deleted).
- Proven, not just asserted: the mocked `sendMail` in both test files samples `appPool.totalCount - appPool.idleCount + systemPool.totalCount - systemPool.idleCount` at the moment it's called. Both the success and the failure path assert `busy: 0`. I reintroduced the old bug and watched these exact assertions fail, then confirmed they pass again on the real commit. Live `pg_stat_activity` never showed `idle in transaction` across four invite attempts (two failures, one re-invite-under-outage, one vendor failure). I consider this finding closed.

## The two items I was specifically asked to check
- **Compensation on failure.** Correct and minimal: only what this call itself created is undone (the new invitation; the new vendor org only when this call made one). No orphaned rows in any of the four live failure tests above. The vendor path additionally re-checks for a duplicate connection inside the final transaction before inserting, and compensates if it loses that race — a real idempotency guard against a duplicated vendor org, not just a comment.
- **A failed re-invite leaves the old link valid.** Confirmed true, live. This is not a new privilege-escalation vector: the surviving invitation is one that already passed `assertRoleFitsOrg`/`assertCanManage` when it was first created, so nothing ungranted becomes reachable — the worst case is an owner's attempted role *correction* silently not taking effect (an accepted, disclosed tradeoff, and arguably safer than round 1's alternative, where the same failure mode existed too: the single-transaction design meant a thrown error from `sendInviteEmail` rolled back the whole transaction, including the `cancelPendingInvitations` update, so the old invitation survived a failed re-invite in round 1 as well — this card doesn't newly introduce the behavior, it just documents and tests it explicitly for the first time). No finding.

## Threat re-check (round 2 diff only)
- **Tenancy:** every transaction in both flows is still `withTenant`/`withSystem` scoped exactly as before; no new tenant-unscoped read or write was introduced by splitting the flow into steps.
- **Idempotency / replay:** the failure path is safe to retry (compensating delete removes exactly what was added); the success path is unchanged from round 1 (already reviewed: replaces the pending invitation, cleans up stale pre-Better-Auth `invited` member rows). One latent gap, **not introduced by this round**: no unique constraint stops two concurrent identical `team.invite` calls from both passing the initial checks and each sending an email before the "keep newest" reconciliation runs — worst case is a duplicate email, not a duplicate membership or a security issue (each invitation still has its own id and both would 200; the later "finish" step cancels the other). Recording as a non-blocking follow-up, owner TBD by tech lead.
- **PII / auth surface:** unchanged by this diff — no new endpoint, no new field returned, no change to `invite-preview` or `accept-invitation`.
- **Timeout / late delivery:** `deliverInviteMail`'s 15 s `Promise.race` does not cancel the underlying SMTP call, so a very slow send can still deliver mail after the invitation was already compensated away. This is a reliability/UX gap (a dead link), not a security one — it cannot be used to bypass anything, since accepting still requires the invitation id to resolve to a live, pending row. Disclosed by the author as a known gap. Non-blocking. If a real SMTP provider (not Mailpit) is ever wired up with materially slower typical latency, worth revisiting `mailer.ts` to support real cancellation (owned by T-1-1/platform, out of scope here).

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (7 files, `modules/tenancy/**`, `modules/vendors/**`); web untouched.
- [x] Nothing outside scope.
- [x] Tests exercise the behavior, none weakened; the specific tests this round exist to prove are independently confirmed to fail when the bug is reintroduced.
- [x] Tenancy (`withTenant`/`withSystem` scoping intact), idempotency (compensation verified live four ways), no PII/auth surface change.
- [x] Decisions recorded — round 2 report section documents the design and both known gaps.

## Optional notes (not blocking)
- Same as `reviewer`'s: a partial unique index on `invitations (organization_id, lower(email))` for `status = 'pending'` would close the double-submit duplicate-email gap outright; recommend a small follow-up card rather than reworking this one.
