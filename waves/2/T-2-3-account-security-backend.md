# T-2-3: Account security (backend)

| Field | Value |
|---|---|
| Wave | 2 |
| Scope ref | always-in-scope: security |
| Backlog | B-09, B-60 (backend) |
| Owner | backend-foundation |
| Reviewer | reviewer |
| Co-reviewers | security-reviewer |
| Risk flags | auth, pii |
| Model | opus |

## Owned paths (edit)
- `invai-backend/src/auth.ts`, the auth migration if the plugins need tables
- New `invai-backend/src/lib/auth-mail.ts` (email templates en/es for verification, reset and MFA notices)
- tests next to these files

## Read-only paths
- `integrations/vendors/mailer.ts` (call `sendMail`)

## Acceptance criteria
1. **Email verification:**
   - Sign-up sends a verification email (en/es) linking to `${WEB_ORIGIN}/verify-email?token=`.
   - Unverified owners can sign in, but actions that move money return `EMAIL_NOT_VERIFIED`: **label buy and `billing.checkout`/`billing.portal` only.** Connecting a channel (CSV or Shopify OAuth) is *not* gated on verification — it's the first thing a self-serve small shop does after signup (`scope.md`: "small shops must be able to self-serve without a call"), and it doesn't move money. Gating it would strand a brand-new shop mid-onboarding if the verification email is slow or lands in spam.
   - Accounts created through an accepted invite count as verified, because the invite proved the email.
   - Seed users are verified.
2. **Password reset:**
   - `requestPasswordReset` always answers the same way, whether or not the email exists.
   - The link goes to `/reset-password?token=` and expires in 1 hour.
   - A reset revokes all other sessions.
   - It's rate limited.
3. **MFA:**
   - The Better Auth `twoFactor` plugin with TOTP and backup codes, issuer "InvAI".
   - Optional for everyone. Owners get a strong prompt, but it isn't forced in v1.
   - The sign-in flow returns `twoFactorRedirect` when MFA is on.
4. **Change password and sessions:** changing the password needs the current one and revokes other sessions. Listing and revoking sessions works.
5. **Floor PIN sessions are unaffected.**
6. Tests cover every path, including token reuse and expiry, and enumeration-safe responses.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build` in invai-backend, with your own test DB.
- Curl against your own API with Mailpit: sign up, verify, then reset, then enable TOTP and sign in with a code (generate it with `otplib` in a script).
- Check the installed Better Auth 1.7 API in `node_modules`.

## Out of scope
- Web screens (T-2-4). SSO.
