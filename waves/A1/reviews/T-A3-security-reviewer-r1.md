Verdict: approve

# Review T-A3 r1 (security co-review — tenancy). Reviewer: security-reviewer (sonnet). Author: backend-engineer (finance, opus). 2026-09-30
Scope: invai-backend 95e9d69 1afdfc3 31db7f3 8c616ef only.

## Evidence I re-ran (own DB `invai_sec_a1_test`, `REDIS_URL=redis://localhost:6379/14`)
- `vitest run src/modules/analytics/ src/modules/shipping/zone.test.ts src/api/authz.test.ts src/db/rls-coverage.test.ts src/db/rls.test.ts` → 7 files, 63/63 passed (covers both T-A3 and T-A4's tests together, no cross-card interference).
- `authz.test.ts` uses `listProcedures(contract)`, so all 7 `analytics.*` procedures (incl. T-A4's `operations`) are walked automatically as anonymous, no-permission, floor, station and vendor — no hardcoded list to go stale.
- Contract check: `invai-contracts/src/contract/analytics.ts` — all 7 procedures declare `proc("finance.read")`, default `auth: user` (never floor/station), matching the module doc comment.
- `router.ts` read: all 6 T-A3 handlers call `withTenant(tenant.companyId, ...)`; no `withSystem` anywhere in the diff.
- `finance-service.ts` `sql.raw` usage (grep): only on `BUCKET_COLUMNS` (fixed 9-entry constant array of column names) for the cost-line bridge selects, and on fixed literal strings (`"b_${k}"`). No user input reaches `sql.raw`. `groupBy`/`by` inputs branch through if/else into hardcoded SQL, never interpolated as raw identifiers.
- Cleanup: test DB dropped, Redis DB 14 flushed.

## Flags checked
- **tenancy**: pass. Confirmed above.
- **money**: not my flag, but noted clean (integer cents, `pgRound`).

## Blocking findings
none

## Optional notes (not blocking)
- None beyond what the primary reviewer already recorded (breakEven/SQL v2, zone follow-up, testkit path).
