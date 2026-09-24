# Report: T-1-4 Team and vendor invites work end to end
Author: backend-foundation on Opus 5.5

```
Card: T-1-4  Owner: backend-foundation  Scope ref: product/scope.md#mvp-in items 9, 14 (bug; B-51, B-52)
Owned (edit): invai-backend/src/auth.ts, src/modules/tenancy/**, src/modules/vendors/** (invite code only),
  invai-web/src/routes/accept-invite*, team-invite message in src/routes/_app/settings/team.tsx,
  invai-web/src/i18n/{en,es}.ts (new keys only), tests next to these
Read-only: integrations/vendors/mailer.ts (called sendMail), api/context.ts
Risk flags → co-reviewers: auth, pii → security-reviewer; ui → product-designer
```

## Commits (on main, not pushed)
- invai-backend `55ca092`: Team and vendor invites work end to end (T-1-4)
- invai-web `d6336e0`: Accept-invite page handles every invite state (T-1-4)

Both were committed with `git commit -- <exact paths>`. `git show --stat HEAD` lists only my files. Another card's staged `src/db/seed/trademarks.ts` deletion is still staged and untouched.

## Built
- **Staff invites use real Better Auth invitations.** `team.invite` inserts an `invitations` row (role, `pending`, 7-day `expires_at`, `inviter_id`). It no longer creates a user row or an `invited` member. Then it emails `WEB_ORIGIN/accept-invite/<id>`. (`invai-backend/src/modules/tenancy/service.ts`, `src/modules/tenancy/invites.ts`)
- **Email text.** One shared builder writes the invite in English or Spanish, as plain text plus HTML. Names are HTML-escaped, and the role name and expiry date are included. `sendMail` comes from `integrations/vendors/mailer.ts`, which I didn't edit. (`invites.ts`: `inviteEmail`, `sendInviteEmail`)
- **A failed email fails the invite.** `sendInviteEmail` throws `UPSTREAM_FAILED` ("Invite email failed"), so the tenant transaction rolls back and no invitation is saved.
- **Re-invites and old data.**
  - Inviting the same email again cancels the pending invitation and sends a new one.
  - Inviting someone who is already an active or deactivated member returns `CONFLICT`.
  - An old `invited` member row left by the previous flow is removed before the new invitation is created.
- **Pending invitations in the team list.** They appear at the top of the first page of `team.list` as `status: "invited"`, with the invitation id as `id` and the email as the name. This keeps the `User` contract unchanged.
  - `changeRole` on one of these rows changes the invitation's role.
  - `deactivate` cancels the invitation, so its link stops working.
  - `setPin` returns `BAD_REQUEST` ("Set a PIN after they accept the invite").
  - The onboarding "staff invited" check counts pending invitations.
- **Vendor invites.**
  - A vendor that isn't registered yet gets the same invitation (14 days), the same `/accept-invite/<id>` link and the same email builder. The `/vendor/accept?token=` link is gone, and `inviteToken` is no longer written.
  - The email is sent before the connection row is saved. If it fails, the new vendor org (and its invitation) is deleted and the call throws `UPSTREAM_FAILED`.
  - A vendor org that already exists still gets the `/vendor/shops` email. That email now fails loudly too.
  - (`invai-backend/src/modules/vendors/service.ts`)
- **`GET /api/auth/invite-preview?id=`**, a small Better Auth plugin in `src/auth.ts`.
  - For a pending invitation it returns `{status: "pending", email, role, organizationName, organizationType, invitedBy, hasAccount}`. For anything else it returns only `{status: "used" | "expired" | "not_found"}`.
  - `invitedBy` is the inviting shop's name on a vendor invite, read through `withSystem` from `vendor_connections`. The reason is written in the code.
  - Rate limits: 30 per minute per IP. I also added a limit of 10 per minute to `/organization/accept-invitation`.
- **`requireEmailVerificationOnInvitation: false`** is now set explicitly in `auth.ts`. It matches Better Auth 1.7.5's default for UUID ids and states the choice in the config.
- **Accept page** (`invai-web/src/routes/accept-invite.$invitationId.tsx`):
  - Reads the preview first. The email field is locked to the invited address. The form starts on "Sign in" when that email already has a password account.
  - Used, expired and invalid or canceled links each get their own title, a hint and a "Sign in" button.
  - A user signed in under a different email is told whose invite it is and gets a "Log out" button.
  - Better Auth error codes map to translated messages (`INVITATION_NOT_FOUND`, `YOU_ARE_NOT_THE_RECIPIENT_OF_THE_INVITATION`, `USER_ALREADY_EXISTS_USE_ANOTHER_EMAIL`, `INVALID_EMAIL_OR_PASSWORD`).
  - Vendors land on `/vendor`.
- **Team invite message** (`team.tsx`): the success toast uses the email the API returned. The mutation is silent on errors and maps them itself: `UPSTREAM_FAILED` → "The invite email didn't go out. Check the address and try again.", `CONFLICT` → "That person is already on the team."
- **Strings:** 17 new keys in English and Spanish. I added them by hand to `src/i18n/en.ts` and `es.ts`, plus `scripts/i18n-es.json`. See "Decisions" for why I didn't use the generated output.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | Unit test "creates a Better Auth invitation…" (row with ~7-day expiry, `/accept-invite/<id>` in the text and HTML, 0 `users` rows). For real: `POST /api/v1/team/invite` as owner → invitation `f7aeac3d…` pending, expires 2026-10-01; `select count(*) from users where email='rosa.t14@example.test'` = 0; Mailpit subject "Riley Owner invited you to Desert Bloom Tees on InvAI" (`staff-1-email.png`). Spanish: admin's locale set to `es` → "Alex Admin te invitó a unirte a Desert Bloom Tees en InvAI como Empacador." (`es-1-email.png`) |
| 2 | Yes | Browser: link → sign up → lands on `/` as Rosa, presser menu (`staff-2`, `staff-3`); DB member `presser / active`, invitation `accepted`. Existing user: unit test "an existing user just signs in and accepts" (`hasAccount: true` → accept 200 → active). Invalid, expired, used and wrong-email: unit tests (403 for another account, 400 for used or expired) and screenshots `state-used`, `state-expired`, `state-invalid`, `state-wrong-account`, `state-bad-password` |
| 3 | Yes | Unit test "a new vendor gets an /accept-invite link…" (no `/vendor/accept`, preview `invitedBy: "Bloom Shop"`, member `vendor / active` in a vendor org, `vendorShops` lists the shop). Browser: `vendor2-1…4` (email → accept page naming Desert Bloom Tees → `/vendor` → Shops shows Desert Bloom Tees); DB connection `active / portal / accepted` |
| 4 | Yes | Seed logins `owner@`, `admin@`, `presser@desertbloom.test` signed in on my API; full backend suite green (existing tenancy and vendor tests unchanged apart from the mailer mock added to `vendors/invite.test.ts`) |
| 5 | Yes | `staff-0-owner-invite-sent.png` shows the toast "Invitation sent to sam.t14@example.test" after a real send. With `SMTP_URL=smtp://localhost:1`, `staff-4-mail-failure.png` shows the error toast, the dialog stays open and 0 invitation rows exist; the API log has `invite email failed … ECONNREFUSED`. Unit tests cover both staff and vendor failure |

## Checks I ran
| Repo | Command | Result |
|---|---|---|
| invai-backend (shared tree at b117997 plus my changes and other cards' uncommitted work) | `pnpm typecheck && pnpm lint && pnpm test` with `TEST_DATABASE_URL=…/invai_test_t14` | tsc clean; `Checked 198 files… No fixes applied.`; `Test Files 39 passed (39) / Tests 226 passed (226)` |
| invai-backend (clean worktree: HEAD 29afd65 plus only my files) | `tsc --noEmit`, `biome check .`, `vitest run` | tsc ok; 188 files clean; `Test Files 33 passed / Tests 167 passed` |
| invai-backend | `vitest run src/modules/tenancy src/modules/vendors` | 25 passed (before the invitedBy addition), then covered by the full runs above |
| invai-web | `pnpm typecheck && pnpm lint && pnpm test && pnpm build` | tsc clean; `Checked 97 files… No fixes applied.`; `Tests 23 passed (23)`; `✓ built in 1.14s` |

An earlier full run in the shared tree failed with 15 failures (`column "submit_attempted_at" of relation "purchase_orders" does not exist`). That came from T-1-3's work in progress before its migration existed, which is why I also ran the clean worktree. After T-1-3 committed, the shared tree ran fully green, as shown in the first row.

## Exercised for real
Setup: my API ran from a clean worktree (HEAD plus my files) with `PORT=3140 WEB_ORIGIN=http://localhost:5184 BETTER_AUTH_URL=http://localhost:3140` against the dev DB. The web ran with `VITE_API_URL=http://localhost:3140 vite --port 5184`. I drove it with Playwright (Chromium) and read the mail through the Mailpit API on :8025. Screenshots are in `invai-docs/waves/1/reports/T-1-4/`, and I looked at every one.
- Owner invites Rosa (presser) by curl → invitation row, no user row, email in Mailpit → browser sign-up → lands in Desert Bloom Tees as a presser.
- Owner invites Sam from the Team page → toast "Invitation sent to sam.t14@example.test". Sam shows as Invited at the top of the list.
- Admin (locale `es`, web in Spanish) invites Lupe as a packer → Spanish toast and Spanish email → Spanish accept page at 390 px → Spanish Today screen at 390 px. There is no truncation. The admin's locale was set back to `en` afterwards.
- States: used link (Rosa's), expired (Sam's invite, date moved into the past), invalid id, signed in as presser@ opening Dee's invite (clear message, then Log out shows the form), and a wrong password on Sign in ("Email or password is wrong").
- Vendor: owner invites "Rio Prints T14" through `/api/v1/vendors/invite` → email "Desert Bloom Tees invited you to their vendor portal on InvAI", with no `/vendor/accept` link → accept page "Desert Bloom Tees invited you to InvAI to receive DTF gang sheets." → sign-up → `/vendor` → Shops lists Desert Bloom Tees.
  - `vendor-2-accept-page-BEFORE-FIX.png` shows a bug I found on the first run: the page named the new vendor org itself. That is why the preview now returns `invitedBy`. The `vendor2-*` screenshots are after the fix.
- Mail down (`SMTP_URL=smtp://localhost:1`): the Team page shows the translated error and 0 invitation rows exist.
- Refused case: `presser@desertbloom.test` → `POST /api/v1/team/invite` → `403 FORBIDDEN "Missing permission team.manage for team.invite"`.

## Decisions
- **InvAI inserts the invitation row itself.** It doesn't call Better Auth's `/organization/invite-member`, which stays disabled. The team rules (owner-only owner role, role fits the org type, audit), the transactional rollback on a mail failure, and the vendor path (the inviter isn't a member of the vendor org) all need our own code. Acceptance still goes through Better Auth's `/organization/accept-invitation`, which checks pending status, expiry and the recipient's email, and creates the member (status defaults to `active`).
- **No email verification before accepting.** Better Auth 1.7.5 skips it by default for UUID ids (`crud-invites.mjs`, `shouldRequireVerifiedEmailForInvitationIdAction`). I made it explicit. The link is only sent to the invited address, and accepting still requires a signed-in user with that email. **security-reviewer should confirm this.**
- **Email language comes from the inviter's `users.locale`.** There is no company language setting (no column exists). The locale column defaults to `en`, and no screen sets it yet.
- **The `user.invited` outbox event is no longer emitted.** The contract payload needs a `userId`, which doesn't exist until acceptance, and nothing consumes the event. See the gaps below.
- **Pending invitations are only in the first page of `team.list`.** Keyset pagination walks members only. The web asks for 200 rows per page.
- **i18n by hand.** `pnpm i18n` regenerated `en.ts`/`es.ts` lossily: it dropped hand-kept keys (`errors.pageNotFound*`, `mismatch.wrong_style`, `auth.inviteSubtitle`). So I restored both files and inserted only my 17 new keys. `scripts/i18n-es.json` has only additions. Otherwise the generated files would have deleted another owner's strings.
- Invites last 7 days for staff and 14 for vendors (the vendor value was already there).

## Known gaps and follow-ups
- **Contract event `user.invited`** (`invai-contracts/src/events.ts:16`, architect): the payload should become something like `{orgId, invitationId}`, or an event on acceptance should be added. It isn't emitted today; nothing listens.
- **Pending invitations have no name.** The `invitations` table has no name column, so the team list shows the email as the name until acceptance. Keeping the name would need a migration (a later card).
- **Company language:** there is no company-level language. It is worth a scope and design decision, because emails follow the inviter's `users.locale`, which the web never sets.
- **Team page buttons on invited rows:** "PIN" gives a clear error and "Deactivate" cancels the invitation. A real Resend and Revoke UI is B-92 (out of scope).
- **Rows left by the old flow:** users created credential-less by the old invite code, who have no member row left, can't sign up with that email (`USER_ALREADY_EXISTS`). Re-inviting such a person removes the old `invited` member row but not the user row. No production data exists; the seed doesn't create these rows.
- **Log noise:** `UPSTREAM_FAILED` isn't declared in the contract, so oRPC logs it as an "unhandled procedure error" even though the client gets the right code. `vendors.*` has the same issue with `upstream()` today.
- **Vendors page toast (`invai-web/src/routes/_app/settings/vendors.tsx`, not mine):** it will now show the server's English text "Invite email failed" on a mail failure. It should map `UPSTREAM_FAILED` to a translated message (web-engineer).
- **Dev DB test data from this card:** users `rosa.t14@`, `lupe.t14@` (active members of Desert Bloom), `mesa.t14@` and `rio.t14@` (vendor orgs "Mesa Transfers T14" and "Rio Prints T14" with active connections), plus accepted or canceled `*.t14@example.test` invitations. All pending ones were canceled. A reseed at the integration gate removes them.
- **Golden-path E2E** (`pnpm e2e`, the API golden path) wasn't run. It needs a fresh seed, and reseeding the shared dev DB isn't allowed during the wave. That is left to the integration gate.

## Blocked by other owners
- None blocking. The follow-ups listed above for the architect (event contract) and web-engineer (vendors toast) apply.

## Processes and data
- Stopped: API on :3140 (tsx) and web on :5184 (vite); both ports are free. Removed the `/tmp/t14-be` worktree. Leftover test DB: `invai_test_t14`.
- Shared dev DB: not reset. Only the test rows above were added, and admin@'s locale was put back to `en`.
- Nothing pushed.

---

# Round 2 (review findings: mail sent inside the tenant transaction)

Reviews: `reviews/T-1-4-reviewer-r1.md` and `T-1-4-security-reviewer-r1.md` asked for changes (blocking finding 1, shared by both); `T-1-4-product-designer-r1.md` approved. I followed the tech lead's decision to use a compensating pattern.

## Commit (on main, not pushed)
- invai-backend `659f1bc`: Invite emails go out with no transaction open (T-1-4 r2). It touches 7 files, all mine: `modules/tenancy/{invites,invites.test,router,service}.ts` and `modules/vendors/{invite.test,router,service}.ts`. Committed with `git commit -m … -- <paths>`, and `git show --stat HEAD` lists only those files.
- invai-web: no changes this round (`d6336e0` still stands).

## What changed
- **`team.invite` → `inviteTeammate(ctx, input)`.** The router no longer wraps it in `withTenant`.
  1. `withTenant(inviteUser)` checks the team rules and commits a pending invitation. `inviteUser(tx, ctx, input)` keeps its name and signature because security-reviewer's `tenancy/security.test.ts` calls it. It is now only this first step: it writes the pending row and sends no email.
  2. `sendInviteEmail` runs with no transaction open.
  3. **If the send works:** a second short `withTenant` cancels older pending invitations for that email (not the new one), removes any old-flow `invited` member row and writes the `team.invite` audit row.
  4. **If the send fails:** a short `withTenant` deletes the new invitation, then the call rethrows `UPSTREAM_FAILED`.
  - Behavior change: a failed re-invite now leaves the earlier invitation and its link working. Before, the old one was cancelled first.
- **`vendors.invite` → `inviteVendor(ctx, input)`.** The router no longer wraps it in `withTenant`.
  1. A short `withTenant` checks that the vendor isn't already connected.
  2. For a vendor that isn't registered yet, a short `withSystem` commits the vendor org and its invitation.
  3. The email goes out with no transaction open.
  4. **If the send works:** a short `withTenant` re-checks for duplicates and writes the connection, the audit row and the `vendor.invited` outbox event.
  5. **If the send fails, or the final write hits a race:** the new vendor org is deleted (its invitation cascades) and the error is rethrown.
  - No outbox event is emitted for a failed invite.
- **Timeout:** `deliverInviteMail` (`tenancy/invites.ts`) caps each send at 15 s (`INVITE_EMAIL_TIMEOUT_MS`) and turns a timeout or a refusal into `UPSTREAM_FAILED`. Nodemailer's own socket timeouts can run for minutes. `mailer.ts` (T-1-1's file) is unchanged.
- **Why not `afterCommit`:** its hooks swallow errors, so the request couldn't report a failed send (AC5). The post-commit step is written out explicitly instead.

## New tests
- **`tenancy/invites.test.ts`:**
  - "sends the email after the invitation is committed, with no transaction open". The `sendMail` mock records the number of connections checked out of `appPool` and `systemPool`, and whether the linked invitation is visible from a fresh connection. It expects `[{busy: 0, committed: true}]`.
  - "removes the committed invitation when the email fails, and keeps an older link working". At send time the row was committed with no connection busy. Afterwards only the first invitation remains, and it is still `pending`.
  - "a mail server that hangs counts as not sent". A 500 ms mock delay with a 50 ms limit gives `UPSTREAM_FAILED`.
- **`vendors/invite.test.ts`:** 0 busy connections at send time on the success path. On the failure path: 0 busy connections, no invitation, no vendor org, no connection.
- **Mutation check:** I temporarily wrapped the staff send in `withTenant`. Both new staff tests failed (`expected [{busy: 1, committed: true}] to deeply equal [{busy: 0, committed: true}]`), so they catch the bug. The file was restored, and `cmp` against the backup matched.

## Checks (round 2)
| Repo | Command | Result |
|---|---|---|
| invai-backend (tree = HEAD plus only my changes) | `pnpm typecheck && pnpm lint && pnpm test` (`TEST_DATABASE_URL=…/invai_test_t14`) | tsc clean; `Checked 198 files… No fixes applied.`; `Test Files 39 passed (39) / Tests 231 passed (231)` (includes the unchanged `tenancy/security.test.ts`) |
| invai-web | unchanged since round 1 | round 1 result stands (typecheck, lint, 23 tests, build) |

## Exercised for real (round 2)
API on :3140 from `invai-backend` (`tsx`, not watch), against the dev DB, reading mail from Mailpit.
- **Mailpit up:** `POST /api/v1/team/invite` (kai.t14r2) → 200 `status: invited`, email "Riley Owner invited you to Desert Bloom Tees on InvAI". `POST /api/v1/vendors/invite` (Sol Transfers T14r2) → 200, email "Desert Bloom Tees invited you to their vendor portal on InvAI". Both invitations are `pending` in the DB.
- **Mail down** (`SMTP_URL=smtp://localhost:1`):
  - Re-invite of kai as presser → `502 UPSTREAM_FAILED`. Kai's original `office` invitation is still `pending`.
  - New staff invite (nope.t14r2) → `502 UPSTREAM_FAILED`, no row.
  - New vendor (Ghost Transfers T14r2) → `502 UPSTREAM_FAILED`, 0 orgs with that name.
  - `pg_stat_activity` idle-in-transaction count = 0.
  - The API log shows 3 "invite email failed" lines.
- Cleanup: the round 2 test invitations were cancelled. The API was stopped and :3140 is free.

## Decisions (round 2)
- `inviteUser` stays as the first, transactional step so another owner's security test keeps working unchanged. The full flow is `inviteTeammate`. If security-reviewer prefers, their test can call `inviteTeammate` later.
- Older invitations are replaced only after a successful send, so a failed re-invite can't kill a working link.
- The 15 s limit races the send; it doesn't abort the SMTP session. A send that finishes after the timeout would deliver a link to an invitation that has already been deleted. The page then shows "This invite link doesn't work", and the inviter already saw an error. This is noted as a known limit. Aborting for real needs `mailer.ts` changes (T-1-1).

## Known gaps (added)
- The timeout race described above.
- If the final write after a successful send fails (for example a database outage), the invitation stays committed and the email is out, but the audit row, or for vendors the connection, is missing. The link still works for staff. For a vendor, the new org is removed and the error is returned.
