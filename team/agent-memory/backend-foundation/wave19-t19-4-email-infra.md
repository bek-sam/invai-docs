---
name: wave19-t19-4-email-infra
description: Non-obvious traps hit while building T-19-4 (email infra, signed links, B-133 rate buckets) — oRPC call() has no path, strict toEqual on mailer skips, shared-tree WIP typecheck noise
metadata:
  type: project
---

Lessons from T-19-4 (2026-09-27, wave 19), backend-foundation:

- `call(procedure, input, { context })` from `@orpc/server` runs middlewares with `path = []` unless
  you pass `path: ["ai","assistant","ask"]`. Anything that classifies by path (the rate-limit
  `bucketFor`) sees an empty path in such tests, so the existing `src/api/ratelimit.test.ts` only
  ever exercised the `reads`/`writes` buckets. Pass the real path in tests of path-based logic.
- `ai.assistant.ask` returns an async iterator: a middleware error surfaces when the iterator is
  consumed (`for await`), not from the `call()` promise.
- `sendMail` skips are asserted with strict `toEqual({ messageId: "skipped:pin-only" })` in
  `pin-only.test.ts` and `demo-guards.test.ts` (tenancy). Adding a field to its return breaks them;
  read skips back from `messageId` (`mailSkipReason`) instead of widening the shape.
- Adding a procedure whose permission a vendor holds (`org.read` on `me.notifications`) breaks the
  exact namespace list in `src/api/authz.test.ts` ("vendor users hold only ..."), which is the
  security-reviewer's file: report it, don't edit it.
- In a shared tree, `pnpm typecheck` fails on other agents' WIP (T-19-3 `digest/router.ts`); the
  post-edit hook reports them as "other files". Re-run later rather than chasing them.
- RLS violations come wrapped by drizzle ("Failed query: ..."); match on `err.cause`
  (pattern in `src/db/rls.test.ts`).

**Why:** each cost 5–15 minutes on this card. **How to apply:** before writing middleware/path tests,
mailer changes, or new procedures reachable by vendors.
