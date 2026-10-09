# T-28-4: Web for account lockout, password history and required two-step sign-in

| Field | Value |
|---|---|
| Wave | 28 |
| Scope ref | `always-in-scope: compliance` (Amazon DPP; backlog B-188 web half, and the web messages for B-185 and B-186) |
| Spec | this card plus T-28-2's acceptance criteria |
| Owner | web-engineer |
| Reviewer | `reviewer` (opus) |
| Co-reviewers | security-reviewer (sonnet; auth flows on the client: no bypass, no secret in logs). Small UI change inside existing screens plus one interstitial page that reuses the existing two-step section, so no product-designer co-review (decision 0019) |
| Risk flags | auth, ui |
| Model | sonnet |

## Owned paths (edit)
- `invai-web/src/features/account/**`, `invai-web/src/routes/login.tsx`, `invai-web/src/routes/reset-password*.tsx`, a new route **outside `_app`** (like `verify-email.tsx`) for the "turn on two-step sign-in" page, for example `src/routes/setup-two-step.tsx`, the app shell `src/routes/_app.tsx` (banner and redirect), `src/main.tsx` (add `MFA_REQUIRED` to `DIALOG_EXPLAINED_CODES` so it never toasts), `invai-web/src/lib/**` error mapping, `src/routeTree.gen.ts` if regenerated
- `invai-web/src/i18n/en.ts`, `src/i18n/es.ts`, `scripts/i18n-es.json` (hand-edited, never `pnpm i18n`)
- tests next to the files above

## Read-only paths
- `invai-contracts/**`, `invai-backend/**`, `invai-web/e2e/**` (QA)

## Depends on
- T-28-1 (contract) committed; T-28-2 committed and running on the dev API (start after both).

## Interfaces promised
- none (consumer).

## Acceptance criteria
0. Codes come from the contract (`AUTH_ERROR_CODES`, `AccountLockedBody`, `COMMON_ERRORS.MFA_REQUIRED`), not string literals.
1. Login: when sign-in returns `ACCOUNT_LOCKED`, the form says, in en and es: "Too many wrong passwords. This account is locked for 30 minutes. Reset your password to unlock it now." with a link to the reset page; the minutes come from `retryAfterSec` (rounded up). No raw code shown.
2. Change password (account page) and reset password: `PASSWORD_REUSED` shows "You used this password before. Choose a new one." (en/es) next to the new-password field.
3. Banner: when `me.mfa.required && !me.mfa.enabled` and the deadline is in the future, every app page shows a dismissible-for-this-session banner: "Owners and admins need two-step sign-in. Turn it on by <date>." with a button to the two-step section; the date is formatted with the active locale.
4. Enforcement: when any oRPC call returns `MFA_REQUIRED`, or `me.mfa` shows the deadline passed, the app routes to the "Turn on two-step sign-in" page, which reuses the existing two-factor setup (`two-factor-section.tsx`) and offers sign-out; if the email isn't verified yet (turning on two-step needs it), the page says so and offers "resend verification email"; after the user turns it on, `me` is refetched and the app returns to the page they wanted. No redirect loop (a test proves it), and the query client doesn't retry `MFA_REQUIRED`.
5. The two-step section hides the "turn off" action when `me.mfa.required` and says why ("Owners and admins must keep two-step sign-in on."); a `MFA_DISABLE_NOT_ALLOWED` response shows the same text (en/es).
6. Vendor users (role `vendor`) see no banner and no setup page (`me.mfa.required` is false for them). Nothing changes in invai-floor. Switching orgs doesn't make the banner flicker (required is per user).
7. Every new string exists in `en.ts`, `es.ts` and `scripts/i18n-es.json`; `scripts/i18n-es-missing.json` is absent or has none of these keys.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build` in invai-web (`2>&1 | tail -n 40`).
- Component or hook tests (Vitest) for: the error mapping of the three codes, the banner's show/hide rules, the redirect and no-loop rule, the hidden disable action.
- Exercise for real (no browser by hand and no screenshots, decision 0024): the API on :3000 and web on :5173 are your slot (check with the tech lead that nobody else holds them; record the PIDs you start). A headless Playwright script under `/tmp` (not committed; e2e/** is QA's) or a `tsx` script that: signs up a fresh user `t284-<ts>@desertbloom.test`, creates a shop, asserts the banner text; backdates the grace in the dev DB for **that user only**; reloads and asserts the setup page; turns on TOTP with a computed code; asserts the app loads. Also 10 wrong passwords for that user → the lockout message. Print the assertions passed.

## Out of scope
- Backend behavior (T-28-2). E2E suite changes (QA, only if the gate shows a need). Floor app.

## Budget
- About 2 hours. Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
