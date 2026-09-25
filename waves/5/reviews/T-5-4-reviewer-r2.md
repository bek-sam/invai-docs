# Review of T-5-4 (round 2)

- Reviewer: reviewer on Sonnet 5
- Author: web-engineer + backend-foundation on Opus 5.5
- Verdict: approve

Round 2 scope only: backend `711c37c`, the fix for round 1's blocking finding (revoke/deactivate
racing an accept). Everything else was already approved in round 1's files.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend log --oneline -1` / `diff --stat c56242a 711c37c` | `711c37c` on `main`, on top of `c56242a`; 2 files: `modules/tenancy/service.ts`, `modules/tenancy/invites.test.ts` — both owned paths, nothing outside scope |
| Read `service.ts` diff | `revokeInvite` and the pending-invite branch of `setMemberStatus` both now `UPDATE … WHERE id = ? AND status = 'pending' RETURNING id`; zero rows returned → `conflict("That invite was just accepted or canceled")` instead of the old unconditional update. Same pattern `resendInvitation` already used in round 1, now applied symmetrically. |
| New test **run against pre-fix code** (`git archive c56242a`, test file copied in, own DB `invai_test_t54_r2`, `REDIS_URL=…/13`, `vitest run src/modules/tenancy/invites.test.ts`) | **fails as required**: `a revoke racing an accept never cancels the accepted invite` → `AssertionError: promise resolved "{ ok: true }" instead of rejecting` (both the `revokeInvite` and `setMemberStatus` cases in the loop hit this before the 3rd assertion in the file runs) — confirms the test is real proof of the bug, not a test that would pass either way |
| Same test **run against `711c37c`** (main tree, own DB `invai_test_t54_r2fix`) | passes, as part of the full tenancy run below |
| `vitest run src/modules/tenancy/` (own DB `invai_test_t54_r2fix`, `REDIS_URL=…/13`) | **6 files, 47 tests passed** |
| `tsc --noEmit` | clean |
| `biome check src/modules/tenancy/service.ts src/modules/tenancy/invites.test.ts` | clean, 2 files |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend c56242a` | no hits (new test only, no removed assertions, no skips/mocks/loosening) |
| Cleanup | dropped `invai_test_t54_r2` and `invai_test_t54_r2fix`, flushed Redis db 13, removed `/tmp/review-T-5-4-r2` |

## How the race test proves the fix
The new test wraps the transaction in a `Proxy` that intercepts the guarded `UPDATE … RETURNING`
call: right before it runs, the proxy commits a real `status: "accepted"` update on a **separate**
connection (`db`, not `tx`) for the same invitation id — simulating Better Auth's `acceptInvitation`
landing in the exact window between the read and the write. It asserts two things: the call rejects
with `CONFLICT`, and the row's final status is `"accepted"`, not `"canceled"`. Confirmed above that
this genuinely fails on the pre-fix code (it silently returns `{ok:true}` and the row would end up
canceled) and passes on the fix. The loop covers both call sites the fix touches (`revokeInvite` and
`setMemberStatus`'s pending-invite branch).

## Round 1 blocking finding — resolved
`service.ts:434-439` (now ~440-446) and the `setMemberStatus` pending-invite branch both gained the
`WHERE status = 'pending'` guard, matching `resendInvitation`'s existing pattern. No new gap
introduced: `assertCanManage` and the audit-write ordering are unchanged, and the fix only adds a
`RETURNING` check plus a `CONFLICT` on the empty case.

## Acceptance criteria
Unchanged from round 1 (all met); AC2/AC3's revoke/deactivate paths are now backed by a race test
in addition to the happy-path tests already re-run in round 1.

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`modules/tenancy/service.ts`, `modules/tenancy/invites.test.ts`)
- [x] Nothing outside scope
- [x] Test proves the fix (fails on pre-fix code, passes on the fix) and is not weakened
- [x] Tenancy: `withTenant`/`Tx` unchanged; idempotency of revoke/deactivate now race-safe
- [x] Decisions recorded — commit message states the race and the guard clearly

## Optional notes (not blocking)
- The CONFLICT message ("That invite was just accepted or canceled") is a plain restatement of
  what happened; the web client isn't in this round's diff, so I didn't check whether `team.tsx`'s
  `teamError` mapping surfaces it distinctly from the existing `NOT_INVITED` message — worth a
  quick look next time the web side of team management changes, not blocking here.
