# T-28-1: Contract for account security (`MFA_REQUIRED`, `Me.mfa`, auth error codes)

| Field | Value |
|---|---|
| Wave | 28 |
| Scope ref | `always-in-scope: compliance` (Amazon DPP, `security/v1-review.md` "Amazon DPP 2025-11-25 update", MFA row; backlog B-188) |
| Spec | the DPP gap table in `security/v1-review.md` §"Amazon DPP 2025-11-25 update" plus this card |
| Owner | architect |
| Reviewer | `reviewer` (opus, a different model from the author) |
| Co-reviewers | backend-foundation (producer), web-engineer (consumer) |
| Risk flags | auth, contract |
| Model | sonnet |

## Owned paths (edit)
- `invai-contracts/src/contract/_base.ts` (COMMON_ERRORS)
- `invai-contracts/src/schemas/tenancy.ts` (`Me`)
- `invai-contracts/src/compat.ts` (`CONTRACT_VERSION`), `invai-contracts/src/photos.test.ts` (relax its exact-version pin at ~:432 to "at least 0.12.0")
- `invai-contracts/src/**/*.test.ts` for these files, `invai-contracts/package.json` (version), `invai-contracts/README.md`, `invai-contracts/CHANGELOG.md` if present

## Read-only paths
- everything else; `invai-backend/src/auth.ts`, `invai-backend/src/api/orpc.ts` (how `EMAIL_NOT_VERIFIED` is thrown), `invai-web/src/features/account/**`

## Depends on
- nothing. **This is the stub the other auth cards build on: commit it first, as fast as possible.**

## Interfaces promised
- `COMMON_ERRORS.MFA_REQUIRED = { status: 403, message: "Turn on two-step sign-in to continue", data: z.object({ deadline: Timestamp.nullable() }) }` (same style as `EMAIL_NOT_VERIFIED`, with a doc comment naming T-28-2 and the DPP).
- `Me.mfa`: `z.object({ required: z.boolean(), enabled: z.boolean(), deadline: Timestamp.nullable() }).optional()`; optional so floor sessions and older backends stay valid. Doc comment: `required` = the user holds an **active owner or admin membership in any non-sample org** (vendor orgs only have the `vendor` role, so vendors are never required; sample workspaces don't count); `deadline` = when the grace period ends (null when not required).
- Better Auth error codes (not oRPC errors; pure constants plus one schema, additive) in `src/schemas/tenancy.ts`: `AUTH_ERROR_CODES = ["ACCOUNT_LOCKED", "PASSWORD_REUSED", "MFA_DISABLE_NOT_ALLOWED"] as const` with their HTTP statuses documented (423, 400, 403), and `AccountLockedBody = z.object({ code: z.literal("ACCOUNT_LOCKED"), message: z.string(), retryAfterSec: z.number().int() })`. README auth section lists them.

## Acceptance criteria
1. Given the contract package, when backend and web import `COMMON_ERRORS`, then `MFA_REQUIRED` exists with status 403 and `data.deadline` typed as an ISO timestamp or null.
2. Given a `Me` value without `mfa`, when parsed, then it is valid (back-compatible); with `mfa`, all three fields are checked.
3. `AUTH_ERROR_CODES` and `AccountLockedBody` are exported from the package index.
4. Only additions: `git diff origin/main -- src/` shows no removed or renamed field or procedure. Version bumped minor (0.12.0 → 0.13.0).
5. A schema test covers 1–3. `CONTRACT_VERSION` in `src/compat.ts` matches `package.json`.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test 2>&1 | tail -n 40` in invai-contracts.
- `pnpm typecheck 2>&1 | tail -n 20` in invai-backend and invai-web (they link the package): both still pass.

## Out of scope
- Any backend or web code. Any other error code.

## Budget
- About 30 minutes. Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
