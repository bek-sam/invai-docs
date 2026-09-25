# Review of T-2-4 (round 1)

- Reviewer: security-reviewer on Sonnet 5
- Author: web-engineer on Opus 5.5
- Verdict: approve

Co-review scope: auth, ui risk flags. Same environment as the primary reviewer (worktree
`../invai-web-r24` at `23f0552`, API on invai-backend HEAD port 3294 against `invai_r24_copy`,
Mailpit :8025) — I reuse it rather than standing up a second copy. This is a web-only diff (no DB,
no server code); the actual controls (rate limits, token TTLs, encryption, lockouts) belong to
T-2-3 and were reviewed there (`T-2-3-security-reviewer-r1.md`). My job here is whether the web
layer handles secrets, tokens and gated errors correctly and doesn't create a new client-side hole.

## Threat model (brief)
- Entry points added: five public routes (`login`, `signup`, `forgot-password`, `reset-password`,
  `verify-email`) and one authed route (`/account`), all client-side only — every one of them calls
  Better Auth's own client (`authClient.*`), which hits the server endpoints T-2-3 already
  threat-modeled. No new fetch/XHR target, no new trust boundary.
- Data handled in the browser that wasn't before: the TOTP `otpauth://` URI (contains the raw
  base32 secret), 10 backup codes, the reset/verify JWT/opaque tokens (in the URL), session tokens
  (via `listSessions`/`revokeSession`).
- Worst outcome if this layer is wrong: a secret (TOTP seed, backup codes, reset token) persists
  somewhere a second party can read it later (localStorage, browser history, logs), or the client
  displays/acts on unverified data as if it were verified.

## Findings

### Low — reset and verify-email tokens remain in the address bar after use
`invai-web/src/routes/reset-password.tsx` and `verify-email.tsx` read the token from
`Route.useSearch()` and never call `navigate({ search: {}, replace: true })` (or
`history.replaceState`) after it's consumed. Confirmed live: after a successful password reset, the
"Your new password is set" page's URL still reads `.../reset-password?token=<the now-used token>`;
navigating back to the same URL re-renders the set-password form rather than an immediate dead-link
state (the dead-link state only appears after an actual failed `resetPassword` call, which is
correct — it's not a logic bug, just that the token sits visibly in the bar the whole time).

Impact is limited because both tokens are single-use and already invalidated server-side the moment
they're consumed (T-2-3), so a second party reading the token from browser history or a screenshot
can't do anything with it once it's been used — and if they see it *before* it's used (e.g. a shared
computer, shoulder-surfing, or synced browser history sync'd to another device), the reset link
itself was already exactly that sensitive by design (anyone with the link can reset the password
once). The marginal risk this adds is the token's visibility lingering after use, in browser history,
for someone who later has read access to that browser. No referrer leak: I checked `AuthLayout` and
found no external-domain resources (images, fonts, scripts) loaded on either page while the token is
in the URL, so there's no realistic third-party leak via the `Referer` header.

**Not blocking** — this is a hardening item, not a control gap (the token is dead the instant it's
used, and the pre-use exposure is inherent to any link-based reset flow). Recommend it as a Low
finding: strip `?token=` from the URL with `replace: true` navigation right after a successful
`verifyEmail`/`resetPassword` call (and, more defensibly, immediately on mount for
`reset-password`, since the token doesn't need to stay visible for a resubmission — the form
doesn't re-send it visibly anyway). I'm not filing this in `v1-review.md` myself since I only write
this review file per my task scope; flagging it here for the tech lead to log with an owner
(web-engineer).

### Verified controls (no finding)

- **No secret ever reaches `localStorage`/`sessionStorage`/logs.** Grepped the full diff
  (`git show 23f0552 | grep -n "localStorage\|sessionStorage\|console\."`) — zero hits. The TOTP
  URI and backup codes live only in `TwoFactorDialog`'s local `useState`, discarded on unmount/close.
- **Backup codes and QR shown exactly once.** Each "Turn on"/"New backup codes" flow re-asks for the
  password and issues a fresh secret; there is no path to re-display a previously-issued secret or
  code set from cached state.
- **`EMAIL_NOT_VERIFIED` handling is generic, not route-specific.**
  `verify-email-banner.tsx`'s `VerifyEmailPromptHost` subscribes to the whole mutation cache and
  keys off the error `code`, not a hardcoded list of routes. This means it will also catch
  `shipping.buy`/`batchBuy`/`billing.checkout` (per T-2-3's `EMAIL_VERIFIED_PROCEDURES`) without the
  web needing to know that list — reduces the chance a future gated endpoint is silently un-gated
  in the UI. Live-verified against `billing.portal`.
- **Sensitive account actions require the current password client-side too**, matching the
  server's own requirement: `changePassword`, `twoFactor.enable/disable/generateBackupCodes` all
  send the typed password; there's no client-only bypass of these dialogs (they're plain forms that
  fail closed — no code path calls the underlying `authClient` methods without the password field
  populated by the user).
- **Session revoke is a thin, correct wrapper.** `sessions-section.tsx`'s revoke handler calls
  `authClient.revokeSession({ token })` with the row's own token — I independently verified the
  underlying primitive at the API (two independent sign-ins as `office@desertbloom.test`, revoking
  one from the other immediately turned its `get-session` into `null`). No client-side session data
  (tokens) is written anywhere but React state and the (invisible) Better Auth cookie.
- **Vendor `/account` access (`_app.tsx`'s `shared` allowlist) does not expose cross-tenant data.**
  Live-checked as `vendor@suncitydtf.test`: the page renders only Better-Auth-session-scoped data
  (own name, email, password form, own 2FA state, own sessions) — no company/tenant query was added
  to any `features/account/*` file. This is safe to allow for every org type.
- **Sign-up enumeration** (`USER_ALREADY_EXISTS`) is pre-existing (T-2-3's report, "already there").
  Not this card's scope; the card only asked for the *reset* flow to be enumeration-safe, which it
  is (live-verified, symmetric ~53–56 ms timing and identical body).
- **No client-side rate-limit bypass added.** The web doesn't implement or cache its own retry/backoff
  logic that could mask or multiply requests; it maps the server's 429 to a translated message and
  stops (`authErrorMessage`, `err.status === 429` checked first, before any code-specific branch).

## Acceptance criteria (security-relevant subset)
| # | Met? | Evidence |
|---|---|---|
| 1 Forgot page never reveals account existence | Yes | Live: identical response/timing for known vs. unknown email |
| 3 MFA code or backup code required, each backup code single-use | Yes | Live: wrong TOTP code rejected, right code accepted; backup code accepted once, rejected on reuse |
| 4 TOTP QR/setup key and backup codes shown once; sessions revoke works | Yes | Code read + live, see Findings above |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed — see primary reviewer's file
- [x] Nothing outside scope
- [x] Tests not weakened (per primary reviewer's scan; I additionally grepped the diff for
      `localStorage`/`sessionStorage`/`console.` myself — clean)
- [x] No PII/secrets in logs (grep above); tenancy n/a (no DB in this repo); idempotency n/a
- [x] Decisions recorded: none new required from me; the Low finding above should be logged in
      `invai-docs/security/v1-review.md` by the tech lead/security owner — out of scope for me to
      edit from a review file

## Optional notes (not blocking)
- Log the reset/verify-email token-in-URL item as a Low finding in `v1-review.md` with owner
  web-engineer, alongside the existing T-2-3 follow-ups (rate limits to Redis, `BETTER_AUTH_SECRET`
  rotation note).
- The double toast + dialog on `EMAIL_NOT_VERIFIED` is a UX issue, not a security one — see the
  product-designer file.
