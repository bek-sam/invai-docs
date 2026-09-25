# Report: T-2-4 Account security (web)
Author: web-engineer on Opus 5.5

```
Card: T-2-4  Owner: web-engineer  Scope ref: always-in-scope: security
Owned (edit): invai-web/src/routes/{login,signup,verify-email,reset-password,forgot-password}.tsx,
              src/routes/_app/account.tsx, src/features/account/**, user menu in app-frame.tsx,
              src/lib/auth.ts (the card calls it auth-client.ts), src/i18n/{en,es}.ts
Also touched (web-engineer role paths, outside the card's list, see Decisions):
              src/routes/_app.tsx, src/lib/errors.ts (+ test), scripts/i18n-es.json, src/routeTree.gen.ts
Risk flags → co-reviewers: auth, ui → product-designer, security-reviewer
```

Commit (invai-web, `main`, not pushed): **`23f0552`**. Report and screenshots: invai-docs commit (see the end of this file).

## Built
- **Auth client** (`src/lib/auth.ts`): `twoFactorClient()` and `inferAdditionalFields({ user: { locale } })`, so `updateUser({ locale })` and `session.user.locale` / `twoFactorEnabled` are typed.
- **Login** (`routes/login.tsx`):
  - "Forgot password?" link next to the password label. It carries the typed email over.
  - When `signIn.email` returns `twoFactorRedirect`, the same page asks for the 6-digit code (`verifyTotp`), or for a backup code (`verifyBackupCode`) through "Lost your phone? Use a backup code".
  - `TOO_MANY_ATTEMPTS_REQUEST_NEW_CODE` and an expired challenge send the user back to the password step.
  - After sign-in the saved `users.locale` becomes the app language.
- **Forgot password** (`routes/forgot-password.tsx`): always answers "If that email has an account, we sent a link…". There's no `redirectTo`, so the email links straight to `/reset-password?token=`.
- **Reset password** (`routes/reset-password.tsx`):
  - new password plus a confirmation, with a mismatch check and at least 8 characters;
  - a missing, expired or used token (`INVALID_TOKEN`) shows "This link doesn't work anymore" with "Send me a new link";
  - success says every device was signed out and links to sign-in.
- **Verify email** (`routes/verify-email.tsx`):
  - `verifyEmail` runs once as a query (safe under StrictMode) and shows either success or failure (expired or invalid token);
  - the next step is "Go to InvAI" when signed in, "Sign in" otherwise;
  - it refreshes the session so the banner goes away.
- **"Confirm your email" banner plus prompt** (`features/account/verify-email-banner.tsx`, mounted in `_app.tsx`):
  - shown while `session.user.emailVerified` is false, with a "Send a new link" button (`sendVerificationEmail`) and a toast;
  - listens to the mutation cache: any `EMAIL_NOT_VERIFIED` opens a translated dialog, "Confirm your email first", with resend;
  - `errorInfo()` also gives that code a translated one-liner instead of the server's English.
- **Account page** `/account` (`routes/_app/account.tsx`, `features/account/*-section.tsx`):
  - **Profile:** name, read-only email and language. Saving calls `updateUser({ name, locale })`, switches the app language and refreshes `me`.
  - **Password:** current, new and confirm → `changePassword`. The toast says the other devices were signed out. A wrong current password shows a translated error.
  - **Two-step sign-in:**
    - Off: "Turn on" asks for the password, then shows the QR code (`qrcode.react`), the setup key and a code field (`verifyTotp`), then the backup codes once (copy, download, and "I saved my backup codes" before "Done").
    - On: "New backup codes" and "Turn off", each asking for the password.
    - Locked with an explanation while the email is unconfirmed.
  - **Where you're signed in:** `listSessions` with browser, OS, IP and last activity, "This device", "Sign out" per device (`revokeSession`) and "Sign out other devices" behind a confirm (`revokeOtherSessions`). `SESSION_NOT_FRESH` shows "For your safety… Sign in again", which signs out and returns to `/account` after sign-in.
- **User menu** (`app-frame.tsx`, user-menu block): an "Account and security" entry. Changing the language there also saves `users.locale`.
- **Sign-up** (`routes/signup.tsx`): the hard-coded English field and server errors are now translated (Better Auth codes go through `authErrorMessage`), and sign-up sends `locale`, so the confirmation email matches the UI language.
- **Error mapping** (`features/account/auth-errors.ts`): maps Better Auth codes to en/es messages. A 429 comes first; unknown codes never show server text.
- **Strings:** 122 new keys, added by hand to `src/i18n/en.ts` and `es.ts`, plus `scripts/i18n-es.json` so a later `pnpm i18n` keeps the Spanish. I didn't run `pnpm i18n`.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Forgot link, neutral forgot answer, reset with clear expired/used errors | Yes | 12, 28, 29, 30 (the unknown email got the same answer), 31 mismatch, 32 done, 33 used link, 34 no token |
| 2 Verify page success/failure; translated banner with resend; `EMAIL_NOT_VERIFIED` shows the prompt | Yes | 06/37 bad token, 07/38 success; 02 banner, 03 resend toast; **39 (en) / 40 (es): an unverified seed owner clicked "Buy & print all" → 403 `EMAIL_NOT_VERIFIED` → dialog + toast, and no label was bought** |
| 3 MFA sign-in with 6-digit code or backup code | Yes | 13 code step, 14 wrong code, TOTP sign-in OK; 15 backup code at 390 px, sign-in OK; 16 reused backup code refused |
| 4 Account page: name and language, change password, TOTP with QR, verify, backup codes once, sessions with revoke | Yes | 05, 08 wrong password, 09 QR, 10 codes (Done disabled until ticked), 11/17 on; 19 wrong current password; 20 saved in Spanish; 21 new codes, 22–23 turned off; 17→18 a device signed out (3→2 rows, and that browser went to /login); 27 stale session → "Sign in again" → back on /account |
| 4a `users.locale` drives email language | Yes | After saving Español, Mailpit subjects were Spanish ("Cambia tu contraseña de InvAI", "Desactivaste el inicio de sesión en dos pasos…"); before, English |
| 5 en + es, 390 px, keyboard | Yes | es: 20–24, 28–33, 37, 38, 40. 390 px: 15, 25 (dark), 28–33, 37, 38. `scrollWidth > clientWidth` = false at 390 px on /account. Every control is a native input, button, link or select; the Playwright flows drove them by role and label; dialogs are Radix (focus trap, Esc). |

Screenshots are in `invai-docs/waves/2/reports/T-2-4/` (01–40). I looked at 02, 05, 09, 10, 13, 17, 21, 24, 25, 26, 27, 28, 33 and 40. The test account and its TOTP secret and codes only ever existed in the dropped DB copy.

## Checks I ran
| Repo | Command | Result |
|---|---|---|
| invai-web | `pnpm typecheck` | exit 0 |
| invai-web | `pnpm lint` | 1 error, **not mine**: the formatter in `e2e/golden-path.spec.ts:346`, which is qa-engineer's uncommitted change in the shared tree. `biome check src scripts` → "Checked 107 files… No fixes applied", 0 errors |
| invai-web | `pnpm test` | 9 files, 47 tests passed (new: `auth-errors.test.ts`, `session.test.ts`, and an `EMAIL_NOT_VERIFIED` case in `errors.test.ts`) |
| invai-web | `pnpm build` | ✓ built in 1.30 s (the existing >500 kB chunk warning is still there) |

I didn't run `pnpm e2e`: the e2e suites are being edited right now (uncommitted) by their owner, and the golden path needs a fresh seed on the shared DB. The golden path's login uses the same email and password form (the `#email`/`#password` ids are unchanged); the one new thing is a link inside the form. **The QA gate should run it.**

## Exercised for real
My API ran on :3240 (non-watch `tsx`, `REDIS_URL=…/4`, `WEB_ORIGIN=http://localhost:5240`) against `invai_t24_copy` (migrated to 0012), with Mailpit. Vite ran on :5240 with `VITE_API_URL=http://localhost:3240`. Four Playwright scripts (Chromium):
- Sign-up (en) → banner → resend toast; the confirmation link came from the Mailpit API → "Your email is confirmed" → banner gone (count 0).
- 2FA on: wrong password → "That password is wrong", wrong code → "That code is wrong", then an RFC 6238 code computed from the setup key → 10 codes shown → "Done" disabled until the box is ticked.
- Sign-in with TOTP OK; with a backup code OK; the same backup code again → "That backup code is wrong or was already used."
- Sessions 3 → revoke → 2, and the revoked browser was redirected to `/login` on reload. Change password: wrong current refused, right one OK, short new password refused.
- Name and language saved as Español → UI in Spanish, and later emails in Spanish. New backup codes, then 2FA turned off (es).
- Sessions made 2 days old in the DB → `listSessions` 403 → "Sign in again" → `/login?redirect=/account` → back with the list.
- Forgot (es, 390 px, email prefilled from login) → Spanish email → mismatch error → reset OK → the other browser signed out → same link again → dead-link page. The old password was refused and the new one worked.
- Seed owner set `email_verified=false` → Shipping → "Buy & print all" → 403 → dialog (en and es). The flag was restored afterwards.
- Console errors in every run were only the expected refusals (401 wrong code or bad token, 400 wrong password or used token, 403 stale session or unverified). No other failed requests.

## Decisions
- **Banner mounted in `_app.tsx`**, not in `app-frame.tsx`. T-2-2 was editing the frame's banner area, so this kept my `app-frame.tsx` diff to the user-menu block plus one import line. `_app.tsx` also lets vendor orgs open `/account` (it was redirecting them to `/vendor`).
- **`errors.ts`:** a translated message for `EMAIL_NOT_VERIFIED`, because the global mutation toast showed the server's English "Verify your email first". It's 7 lines, placed after T-2-2's commit.
- **The prompt listens to every mutation**, including `meta.silent` ones. On Billing and Shipping the user sees the page's own toast **and** the dialog (screenshot 40). I kept both because only the dialog has "Send a new link". The product designer may want the toast dropped when the dialog shows.
- **Language:** the saved `users.locale` is the source of truth across devices. It's applied at sign-in, and both the account page and the user menu save it. `localStorage` still decides before sign-in.
- **The 2FA code step stays inside the login page** (no `twoFactorPage` redirect), so the `redirect` search param and the typed email survive. "Trust this device" isn't offered: the card doesn't ask for it, and it weakens the second step.
- The seed users' `locale` is `en`, so a Spanish-browser seed user switches to English at sign-in until they pick Español once.

## Known gaps and follow-ups
- `pnpm e2e` not run (see Checks). Owner: qa-engineer, at the wave gate.
- An error message already on screen stays in the old language if the user switches language (it's stored as text). Minor.
- Dates on the sessions list use the browser locale (the existing `formatDateTime`), not the app language.
- Better Auth rate limits stay per process (T-2-3 follow-up). The UI shows a translated "Too many tries" on 429.

## Blocked by other owners
- None. The only lint error is in `e2e/golden-path.spec.ts` (qa-engineer, uncommitted work in progress).

## Processes and data
- Stopped: API :3240 and Vite :5240 (by PID; both ports are free). The tech lead had also stopped them once mid-task; I restarted and stopped them again.
- Dropped `invai_t24_copy` (`dropdb --force`), flushed Redis DB 4. The shared dev DB `invai` was only read (as the template for the copy).
- Temporary scripts are in `/tmp/t24/` (not in any repo).
