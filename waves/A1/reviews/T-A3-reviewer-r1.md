Verdict: approve
# Review T-A3 r1 (finance analytics + fixed_monthly_cents). Reviewer: reviewer (opus). Author: backend-engineer (finance, opus). 2026-09-30
Scope: invai-backend 95e9d69, 1afdfc3, 31db7f3 only (T-A4 commits and T-A1's uncommitted `src/db/seed/**` excluded).

## Evidence I re-ran (own DB `invai_rv3_test`, `REDIS_URL=redis://localhost:6379/12`)
- `pnpm typecheck` → tsc clean. `pnpm lint` → "Checked 434 files … No fixes applied."
- `vitest run src/modules/analytics/finance-*.test.ts src/modules/finance/ src/modules/digest/ src/api/authz.test.ts src/db/rls-coverage.test.ts` → 17 files passed, 1 skipped; 139 passed, 2 skipped, 1 todo.
- Verbose rerun of `finance-*.test.ts` + `authz.test.ts` → 3 files, 26/26 passed; parity suite ran (not skipped): all 6 metric SQL files matched.
- getProfit unchanged (AC-G1): scratch script called `getProfit` at base 9228343 (archive) and at HEAD on the dev DB, 2 periods x 5 dimensions x {all, etsy}, sort key → the two JSON outputs are byte-identical (366,201 bytes, `cmp` equal).
- Live, in-process on dev data (desert bloom, week 09-21..09-28): unitEconomics cm3 158823 = getProfit net 158823; bridge 25865 + 6801 = 32666; breakEven 86 orders, 136 to break even, pace 369; shippingMargin 59 labeled, 33 free-shipping counted. The same call under another shop's tenant with A's ctx → all zeros (RLS plus explicit company_id).
- Migration: 0036 is one nullable `ADD COLUMN integer`; applied in the test DB (`integer`, nullable); 0037 (T-A4) snapshot carries it, so the journal is in sequence.
- `scan-test-weakening.sh invai-backend 9228343` → 0 assertions removed. Hits: the `vi.mock("./shared")` pass-through spy (it wraps a helper for the AC-G1 call-count proof; the units under test run for real, so OK), and T-A4's carriers mock (not this card). The dropped "other five are NOT_IMPLEMENTED" test was T-A3's own and is obsolete now that T-A4 registered `operations`.
- Cleanup: test DB dropped, Redis DB 12 flushed (0 clients), base archive removed. No API started.

## Acceptance criteria
- AC-A1 met: test plus live cm3 = net; parity test vs contribution_margin.sql per channel.
- AC-A2 met: test (cm2 −1635, labelCost largest; positive orders absent); parity vs losing_orders.sql.
- AC-A3 met: parity vs shipping_margin.sql; free-shipping orders counted (live 33).
- AC-A5 met: volume + rate = total (test and live); top design = SQL rank 1 (parity).
- AC-A6 met, with a disclosed deviation (note 1): `fixedCostsSet:false` → nulls; $2,500 → matches break_even.sql when no refund falls in the window.
- AC-A7 met: 3 orders without a profit line are counted in leakage and unitEconomics (test; live 3).
- AC-G1 met (whole-shop half): one `computeNet`; spy called twice with the same period; byte-identical getProfit output.
- AC-E4/E5 met: cross-tenant test, my live probe, and designer/presser FORBIDDEN on all 6 through the router; authz.test green.

## Checklist
- Tenancy: all 6 handlers use `withTenant`; no `withSystem`; every query also filters `company_id` or relies on RLS joins (leakage `exists`, reprints join). No new table.
- SQL: every value is a bound drizzle param. `sql.raw` is used only on constant column names and flags. `limit` is bounded by Zod (≤500 and ≤50).
- Money: integer cents; per-order values use `pgRound`. No PII read or logged. No jobs, webhooks or side effects. The fixed-cost-only PATCH emits no recompute (router test, run twice).
- Ownership: all paths are T-A3's per card and wave.md (see note 3).

## Blocking findings
none

## Optional notes (non-blocking)
1. finance-service.ts:645 breakEven uses `computeNet` Net (refunds dated in the window), while break_even.sql v1 sums `net_cents` only, so the two differ by in-window refund net. The SQL's own comment says "the Profit page's Net / orders", so the code follows the intent. data-analyst: publish break_even.sql v2 before the gate's parity sign-off.
2. finance-service.ts:414-425 `groupBy: "zone"` still reports every shipment as without a zone, although T-A4's `dest_zone` has landed (d256a78). The code is honest (it makes no rows up), but it needs a follow-up card before T-A6 shows zone rows.
3. `analytics/finance-testkit.ts` (test helper) is not in the card's literal list but matches wave.md's `finance*.ts` split for T-A3. Tech lead: acknowledge it.
4. The dev DB still has desert bloom `fixed_monthly_cents = 250000` from the author's live run; T-A1's reseed resets it.
