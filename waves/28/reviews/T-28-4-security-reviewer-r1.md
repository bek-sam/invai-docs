# Review: T-28-4 (security co-review, auth on the client)
Reviewer: security-reviewer (sonnet). Author: web-engineer (sonnet). Commit: invai-web 4559618. Round 1.
Verdict: **approve** (no blocking findings; two Low notes, no S-id logged)

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` (invai-web) | exit 0 |
| `pnpm exec vitest run src/features/account --reporter=dot` | 3 files, 18 tests pass |
Code review only (decision 0024); no browser, no API run.

## Checks
- Server is the control: `mfaState` only drives UX (banner, redirect). Every refusal comes from the API as `MFA_REQUIRED`; `main.tsx` sends it to the setup page from both QueryCache and MutationCache; `shouldRetry` never retries it. Hiding the setup page or editing the `me` cache grants nothing. A missing `mfa` fails open in the UI only (documented), server still blocks.
- No stale "enabled": the setup page leaves only when the Better Auth session shows `twoFactorEnabled`, then fetches `me` with `staleTime: 0` and invalidates all queries. `_app` beforeLoad reads `me` each navigation. The banner's `last` ref keeps only the last server `mfa` (cosmetic, per user).
- Dismissed banner: `sessionStorage` flag hides only `MfaBanner`. Enforcement is the `_app` beforeLoad redirect plus `MFA_REQUIRED` handlers, neither reads the flag. Cannot hide the enforcement page.
- Secrets: no console/log calls in the diff. TOTP seed, backup codes and tokens are handled only by the existing `TwoFactorSection` (unchanged apart from hiding "turn off"). Only new storage is `invai.mfaBannerDismissed = "1"`. No analytics calls added.
- Email: shown on the setup page in the UI (own address, from session); `/forgot-password?email=` search param already existed before this commit (route validated it before), so no new URL exposure.
- Redirect: `mfaReturnTarget` accepts only a leading `/` and not `//`, never `/setup-two-step`; it is passed to the in-app router `navigate`, not `window.location`, same rule as login.tsx:46. `redirect` values we generate are `location.href` (internal).
- Errors: lock/reuse/MFA messages are generic. Web adds no existence signal of its own; login still shows the generic bad-credentials text. (Whether the backend answers ACCOUNT_LOCKED for unknown emails is T-28-2's call; not in this diff.)
- Lock text uses body `retryAfterSec`, validated with the contract Zod schema, not free text.

## Findings
- Low (hardening, not logged): `mfaReturnTarget("/\\host")` and the login equivalent pass a backslash path; browsers read `/\` as `//`. Not exploitable here since navigation is client-side router only, but a `!redirect.includes("\\")` guard would close it. Owner: web-engineer, optional.
- Low (gap in evidence): vendor login and the reset-page PASSWORD_REUSED were not run for real (report says so); server enforces regardless.

## Open items
None blocking. Fix clocks: none.
