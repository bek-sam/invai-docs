# Review of T-28-4 (round 1)

- Reviewer: reviewer on opus. Author: web-engineer on sonnet. Commit: invai-web 4559618 (only commit ahead of origin/main, tree clean)
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` (invai-web @4559618, contracts dc62328) | exit 0 |
| `pnpm lint` | exit 0, 1 existing warning (src/content/markdown.test.ts, not in diff) |
| `pnpm exec vitest run src/features/account --reporter=dot` | 3 files, 18 passed |
| `scan-test-weakening.sh invai-web origin/main` | removed=0 added=39; no skip/only, snapshots, config or test-only branches |
| i18n key grep in en.ts / es.ts / scripts/i18n-es.json | all 15 new keys in all three; i18n-es-missing.json absent |
| `pnpm build` | skipped: one new flat route outside `_app`, routeTree.gen.ts diff is the plain generated shape |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 0 | yes (note 1) | auth-errors.ts:6-8 `satisfies AuthErrorCode`, mfa.ts:4 `satisfies keyof typeof COMMON_ERRORS`, `AccountLockedBody.safeParse` in mfa.ts:35 |
| 1 | yes | auth-errors.ts:27-41 checked before the 429 rule; minutes = ceil(sec/60) from body, then `Retry-After` (login.tsx onError), else 30; reset link to /forgot-password with email; tests mfa.test.ts:23-45; report script run |
| 2 | yes | password-section.tsx:43, reset-password.tsx:55 show it in the new-password `Field` error; mapping tested; reset page only unit-tested (needs emailed token, accepted) |
| 3 | yes | showMfaBanner = required && !enabled && deadline ahead; sessionStorage dismiss; `formatDate` (locale); last-known `mfa` ref avoids org-switch flicker; button goes to /account (note 2) |
| 4 | yes | _app.tsx:47 redirect when blocked; main.tsx QueryCache + MutationCache `goToMfaSetup` (skips when already on page), code in DIALOG_EXPLAINED_CODES (no toast), `shouldRetry` false; setup page outside `_app`, reuses TwoFactorSection, sign-out, unverified notice + resend; Continue only after session shows 2FA on, refetches `me` (exempt), `mfaReturnTarget` never returns the setup page or off-origin (unit test) |
| 5 | yes | two-factor-section.tsx: Turn off hidden + reason when `me.mfa.required`; disable path maps MFA_DISABLE_NOT_ALLOWED via authErrorMessage (line 144) |
| 6 | yes | `required` false for vendors gives state "off": no banner, no redirect (unit); no floor change; banner keyed on user `mfa` |
| 7 | yes | see i18n row; es copy natural tú form, no raw codes |

## Blocking findings
none

## Checks
- [x] Only owned paths changed: 17 files, all in features/account, routes/{login,reset-password,setup-two-step,_app}.tsx, main.tsx, lib/errors.ts, i18n, routeTree.gen.ts
- [x] Nothing outside scope (no backend, e2e, floor or contract edits)
- [x] Tests exercise the behavior; none weakened; mfa.test.ts is new and imports new modules, so it fails on base
- [x] Tenancy/idempotency n/a (client only); no secrets or PII logged; en/es present
- [x] Decisions: card-local, in report

## Optional notes (not blocking)
1. password-section.tsx:43 and reset-password.tsx:55 compare `res.error.code === "PASSWORD_REUSED"` as raw literals; a contract rename would fail the build only in auth-errors.ts and these two would silently fall back to the form-level error. Export a checked `isPasswordReused()` next to `isAccountLocked()`.
2. The banner button links to /account, not to the two-step section anchor; fine on today's page, an `#two-step` hash would match the AC more literally.
3. `Retry-After` fallback is read cross-origin; if the API does not expose it via CORS it is null and the body value (always sent) or 30 applies. Harmless.
