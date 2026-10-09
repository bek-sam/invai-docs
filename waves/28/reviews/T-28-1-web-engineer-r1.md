# Review T-28-1 (consumer co-review) - web-engineer, round 1

Reviewer: web-engineer (consumer). Author: architect. Commit: invai-contracts dc62328 (0.13.0).
Verdict: approve

## Can T-28-4 build against this shape? Yes
- `COMMON_ERRORS.MFA_REQUIRED` (403, `data: { deadline: Timestamp|null }`) has the same style as `EMAIL_NOT_VERIFIED`; web matches on `code` and reads `data.deadline`.
- `Me.mfa` is optional, all three fields required when present: fits the banner and enforcement logic (`required && !enabled`, null deadline = unknown). Floor and older backends stay valid.
- `AUTH_ERROR_CODES` and `AccountLockedBody` are exported from the package index (the schema test imports them via `./index`). `retryAfterSec` is an int, good for a locked-sign-in countdown. Status map documented (423 / 400 / 403).
- `DIALOG_EXPLAINED_CODES` in `src/main.tsx` is a plain `Set<string>`; adding "MFA_REQUIRED" is a one-line change.
- Additive only: 0.12.0 -> 0.13.0, `CONTRACT_VERSION` bumped, photos version pin relaxed via `isContractVersionAtLeast`.

## Notes for T-28-4 (non-blocking)
- `AUTH_ERROR_CODES` are Better Auth body codes, not oRPC codes: `auth-errors.ts` must parse `{code,message}` bodies from the auth client separately from `errorInfo()`. Use `AccountLockedBody.safeParse`, falling back to the `Retry-After` header if `retryAfterSec` is missing.
- `MFA_REQUIRED` means "grace over" only; during grace the signal is `me.mfa`. `me.get` and `me.switchOrg` are exempt per the doc comment, so the redirect cannot loop on the `me` refetch.
- `shouldRetry` in `src/lib/errors.ts` must skip `MFA_REQUIRED` (card AC 4); web-side work.

## Evidence I re-ran
- `git -C invai-contracts show dc62328 --stat` and the `src/` hunks: read.
- `pnpm typecheck` in invai-web against linked contracts 0.13.0: clean, no errors.
