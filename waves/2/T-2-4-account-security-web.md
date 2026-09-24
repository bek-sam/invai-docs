# T-2-4: Account security (web)

| Field | Value |
|---|---|
| Wave | 2 |
| Scope ref | always-in-scope: security |
| Backlog | B-09, B-60 (web) |
| Owner | web-engineer |
| Reviewer | reviewer |
| Co-reviewers | product-designer, security-reviewer |
| Risk flags | auth, ui |
| Model | opus |

## Owned paths (edit)
- `invai-web/src/routes/login.tsx`, `signup.tsx`
- New `invai-web/src/routes/{verify-email,reset-password,forgot-password}.tsx`
- New `invai-web/src/routes/_app/account.tsx`, `invai-web/src/features/account/**`
- The user menu entry in `invai-web/src/components/app-frame.tsx`. T-2-2 edits the banner in the same file; coordinate by editing only the user-menu block, and commit with a pathspec after checking `git diff` holds only your hunk. If it doesn't, tell the tech lead.
- `invai-web/src/lib/auth-client.ts` (add the twoFactor client plugin)
- `invai-web/src/i18n/{en,es}.ts` (new keys by hand), and the hard-coded English sign-up errors (`signup.tsx:22-25`)
- tests next to these files

## Depends on
- T-2-3's routes (agreed in wave.md). Start with the screens and wire them up as T-2-3 lands. Final verification needs T-2-3 committed.

## Acceptance criteria
1. The login page has a "Forgot password?" link. The forgot page always shows "If that email has an account, we sent a link". The reset page sets a new password, with clear errors for an expired or used token.
2. The verify-email page shows success or failure. The app shows a translated "Verify your email" banner with "resend", and `EMAIL_NOT_VERIFIED` errors show that prompt.
3. Sign-in with MFA asks for the 6-digit code or a backup code.
4. The account page covers:
   - name and language (saves `users.locale`, which also fixes the invite-email language in wave 1)
   - change password
   - enable or disable TOTP, with a QR code, a verification step and backup codes shown once
   - active sessions with revoke
5. Every string in en and es; 390 px; keyboard accessible.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build` in invai-web.
- In the browser against T-2-3's API on a DB copy with Mailpit: go through every flow. Take screenshots in en and es and look at them.

## Out of scope
- Backend (T-2-3).
