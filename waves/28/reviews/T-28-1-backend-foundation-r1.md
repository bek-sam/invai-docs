# T-28-1 co-review r1 (backend-foundation, Sonnet 5.5; author: architect)
Verdict: approve

## Answers to the question
1. MFA_REQUIRED from `guard` like EMAIL_NOT_VERIFIED: yes. `_base.ts` adds a plain COMMON_ERRORS entry (403, `data: {deadline: Timestamp.nullable()}`); the backend throws it with `new ORPCError("MFA_REQUIRED", {status:403, data:{deadline}})`, same helper style as `errors.ts:26`. Nothing contract-side blocks placement after the permission check.
2. `Me.mfa` from `me.get`: yes. Optional `{required, enabled, deadline: Timestamp|null}` matches the card's definitions (floor sessions omit it; non-required gets deadline null). Deadline must be emitted as an ISO string with offset (`Timestamp` = `z.iso.datetime({offset:true})`): `Date.toISOString()` passes.
3. Better Auth bodies vs `AccountLockedBody`: yes. `new APIError("LOCKED", {code, message, ...extra})` serializes to a JSON body with those keys, so `{code:"ACCOUNT_LOCKED", message, retryAfterSec}` parses. Constraint for the producer: `retryAfterSec` must be an integer (Math.ceil), and `code` must be the exact literal.

## Findings (none blocking)
- Optional note: `AUTH_ERROR_CODES` / `AccountLockedBody` are not oRPC errors, so `authz.test.ts` and the contract's error map do not cover them; the producer's own tests should assert the 423 body with `AccountLockedBody.safeParse`.
- Optional note: `MFA_REQUIRED.deadline` doc says "when the grace ended"; `Me.mfa.deadline` is "when it ends". Same value, no code impact.
- Observed (not mine to judge): the tree already holds the producer's T-28-2 work (`src/lib/mfa.ts`, `errors.ts:31`, `src/auth.ts` `authError`, `account-security.test.ts`) and it uses the contract as written.

## Commands re-run
- `git -C invai-contracts show dc62328 --stat` and the `_base.ts` / `schemas/tenancy.ts` hunks: read.
- `cd invai-backend && pnpm typecheck 2>&1 | tail -n 20`: exit clean (`tsc --noEmit`, no errors) with the producer's uncommitted work in the tree.
- No tests run (read-only contract review; nothing edited).
