# Review of T-1-4 (round 1)

- Reviewer: product-designer on Opus
- Author: backend-foundation on Opus 5.5
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| Read every screenshot in `invai-docs/waves/1/reports/T-1-4/` (24 files) | all opened and inspected below |
| Worktree `invai-web@d6336e0`: `pnpm typecheck && pnpm lint && pnpm test && pnpm build` | tsc clean; biome "Checked 97 files… No fixes applied."; vitest 5 files / 23 tests passed; build OK |
| `git -C invai-web show d6336e0 -- src/i18n/en.ts src/i18n/es.ts` | read every new string in both languages |
| Live: web dev server on `:5194` against the API on `:3194`, `GET /accept-invite/<real id>` and `/` | both `200`, SPA serves |

## Acceptance criteria (UX-relevant)
| # | Met? | Evidence |
|---|---|---|
| 2 | Yes | `staff-2-accept-page.png`: title "Join your team", subtitle "Desert Bloom Tees invited you to join as Presser," email locked with the hint "The invite is for this email," tabs default correctly. Error states each get a distinct title + hint + one clear next action (`state-used.png` "Sign in", `state-expired.png` "Sign in", `state-invalid.png` "Sign in", `state-wrong-account.png`/`-after-logout.png` "Log out" then re-shows the form, `state-bad-password.png` inline red banner "Email or password is wrong" with the form intact). |
| 3 | Yes | `vendor2-2-accept-page.png` names the inviting shop ("Desert Bloom Tees invited you to InvAI to receive DTF gang sheets") rather than the new vendor org itself — the author caught and fixed this in-flight (`vendor-2-accept-page-BEFORE-FIX.png` shows the bug: it named "Mesa Transfers T14", the vendor's own new org). `vendor-4-shops.png`/`vendor2-4-shops.png` land the accepted vendor on a clean "Shops" list. |
| 5 | Yes | `staff-0-owner-invite-sent.png`: green toast "Invitation sent to sam.t14@example.test" only after a real send. `staff-4-mail-failure.png`: with SMTP down, the dialog stays open (no false "sent") and shows a clear red error "The invite email didn't go out. Check the address and try again." |

## Spanish and copy quality
Read `es-1-email.png`, `es-2-accept-page.png`, `es-3-landed.png` and the `invite`/`team` keys in `src/i18n/es.ts`. The Spanish is natural, not machine-translated: correct role nouns (Empacador, Planchador, Dueño, Recepción — shop-floor words, not literal dictionary translations), correct verb forms ("te invitó", "Crea tu cuenta o entra con la tuya"), consistent informal *tú* register matching the rest of the app, and the date formatting uses `es-MX` month names ("El enlace vence el 1 de octubre"). No English leaked into the Spanish screens I checked, and no truncation at the narrow width used (`es-2-accept-page.png` looks to be at the ~390px viewport per the ux-audit convention).

## Visual and interaction notes
- Consistent with the existing auth layout (centered card, InvAI mark, same button/input styles as login/signup).
- The email field being `readOnly` rather than editable on the accept page is the right call: it removes the exact mistake this card's own bug (`vendor-2-*-BEFORE-FIX`) shows is easy to make, and the hint text explains why the field is locked instead of just disabling it silently.
- Tab defaults to "Sign in" when the invited email already has a password account (`invite.hasAccount`), saving a step for returning users — good default, not just correct behavior.
- The wrong-account state (`state-wrong-account.png`) tells the reader exactly what's wrong and gives one button ("Log out") rather than a dead end — matches the plain-language, one-primary-action principle.
- Team list (`es-0-invite-sent.png`): pending invitations show an amber "Invitado" badge at the top of the list, visually distinct from "Activo" (green) — clear at a glance who hasn't joined yet.

## Blocking findings
None from a UX standpoint. (I note but do not block on the transaction/mail-timing finding in the reviewer and security-reviewer files — that's a backend correctness/availability issue, not a UI one, and per role boundaries the primary `reviewer` verdict already gates the push.)

## Checks
- [x] Only owned-by-card web paths changed (`accept-invite.$invitationId.tsx`, `settings/team.tsx`, `i18n/{en,es}.ts`, `scripts/i18n-es.json`).
- [x] Nothing outside scope.
- [x] States covered: loading (spinner), empty/not-applicable, error (4 distinct kinds), partial (signed in wrong account), success (accept → redirect, vendor → `/vendor`). All screenshotted and readable.
- [x] En/es parity — every new key has both languages, checked in the diff.
- [ ] Not independently verified this round: keyboard focus order and dark-mode rendering of the new accept-invite states (no screenshots of either were provided). Non-blocking — nothing in the diff suggests a new focus trap or dark-mode-specific styling, and the page reuses existing `AuthLayout`/`Field`/`Button` primitives that already carry those states. Recommend adding dark-mode + keyboard-nav shots next time this page changes.

## Optional notes (not blocking)
- The gray hint text under the locked email field ("The invite is for this email.") and under password-less states is fairly light; worth a contrast spot-check across the app's secondary-text token generally, but this page doesn't introduce a new color, it reuses the existing `Field` hint style.
- Consider (future card, not this one) showing the invited person's name once they're known, rather than only the email, in the team list's "Invited" rows — already flagged by the author as a follow-up (`invitations` has no name column).
