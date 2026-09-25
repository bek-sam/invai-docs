# T-5-4: Team and stations

| Field | Value |
|---|---|
| Scope ref | `product/scope.md#mvp-in` items 5 and 14 |
| Backlog | B-92, plus the wave 1 follow-ups (invitation uniqueness, "an earlier invite is still pending") |
| Owner | web-engineer; backend-foundation for PIN-only staff and invite uniqueness |
| Reviewer | reviewer; co-reviewers product-designer, security-reviewer |
| Risk flags | ui, auth |

## Owned paths
- invai-web `routes/_app/settings/{team,stations}.tsx`, own i18n keys
- invai-backend `modules/tenancy/**` (invites, PIN-only members), the invitation unique index migration
- tests

**Clarified in plan review (architect r1):** the exact `team.invite`/`User` contract shapes are in `wave.md` under "Contract stubs (exact)" §4 — read those first. Two load-bearing findings:
- `email` on `User` **stays required** in the schema; it cannot become genuinely nullable. Better Auth's own `user` table hard-requires a unique, non-null email (checked in `node_modules/@better-auth/core`, no supported override), and `users.email` is a real Postgres `NOT NULL UNIQUE` column that Better Auth's adapter writes to directly (`auth.ts`'s `drizzleAdapter` points straight at InvAI's own `users`/`members` tables — there's no separate InvAI-only user schema in front of it). `pinOnly: true` instead makes the backend write a synthetic, non-deliverable placeholder email (`pin+<uuid>@floor.invai.internal`), skips `auth.api.signUpEmail` (no password, no verification mail, no `accounts` row — that's what actually prevents web sign-in), and adds a new `User.pinOnly` flag so the web never renders or mails that placeholder as a real address.
- The invitation unique index is confirmed as genuinely new work, not a gap-fill: `invitations` (`db/schema/tenancy.ts:177-193`) has only plain, non-unique indexes today; dedup is app-level only (`cancelPendingInvitations`, not atomic, gives the UI no signal). Add a partial unique index (`organizationId, email` where `status = 'pending'`).

## Acceptance criteria
1. **PIN-only staff:** floor-role staff (presser, packer, receiver) can be added with a name and no email. They get a PIN, can't sign in on the web, and appear in the team list.
2. **Invites:**
   - `contract/tenancy.ts`'s `team` router needs new `resend`/`revoke` procedures — neither exists today (only `list, invite, changeRole, deactivate, reactivate, setPin` are wired);
   - a unique pending invite per company and email (DB index); a second invite resends instead;
   - the UI shows "An earlier invite is still pending".
3. **Confirmations:** role changes (especially to owner), deactivation and revoke all need confirmation dialogs. The last owner can't be demoted (already enforced: `activeOwnerCount()` in `changeRole`, `service.ts:204-216,376-377`) or deactivated (**not confirmed to exist** on the deactivate path in plan review — verify and add the same guard, don't assume it's covered).
4. **Stations:** edit a station's name and kind, revoke a lost tablet's token (`stations.revokeToken`), and see its last seen time.
5. **Quality:** en and es, 390 px, keyboard accessible.

## Verification
- Typecheck, lint, test and build in backend and web.
- Browser on a DB copy: add PIN-only staff and sign them in on the floor with the PIN; resend and revoke an invite (check Mailpit); demote the last owner (refused); revoke a station token (the floor tablet is signed out). Screenshots in en and es.

## Added from the wave 4 gate
- AC 6: invai-ui's shared i18n is missing `station.receiving`, so Settings → Stations shows the raw key. Add "Receiving" / "Recibir".
