# Review of T-1-4 (round 1)

- Reviewer: reviewer on Opus
- Author: backend-foundation on Opus 5.5
- Verdict: **changes-required**

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend show 55ca092 --stat` | 6 files, matches owned paths (`auth.ts`, `modules/tenancy/invites.ts` new, `modules/tenancy/service.ts`, `modules/tenancy/invites.test.ts`, `modules/vendors/service.ts`, `modules/vendors/invite.test.ts`) |
| `git -C invai-web show d6336e0 --stat` | 5 files, matches owned paths (`accept-invite.$invitationId.tsx`, `settings/team.tsx`, `i18n/{en,es}.ts`, `scripts/i18n-es.json`) |
| Worktree `invai-backend@55ca092`: `pnpm typecheck && pnpm lint && pnpm test` (`TEST_DATABASE_URL=postgres://invai_app:invai@localhost:5432/invai_test_r14`, `TEST_MIGRATION_DATABASE_URL=postgres://invai:invai@localhost:5432/invai_test_r14`) | tsc clean; biome "Checked 195 files… No fixes applied."; vitest "Test Files 38 passed (38) / Tests 223 passed (223)" |
| Worktree `invai-web@d6336e0`: `pnpm typecheck && pnpm lint && pnpm test && pnpm build` | tsc clean; biome "Checked 97 files… No fixes applied."; vitest "Test Files 5 passed (5) / Tests 23 passed (23)"; `✓ built in 1.32s` |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend 55ca092^` | exit 1 (hits); read every hit below |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web d6336e0^` | exit 0, no hits |
| Live: API on `PORT=3194` against a throwaway copy of dev DB (`createdb -T invai invai_r14_copy`), web `vite --port 5194 VITE_API_URL=http://localhost:3194` | see below and the acceptance table |
| `POST /api/auth/sign-in/email` for `owner@`, `admin@`, `office@`, `presser@desertbloom.test`, `vendor@suncitydtf.test` / `demo1234!` | all `200` |
| `POST /api/v1/team/invite` (owner→presser), Mailpit search, `GET /api/auth/invite-preview`, sign-up + `POST /api/auth/organization/accept-invitation`, `GET /api/v1/me` | invitation created, email delivered, previewed publicly, accepted, `role: "presser"`, `status: "active"` |
| `POST /api/v1/team/invite` role `owner` as `admin@`; as newly-accepted `presser` | both `403 Forbidden` |
| `POST /api/auth/organization/accept-invitation` with a session signed in as a different email | `403 { code: "YOU_ARE_NOT_THE_RECIPIENT_OF_THE_INVITATION" }` |
| 35× `GET /api/auth/invite-preview?id=<valid>` in <1 min | `200` ×30, then `429` — matches the documented 30/min limit |
| `POST /api/v1/vendors/invite`, accept as a new vendor user | vendor org created, invitation link (not `/vendor/accept?token=`), member `role: vendor`, `status: active` |
| Cleanup | dropped `invai_r14_copy` and `invai_test_r14`, removed both worktrees, killed both dev processes, ports 3194/5194 free |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | Live invite created a real `invitations` row (7-day expiry), no user row until signup; email delivered via Mailpit with `/accept-invite/<id>`; `invites.test.ts` covers en/es by inviter locale. |
| 2 | Yes | Live: new email → signup → active `presser` member. Existing user: unit test "an existing user just signs in and accepts". Invalid/expired/used/wrong-email: unit tests + author's screenshots (`state-used.png`, `state-expired.png`, `state-invalid.png`, `state-wrong-account*.png`, `state-bad-password.png`), all read and correct. |
| 3 | Yes | Live vendor invite: no `/vendor/accept?token=` anywhere in the email (grepped the Mailpit text), same `/accept-invite/<id>` link, 14-day expiry, accepted vendor is `role: vendor / active`, screenshots `vendor2-*` show `/vendor` → Shops. |
| 4 | Yes | Live: all 6 seed staff logins + the seed vendor login return 200. |
| 5 | Yes | `team.tsx` diff: toast fires only in `onSuccess`, using the email the API returned; `onError` maps `UPSTREAM_FAILED`/`CONFLICT` to translated copy. Unit tests cover both staff and vendor mail-failure paths (rollback verified: "a failed email fails the invite and saves nothing"). |

## Blocking findings
1. **`invai-backend/src/modules/tenancy/service.ts` `inviteUser` (the `sendInviteEmail(...)` call before `return invitedUser(...)`) and `invai-backend/src/modules/vendors/service.ts` `inviteVendor` (the `sendInviteEmail`/`sendMail` call in the try block) — an outbound SMTP call runs while the request's tenant DB transaction is still open.** Both are invoked as `withTenant(companyId, (tx) => svc.inviteUser(tx, ...))` / `...inviteVendor(tx, ...)` (`router.ts:46`, `router.ts:13`), and `withTenant` is a real Postgres transaction (`db/client.ts` `scoped()`/`database.transaction`). By the time `sendInviteEmail` runs in `inviteUser`, the transaction already holds an uncommitted `invitations` insert and (on a re-invite) a `members` delete. `idempotent-side-effect` (a skill loaded by this very role and by security-reviewer) states plainly: "MUST NOT call a money-costing or buyer-emailing API inside a DB transaction or while holding a row lock," and the codebase already has the tool for this — `afterCommit(tx, fn)` — used 30+ times elsewhere, including twice in `vendors/service.ts` itself (line 605) for a different side effect in this same module. The app's Postgres pool is capped at 10 connections (`db/client.ts:8`, `max: 10`). A slow or hanging SMTP relay (a real risk once a live SMTP provider replaces Mailpit) holds a transaction, a connection and a row lock open for the whole round trip; a handful of concurrent invites during a slow SMTP window can exhaust the shared pool and stall every tenant's requests, not just the inviting company's. Failure scenario: office at shop A invites three teammates while the mail relay is timing out; three of the ten pool connections wedge for the SMTP timeout window, and shop B's `orders.list` and everything else app-wide starts queuing or timing out.
   - This is a real design tension, not an oversight the author missed: the card requires "the web shows 'Invitation sent' only when the backend actually sent it" (AC 5), and doing the send after commit would break that atomicity. The fix doesn't have to give that up — e.g. call `sendMail` with its own short timeout *before* opening the tenant transaction (attempt the send, then write the invitation row only on success), or write the row in a first short transaction and compensate with an update on failure (the vendor path already does exactly this compensating-delete pattern for the org row). Either avoids holding the transaction open across the network call.

## Checks
- [x] Only owned paths changed (`git diff --stat`) — confirmed above.
- [x] Nothing outside scope — no contract changes, no migrations, no unrelated files.
- [x] Tests exercise the behavior, and none were weakened — `scan-test-weakening.sh` hit only the two `vi.mock(".../mailer")` calls (needed so unit tests don't hit real SMTP; the mock exposes a `fail` toggle and is used to test both the success and failure/rollback paths — not a mock of the unit under test) and one `toBeTruthy()` (on a generated invitation id, not a weakened assertion). 0 assertions removed, 59 added, confirmed by reading the diff.
- [x] Tenancy (`withTenant`, RLS on new tables) — `team.invite`/`vendors.invite` run under `withTenant`; the one new `withSystem` read (`invitePreview`'s lookup of the inviting shop's name) has a reason comment and returns only a name, pre-session; cross-tenant `changeRole` on an invitation from another company returns `NOT_FOUND` (tested and matches the "never FORBIDDEN" rule). No new tables, so nothing new to RLS-check.
- [x] Idempotency, money in cents, en/es text — no money involved; en/es strings read correctly in both languages (see product-designer review); idempotency flagged above (mail send placement), everything else (re-invite replaces pending invite, stale `invited` member row cleanup) behaves correctly on replay.
- [x] Decisions recorded where needed — author's report documents the no-email-verification-on-accept choice, locale source, and the i18n-by-hand decision, all reasonably.

## Optional notes (not blocking)
- `team.invite`'s order of checks (`assertRoleFitsOrg` → `assertCanManage` → `if (!ctx.userId)`) puts the `ctx.userId` guard last; harmless today since every tenant procedure has a userId, but consider checking auth context first for clarity.
- `vendors.tsx` toast (not owned by this card) will show raw English `Invite email failed` on the failure path the author didn't touch — already logged as a follow-up in the report for web-engineer.
