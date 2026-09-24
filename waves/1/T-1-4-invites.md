# T-1-4: Team and vendor invites work end to end

| Field | Value |
|---|---|
| Wave | 1 |
| Scope ref | `product/scope.md#mvp-in` items 9 and 14 (bug) |
| Backlog | B-51, B-52 |
| Owner | backend-foundation (with the web accept-invite route granted on this card) |
| Reviewer | reviewer |
| Co-reviewers | security-reviewer, product-designer (UI) |
| Risk flags | auth, pii, ui |
| Model | opus |

## Owned paths (edit)
- `invai-backend/src/auth.ts`, `invai-backend/src/modules/tenancy/**`
- `invai-backend/src/modules/vendors/**` (invite code only)
- `invai-web/src/routes/accept-invite*` and the web team-invite success message in `invai-web/src/routes/_app/settings/team.tsx`
- `invai-web/src/i18n/{en,es}.ts` (new keys only)
- tests next to these files

## Read-only paths
- `invai-backend/src/integrations/vendors/mailer.ts` (call `sendMail`; T-1-1 owns it)
- `invai-backend/src/api/context.ts`

## Evidence
`build/audit-2026-09-24.md` §A-BE B-51 and B-52.

## Acceptance criteria
1. Inviting a staff member creates a real Better Auth organization invitation (a row with an expiry) and sends an email (en/es by company language). The email links to `/accept-invite/<id>`. No credential-less user row is created ahead of time.
2. A new person opens the link, signs up with the invited email, and becomes an `active` member with the invited role. An existing user just accepts. Invalid, expired, used or wrong-email invites show a clear message.
3. The vendor invite for a vendor that isn't registered yet uses the same flow and route, so the `/vendor/accept?token=` link is gone. An accepted vendor sees the shop in the portal.
4. Existing members and the seed still work (the seed logins still sign in).
5. The web shows "Invitation sent to <email>" only when the backend actually sent it. Mail failures show an error.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test` in invai-backend and invai-web (plus `pnpm build` in web).
- For real, on your own API port plus the web dev server:
  - invite a new email as the owner;
  - open the email in Mailpit (:8025) and follow the link;
  - sign up and land in the app with the right role.
  - Do the same for a vendor invite.
  - Take screenshots of both and look at them.

## Out of scope
- PIN-only staff with no email (B-92, wave 5). Resend and revoke UI (B-92).
