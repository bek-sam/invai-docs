# Review of T-5-4 (round 2) — security co-review

- Reviewer: security-reviewer on Sonnet 5
- Author: web-engineer + backend-foundation on Opus 5.5
- Verdict: approve

Round 2 scope only: backend `711c37c`, the fix for round 1's blocking finding (threat #10, double/
conflicting side effect on revoke racing accept). Round 1's other threats (1–9) are unaffected by
this diff and remain approved as filed.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend diff --stat c56242a 711c37c` | 2 files, `modules/tenancy/service.ts` + its test — no new entry point, no permission change, no new table |
| Read `service.ts` diff | `revokeInvite` and `setMemberStatus`'s pending-invite branch both changed from an unconditional `UPDATE …SET status='canceled'` to `UPDATE … WHERE id=? AND status='pending' RETURNING id`, throwing `conflict(...)` on an empty result — the same guard shape `resendInvitation` already used, now applied to both cancel paths |
| Race test **run against pre-fix `c56242a`** (own DB `invai_test_t54_r2`, `REDIS_URL=…/13`, `git archive` + test file copied in, per the skill's "does the new test fail without the change" step) | **fails**: `promise resolved "{ ok: true }" instead of rejecting` — i.e. on the vulnerable code, revoke silently wins the race and cancels an accepted invite, exactly threat #10's failure mode |
| Same test **run against `711c37c`** | passes, as part of the full tenancy suite below |
| `vitest run src/modules/tenancy/` (own DB `invai_test_t54_r2fix`) | 6 files, 47 tests passed |
| `tsc --noEmit` / `biome check service.ts invites.test.ts` | clean |
| Re-check threat #1 (cross-tenant) and #2 (escalation) are untouched by this diff | yes — the guard only adds a status predicate on an already tenant-scoped, already-`assertCanManage`'d update; no new query shape, no new permission |

## Threat re-check (#10 only — the others carry over unchanged from round 1)
| # | Threat | Control now | Test |
|---|---|---|---|
| 10 | Double/conflicting side effect: revoke racing a genuine accept | `WHERE status='pending'` on both cancel paths (`revokeInvite`, `setMemberStatus`'s invitation branch); zero-row update → `CONFLICT("That invite was just accepted or canceled")`, the accepted row is left untouched | `invites.test.ts`: "a revoke racing an accept never cancels the accepted invite" — proxies the transaction to commit a real `status: 'accepted'` write on a separate connection between the guarded read and the guarded write, then asserts `CONFLICT` and that the row stays `accepted`. Confirmed above to fail on the pre-fix code and pass on the fix. |

## Worst outcome (updated)
With the fix, a revoke that loses the race to a genuine accept now fails closed (`CONFLICT`) instead
of silently mutating an already-accepted invitation's audit state. There is no remaining path in
this diff where the false-audit-trail outcome from round 1's finding can occur. No cross-tenant or
privilege-escalation exposure was introduced or found.

## Blocking findings
none

## Checks
- [x] Tenancy — no change to `withTenant`/scoping, guard is purely a status predicate
- [x] Idempotency — both cancel paths (revoke, deactivate-a-pending-invite) are now safe under
  concurrent accept; resend was already safe from round 1
- [x] Test is real proof, not just a passing test — verified it fails on the pre-fix commit
- [x] No new entry point, permission, or PII surface in this diff

## Decisions and follow-ups
- Required before merge: none remaining — round 1's finding is closed.
- Accepted risk: none.
- New finding ids in `security/v1-review.md`: none — resolved within review, never shipped.
