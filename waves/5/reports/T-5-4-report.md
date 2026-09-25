# T-5-4 report: Team and stations

Status: **built**. The floor gap found at first is fixed in `effa695` (granted by the tech lead). Nothing is pushed.

## Commits
| Repo | SHA | What |
|---|---|---|
| invai-backend | `c56242a` | PIN-only staff, `users.pin_only`, the partial unique invite index (migration `0018_team_pin_only_invites`), `team.resend`/`team.revoke`, the mailer guard, tests |
| invai-web | `7bf4b3d` | `settings/team.tsx`, `settings/stations.tsx`, en/es keys (`team.*`, `stationsSettings.*`) |
| invai-ui | `eaad60d` | AC 6: `station.receiving` = "Receiving" / "Recibir" |
| invai-floor | `effa695` | A revoked station token unpairs the tablet (granted fix, see below) |

I built in my own worktrees (`invai-backend-t54`, `invai-web-t54`, now removed), then applied the patches to the main trees. Backend main was clean at `72c1139`. Web picked up T-5-3's `3da9a73`, and the patch applied cleanly on top of it. Only my files and hunks were staged.

## Backend (`modules/tenancy/**`, schema, mailer)
- **PIN-only (`team.invite` with `pinOnly: true`):** the new `addPinOnlyStaff` function inserts a `users` row directly with `email = pin+<uuid>@floor.invai.internal`, `pinOnly = true` and `emailVerified = false`, then an active `members` row with the floor role, then an audit row.
  - There is no `signUpEmail` call, no password and no `accounts` row, so the person can't sign in on the web. A test checks that the web sign-in returns 4xx with no session cookie.
  - The PIN is then set with the normal `team.setPin`. The web does this right after the invite.
  - The member takes a seat, checked by `assertWithinPlan("users")`.
  - Non-floor roles are refused. `changeRole` refuses to move a PIN-only member to a non-floor role.
- **Mailer guard:** `PIN_ONLY_EMAIL_DOMAIN` and `isPlaceholderEmail()` live in `integrations/vendors/mailer.ts`. `sendMail` skips placeholder addresses, and every mail path (invites, auth reset/verify, vendor mail) goes through it. `inviteUser` also refuses a placeholder address.
- **`toUser`** now returns `pinOnly` from the row. Invitation rows stay `pinOnly: false`.
- **Invitation uniqueness:** a partial unique index `invitations_pending_org_email_unique` on `(organization_id, email) WHERE status = 'pending'`.
  - The migration has one hand-added statement before the index. It cancels older duplicate pending invites (keeping the newest), so the index can build on existing data.
  - Re-inviting an email that has a pending invite now **resends** it: the same invitation id, a new 7-day expiry, and the role asked for. The row is updated only after the email went out, so a failed resend leaves the old invite as it was.
  - A concurrent insert that hits the index returns `CONFLICT` "An earlier invite is still pending".
  - The old "create a new invite, cancel the older ones" path is gone. `cancelPendingInvitations` is now unused but still exported.
- **`team.resend` / `team.revoke`** replace T-5-3's `NOT_IMPLEMENTED` stubs.
  - `userId` is the invitation id, which is the `invited` row's id.
  - For anything else (an accepted, canceled or unknown invite, or a member) they return the typed `NOT_INVITED` (409).
  - Resend sends the email with no transaction open, like invite. Revoke sets the invite to `canceled` and writes an audit row.
  - Only an owner can resend or revoke an owner invite.
- **Last owner:** the deactivate path already had the guard (`setMemberStatus`: `activeOwnerCount() <= 1` gives `CONFLICT`), so I added no code, only a test.
  - In practice the demote/deactivate refusal a user meets is "You cannot change your own role / deactivate yourself" (`BAD_REQUEST`), or `FORBIDDEN` for a non-owner.
  - The `CONFLICT` guard is reachable only in a race, because only owners can touch owners and nobody can act on themselves.

## Web
- **Team page:**
  - The Invite dialog has a "No email: floor PIN only" switch (shop orgs only). It limits roles to presser/packer/receiver, hides the email field, requires a 4–6 digit PIN, then calls `invite` and `setPin`.
  - If the PIN is taken, the member already exists. The dialog stays open with "…was added, but that PIN is taken", and the retry calls only `setPin`.
  - PIN-only rows show "PIN only, no email" in place of the email, plus a "PIN only" badge. The placeholder is never rendered.
  - Typing an email that has a pending invite shows "An earlier invite is still pending. Sending again resends it…", and the button becomes "Resend invite".
  - Invited rows have **Resend** and **Revoke** (Revoke is confirmed). The PIN button is hidden for invited rows.
  - A role change opens a confirmation: "Make X an owner?" with an owner warning, or "Change X's role? From A to B". Deactivate is confirmed too. Last-owner and `NOT_INVITED` errors are translated.
- **Stations page:**
  - **Edit** (name and kind) and **Revoke token**, shown only when a token exists. Revoke is confirmed: "Use this for a lost or stolen tablet…".
  - Deactivate is confirmed. Each card shows last seen or "Not seen yet". The card actions wrap at 390 px.
- **Accessibility:** a new `team.roleFor` aria-label on the role selects. The PIN column has screen-reader text inside a `relative` span, because an `sr-only` span placed off-screen stretched the page to 478 px at 390 px. The page is now 390 px wide.
- **i18n:** keys added by hand to `en.ts`, `es.ts` and `scripts/i18n-es.json`. I did not run `pnpm i18n`.

## Verification
- **Backend** (`invai_test_t54`, Redis /4):
  - `tsc` clean and `biome check .` clean.
  - `vitest run`: **67 files, 480 tests passed**.
  - New tests are in `pin-only.test.ts` (5) and in `invites.test.ts` (the resend-on-reinvite rewrite, the DB unique index, resend/revoke/`NOT_INVITED`, and admin vs owner invite).
- **Web** (also re-checked on the merged main tree): `tsc` clean, `biome check` clean, 70 tests passed, `vite build` ok.
- **invai-ui:** 20 tests passed, and biome is clean on the locales.
- **Browser run** (Playwright): DB copy `invai_t54_copy` (migrated: `pin_only` column and index present), API :3140, web :5143, floor :5144. The screenshots are in `reports/T-5-4/`, and I looked at each one.
  - **PIN-only:** added "Lupe Floor" as packer with a PIN, and the row shows no email (`3-team-en.png`). On the floor I paired "Pack 1", entered the PIN, and Lupe was signed in on the Pack screen (`4-floor-pin-only-signed-in.png`).
  - **Invites:** invited a new email, re-invited the same email (the "earlier invite pending" hint showed, `1-earlier-pending-en.png`), then used Resend on the row. **Mailpit had 3 mails** to that address. Revoke was confirmed, then the row disappeared. **0 mails** went to `floor.invai.internal`.
  - **Demote the last owner:** the sole owner's own row has no role control. `team.changeRole` on self returns `400 BAD_REQUEST` "You cannot change your own role". The owner-promotion confirm is in `2-confirm-owner-en.png`.
  - **Revoke station token (API):** `me.get` with the floor session gave 200 before the revoke and **401** after it. Signing in again with the revoked station token gave 401 "Station token not recognized".
  - **Spanish at 390 px:** `5-stations-es-390.png` (the receiving label is translated and no raw key shows) and `6-add-pin-only-es-390.png`.
- **Cleanup** (also after the floor fix): my API and Vite processes are stopped (ports 3140, 5143 and 5144 are free). `invai_t54_copy` and `invai_test_t54` are dropped, Redis db 4 is flushed, and both worktrees are removed.

## Floor fix for revoked station tokens (`effa695`, granted)
The first browser run showed a gap. The server signed the tablet out, but the floor app only locked on a 401 from the outbox. The screen stayed on "Reconnecting", and the next PIN attempt said "wrong PIN".

- **What changed:** a 401 now triggers `onAuthFailure()` in `app/actions.ts`, whether it comes from the queue load (`useStationQueue`), the SSE stream (the new `onUnauthorized` in `realtime/sse.ts`) or the outbox (`engine.onAuthExpired`).
- **How it decides:** `onAuthFailure()` asks the station token itself through `floor.staff` (`checkStationRevoked`, with one check in flight at a time).
  - If the answer is 401 or `STATION_REVOKED`, `stationWasRemoved()` runs `forgetStation()`. Unsent outbox entries stay, parked as `station_forgotten` as in T-4-2. It then sets `stationRemoved`, and the setup screen shows "This tablet was removed in InvAI. Pair it again with a new station QR code." (es: "Esta tableta se quitó en InvAI…").
  - Otherwise, including when offline, only the session ends, as before.
- **PIN login:** a non-`INVALID_PIN` 401 runs the same check and throws `STATION_REVOKED`. `LoginScreen` then shows nothing, because the setup screen takes over. A wrong PIN still says "PIN not recognized".
- **Checks:**
  - The new `src/app/stationRemoved.test.ts` has 4 tests: a 401 while signed in unpairs and keeps the outbox entry parked; a 401 with the station still known only ends the session; PIN login on a revoked station goes to setup; a wrong PIN stays a wrong PIN.
  - Floor tsc and biome are clean, 86 tests pass, and `vite build` is ok.
- **Browser run** (API :3140 on a fresh `invai_t54_copy`, floor :5144):
  - Signed in on Pack 1, revoked the token from the API, reloaded, and the setup screen showed the message in en and es. No "wrong PIN" appeared (`7-floor-removed-en.png`).
  - Paired again, revoked the token while the PIN pad was open, then entered a PIN. The tablet went to the setup screen with the message, not "wrong PIN".
- **Limit:** a tablet sitting idle with an open SSE stream only notices on its next request: a queue refresh, a scan or a reconnect. The backend doesn't close open streams when a token is revoked.

## Cross-card notes
- **The seed companies are `demo = true`** in the current dev DB: "Desert Bloom Tees" and "Sun City DTF". Because of that, `sendInviteEmail` skips every invite ("invite email skipped: demo company"), so the gate's Mailpit check on invites will see nothing. I set `demo = false` on my copy to verify. This is a question for T-5-3 or the seed: should the seeded shop really be a demo workspace?
- `RelativeTime` (invai-ui) shows English ("8 seconds ago") in Spanish. This isn't from T-5-4.
- The contract `team.resend` doc says "No-op target for pinOnly members". The backend returns `NOT_INVITED` for any non-invite, PIN-only members included.
