# Gate-fix review: invai-backend 7a763a5 + 246838f
Reviewer: reviewer (Opus 5.5), 2026-10-09. Verdict: **approve**

- **7a763a5 (T-29-4):** only `src/modules/channels/webhook-auto-import.test.ts` (+6/-9). Fixes TS2322 by narrowing: `const fetched = mockEtsyReceipt(receipt).order; expect(fetched).not.toBeNull(); if (!fetched) throw`. No `as any`, `!`, `@ts-ignore` or `@ts-expect-error`. No assertion was removed or loosened: the `not.toBe("cancelled")` check stays, and it gains a not-null check.
- **246838f (T-29-2 security co-review):** only `src/modules/tenancy/security.test.ts` (+53). Test 1 calls `me.updateOrg` and `today.dismissChecklist` through the real router as a shop owner, with smuggled `demoOwnerUserId`, `demoRetiredAt` and `settings.demoRetiredAt`. It then checks the DB row and that `isUserMfaRequired` is still true. Test 2 checks that `isMfaRequired` keeps the requirement for a mixed sample/real membership. The `as never` casts only let the test send the smuggled input on purpose (non-blocking).
- **Mutation proof** (scratch git worktree at 7a763a5, removed afterwards):
  - A) `src/lib/mfa.ts` with `!m.sample` dropped: test 2 FAILS ("expected true to be false").
  - B) `tenancy/service.ts` `updateOrg` writing `settings.demoRetiredAt`: test 1 FAILS ("expected '2026-10-09T…' to be undefined").
  - Both tests can fail, so they are meaningful.

## Commands re-ran (invai-backend, HEAD 7a763a5)
| Command | Result |
|---|---|
| `pnpm typecheck` | exit 0, no errors |
| `pnpm lint` | 1st run exit 1 with no file listed. Re-run: exit 0, "Checked 513 files". `biome check` on the 2 files: clean. The 1st failure is most likely the uncommitted `src/modules/privacy/security.test.ts` (another agent's work in progress, not in these commits). |
| `pnpm vitest run src/modules/channels/webhook-auto-import.test.ts src/modules/tenancy/security.test.ts --reporter=dot` | 2 files, 18/18 passed |
| mutation A / B: `vitest run src/modules/tenancy/security.test.ts -t T-29-2` | each 1 failed / 1 passed (as expected) |

Scope: each commit touches one test file inside its author's paths. No production code changed. Blocking findings: none.
