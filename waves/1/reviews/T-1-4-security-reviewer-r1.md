# Review of T-1-4 (round 1)

- Reviewer: security-reviewer on Opus
- Author: backend-foundation on Opus 5.5
- Verdict: **changes-required**

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend show 55ca092` (full diff, `src/auth.ts`, `src/modules/tenancy/invites.ts`, `src/modules/tenancy/service.ts`, `src/modules/vendors/service.ts`) | read in full |
| Threat-model entry points from `invai-contracts/src/contract/tenancy.ts`, `vendors.ts` | `team.invite`/`changeRole`/`deactivate` all `proc("team.manage")`; `vendors.invite` `proc("vendors.manage")`; new `GET /api/auth/invite-preview` is unauthenticated by design (a Better Auth plugin endpoint, not an oRPC procedure) |
| Worktree `invai-backend@55ca092`: `pnpm test` (`TEST_DATABASE_URL=…/invai_test_r14`) | 38 files / 223 tests passed, includes the permission-matrix and RLS-coverage suites (unchanged by this diff) |
| Live: API on `PORT=3194` against a throwaway copy of the dev DB (`createdb -T invai invai_r14_copy`) | see below |
| `GET /api/auth/invite-preview?id=<pending>` | `{status:"pending", email, role, organizationName, organizationType, invitedBy, hasAccount}` — full detail, but only reachable by knowing the id (a random UUID minted server-side, `advanced.database.generateId: "uuid"`, sent only in the email) |
| `GET /api/auth/invite-preview?id=<random uuid>` / `id=not-a-uuid` | both `{status:"not_found"}` — no email/role/org leaked for a guess |
| `GET /api/auth/invite-preview?id=<already-accepted id>` | `{status:"used"}` only (confirmed pre-rate-limit; also covered by `invites.test.ts` "expired, canceled and unknown links show their status only") |
| 35× `GET /api/auth/invite-preview` for one id inside a minute | 30× `200`, then `429` — the `customRules["/invite-preview"] = {window:60, max:30}` in `auth.ts` is live |
| Sign up with the invited email, then `POST /organization/accept-invitation` | succeeds, member becomes `active` with the invited role |
| `POST /organization/accept-invitation` with a session signed in as a **different** email, same invitation id | `403 { code: "YOU_ARE_NOT_THE_RECIPIENT_OF_THE_INVITATION" }` — Better Auth checks `invitation.email.toLowerCase() === session.user.email.toLowerCase()` server-side (`node_modules/better-auth/dist/plugins/organization/routes/crud-invites.mjs`), not client-trusted |
| `POST /api/v1/team/invite {role:"owner"}` as `admin@desertbloom.test` (non-owner) | `403 Forbidden` (`assertCanManage`, unchanged by this diff) |
| `POST /api/v1/team/invite` as the newly-accepted `presser` | `403 Forbidden` (`presser` has no `team.manage` in `invai-contracts/src/roles.ts`) |
| `changeRole` on another company's pending invitation (`invites.test.ts`) | `NOT_FOUND`, never `FORBIDDEN` |
| Vendor accept flow live | vendor org, invitation, active `vendor` member; no `/vendor/accept?token=` link anywhere in the sent email (grepped Mailpit text) |
| Cleanup | dropped `invai_r14_copy`/`invai_test_r14`, removed worktrees, stopped both dev processes |

## Threat model (T-1-4)
- **Entry points:** `POST /team/invite`, `POST /team/{userId}/role`, `POST /team/{userId}/deactivate` (all `team.manage`, session auth); `POST /vendors/invite` (`vendors.manage`, session auth); `GET /api/auth/invite-preview` (no auth — a Better Auth plugin endpoint, public by design); `POST /organization/accept-invitation` (Better Auth core, session auth, not gated by InvAI's own permission system).
- **Tenant comes from:** the session's active org for the `team.*`/`vendors.*` procedures (standard `withTenant`). `invite-preview` and `accept-invitation` take the tenant from the invitation row itself, keyed by an unguessable id — correct, since there is no session yet.
- **Data touched, PII:** invited email address, name, role, company name; for a vendor invite, the inviting shop's name (`invitedBy`, read cross-tenant via `withSystem`, justified in a comment, returns only a name).
- **Worst outcome considered:** an attacker who can read or guess an invitation id learns who was invited to which company as what role, and — because sign-up never verifies email ownership anywhere in this app (`emailAndPassword` has no `requireEmailVerification`, pre-existing, not introduced by this card) — could sign up with the target's email and accept the invite under an account they control before the real recipient does. **This is a pre-existing, app-wide condition** (any sign-up, invited or not, is unverified), correctly called out by the author as a decision needing confirmation. I confirm the call: `requireEmailVerificationOnInvitation: false` only makes explicit what Better Auth already defaulted to, and Better Auth's own accept-invitation still hard-checks the signed-in email against the invitation email server-side, so this card does not add a new bypass. The risk is that the invitation id itself must stay a real secret (delivered by email only, adequate entropy, rate-limited) — verified above. I recommend a follow-up finding in `invai-docs/security/v1-review.md` (owner: security-reviewer/platform) to track "no email verification at sign-up" as a standing accepted risk ahead of the Amazon DPP review, not something this card needs to fix.
- **Enumeration / disclosure via `invite-preview`:** verified minimal for anything not pending (status only), full detail gated by a 122-bit random id, 30/min/IP rate limit live. No finding.
- **Role escalation:** verified blocked both ways (non-owner can't grant/change to owner; roles without `team.manage` get 403 before role logic even runs; `assertRoleFitsOrg` still stops a shop granting `vendor` or a vendor org granting anything else). No finding — this logic is unchanged by the diff, only reused.
- **Tenant isolation:** verified — `team.invite`/`vendors.invite` run inside `withTenant`; the only new `withSystem` use is documented, minimal (a name, not vendor_connection details) and needed because a fresh vendor org has no session; cross-tenant access to a pending invitation returns `NOT_FOUND`, never `FORBIDDEN`, matching the rule that a response must never confirm another tenant's row exists.

## Blocking findings
1. **Mail sent while holding the tenant transaction open — co-signed with `reviewer`'s finding 1** (`invai-backend/src/modules/tenancy/service.ts` `inviteUser`, `invai-backend/src/modules/vendors/service.ts` `inviteVendor`). This isn't a cross-tenant leak or an auth bypass (not High), but it is a shared-resource integrity/availability issue squarely in this role's remit (`idempotent-side-effect`, a skill this role loads, states "MUST NOT call a money-costing or buyer-emailing API inside a DB transaction or while holding a row lock"): with the app's Postgres pool capped at 10 connections, a slow SMTP relay during a burst of invites can wedge enough connections to degrade every tenant sharing the pool, not just the inviting company. Severity: Medium (unbounded-abuse/integrity class, per this role's rubric) — a slow or malicious-adjacent SMTP endpoint (or simply a real provider having a bad minute) becomes a cross-tenant availability lever. Same fix suggestion as the primary review: attempt the send (with its own short timeout) before or outside the DB transaction, and write the invitation row conditionally on that result, mirroring the compensating-delete pattern `inviteVendor` already uses for the org row on a failed vendor invite.

## Checks
- [x] Only owned paths changed.
- [x] Nothing outside scope.
- [x] Tests exercise the behavior; scan-test-weakening hits are legitimate mailer mocks (needed to test both the success and the mail-failure/rollback paths without real SMTP), not weakening.
- [x] Tenancy (`withTenant`, RLS on new tables) — no new tables; the one `withSystem` read is justified and minimal; cross-tenant reads return `NOT_FOUND`.
- [x] Idempotency — flagged above (mail-in-transaction). Re-invite/cleanup of stale rows is safe to repeat (tested).
- [x] Decisions recorded — the no-verified-email decision is documented in the author's report; I've recorded my confirmation and a recommended follow-up above rather than a new blocking finding.

## Optional notes (not blocking)
- Recommend a `invai-docs/security/v1-review.md` entry (Low, pre-existing, owner TBD by tech lead) tracking "sign-up has no email verification app-wide" ahead of the Amazon DPP application, since invites now make that gap slightly more visible (an unverified account can claim to be someone else's invited teammate). Not something T-1-4 should fix.
- `UPSTREAM_FAILED` isn't declared in the oRPC contract, so it logs as an "unhandled procedure error" even though the client gets the right code — cosmetic log noise, already noted by the author as a follow-up.
