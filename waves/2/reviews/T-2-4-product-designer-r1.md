# Review of T-2-4 (round 1)

- Reviewer: product-designer on Sonnet 5
- Author: web-engineer on Opus 5.5
- Verdict: approve

Co-review scope: UX, states, copy, accessibility. I read the card, the author's report, the 40
screenshots in `invai-docs/waves/2/reports/T-2-4/`, and exercised the live flows myself (signup,
verify, forgot/reset, TOTP enable + sign-in, backup codes, sessions, the `EMAIL_NOT_VERIFIED`
dialog, vendor `/account`) against a fresh DB copy — see the primary reviewer's file for the setup
and commands; I reuse that environment rather than repeating it here.

## Screenshots looked at
Author's: 02, 05, 09, 10, 13, 17, 21, 24, 25, 26, 27, 28, 33, 39, 40 (the ones the author flagged as
looked-at), plus a spot check of 01, 06, 07, 15, 30, 34, 36, 38. Mine (live, this session): the QR
setup dialog, the wrong/right TOTP code states, the backup-codes dialog, the login MFA step
(390 px, es), a reused-backup-code rejection (390 px, es), the `EMAIL_NOT_VERIFIED` dialog+toast on
Billing, and the vendor `/account` page.

## Findings

### F1 — Double toast + dialog on `EMAIL_NOT_VERIFIED` (S3, cosmetic/annoyance, not blocking)
Screen: Billing (`/settings/billing`, "Manage billing") and Shipping ("Buy & print all"), en and es.
Confirmed live and in the author's own screenshots 39/40: clicking a gated action while unverified
opens the "Confirm your email first" dialog **and** shows a separate bottom-right toast with
near-duplicate text ("Verify your email before paying. Check your inbox for our link."). The dialog
alone is sufficient — it has the one actionable button ("Send a new link") the toast lacks. The
toast adds visual noise without adding information, worse on a screen already showing an inline
banner about the same thing.

Proposed change: suppress the generic mutation-error toast specifically for `EMAIL_NOT_VERIFIED`
(the wave already tracks suppressing it for `PLAN_LIMIT_REACHED`/`PAYMENT_REQUIRED`/
`CREDITS_EXHAUSTED` in `main.tsx`, owner web-engineer — add `EMAIL_NOT_VERIFIED` to that same list).
This is a one-line addition to an already-planned follow-up, not a new task. Non-blocking: nothing
is broken, the user still gets a clear, actionable path in both languages.

### F2 — Seed users default to English (S4, annoyance, out of scope for this card)
`users.locale` seeds as `"en"` for every seed login (owner, office, designer, presser, packer,
vendor, …). A Spanish-speaking seed user's first sign-in still shows English until they manually
switch it once in `/account` or the user menu — the language preference this card adds is real and
correct, but it can't fix a seed data default. Not a finding against T-2-4's code; flagging so it
doesn't get lost as "the locale bug T-2-4 introduced." If floor/office demo staff should default to
es, that's a seed script change in invai-backend (different owner, different repo) — I'd propose a
backlog item, not a blocker here.

### F3 — Backup codes and QR/setup key: shown once, not persisted (verified, no finding)
Confirmed by code read (`two-factor-section.tsx`) and live: the TOTP URI and the 10 backup codes
live only in the dialog's local React state (`Step` union), never `localStorage`/`sessionStorage`,
never logged. Closing the dialog and reopening "Turn on"/"New backup codes" always restarts at the
password step and issues a **new** secret — there's no way to re-view an old one. Copy uses
`navigator.clipboard`; download builds an object URL client-side and revokes it immediately after
the click. This is exactly right for a shown-once secret. No action needed.

### F4 — Accessibility spot check (pass, no finding)
- Every new field is a real `<label htmlFor>` + native `<input>`/`<select>` pair (`Field` component,
  reused from the existing pattern) — no div-based fake inputs.
- The 6-digit code field uses `inputMode="numeric"`, `autoComplete="one-time-code"`, and a visible
  label ("6-digit code" / "Backup code" swap correctly with `key={step}` so screen readers get a
  fresh announcement on toggle).
- Error and status text uses `role="alert"` / `role="status"` consistently across every new
  screen (login MFA step, forgot/reset, verify, account sections).
- Dialogs (`Dialog`/`DialogContent` from `@invai/ui`) are the same Radix-based primitive already
  used elsewhere in the app (focus trap, Esc-to-close, labelled by `DialogTitle`) — nothing custom
  was built here that could regress this.
- Backup codes list has `aria-label="Backup codes"` on the `<ul>`; per-row "Sign out" buttons on the
  sessions list have a computed `aria-label` ("Sign out {{device}}") instead of a bare "Sign out",
  which matters once there's more than one row.
- 390 px: no `scrollWidth > clientWidth` on `/account` or the login/forgot/reset flow at 390 px, en
  or es (author's assertion, and I re-confirmed visually on the login MFA step and a reused-backup
  screenshot I took at 390×844, es).

### F5 — Copy quality (pass, no finding)
Plain shop language throughout ("That code is wrong", "This link doesn't work anymore", "For your
safety we signed you out everywhere"), consistent tone with the rest of the app, no raw English
found in the es strings I sampled (account page, login MFA step, forgot/reset at 390 px — all fully
translated, including the newly-added error strings in `auth-errors.ts`/`es.ts`).

## Acceptance criteria (design-relevant subset)
| # | Met? | Evidence |
|---|---|---|
| 2 Translated banner + resend; `EMAIL_NOT_VERIFIED` prompt | Yes (with F1 non-blocking note) | Live dialog+toast on Billing, en/es |
| 4 QR, verify, backup codes shown once | Yes | Live TOTP enable end-to-end; F3 above |
| 5 en/es, 390 px, keyboard | Yes | F4, F5 above |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed — see primary reviewer's file (I didn't re-run `git diff --stat`
      myself, no reason to duplicate it)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; not weakened (per primary reviewer's scan)
- [x] en/es text present and correct for every string I sampled; no hard-coded English found in the
      new UI
- [x] Decisions recorded: none new from me: F1/F2 are proposed follow-ups, not decisions

## Optional notes (not blocking)
- F1: suggest folding into the already-planned `main.tsx` toast-suppression follow-up (owner
  web-engineer, wave.md).
- F2: suggest a backlog item for seed `locale` defaults (owner: whoever owns
  `invai-backend/src/db/seed`), separate from this card.
- Dates on the sessions list use the browser locale, not the app language (author-acknowledged,
  minor — `formatDateTime` is pre-existing code, not something this card should have touched).
