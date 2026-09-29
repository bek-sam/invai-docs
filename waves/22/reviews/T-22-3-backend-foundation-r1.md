# Review of T-22-3 (round 1) — migration only (backend-foundation co-review)
Reviewer: backend-foundation on Opus. Author: integrations-engineer on opus.
Scope: `invai-backend` 044c3af — `drizzle/0032_shipping_scan_forms.sql`, `scan_forms`/`address_verifications` in `schema/shipping.ts`.
**Verdict: approve**

## Evidence
- `git show 044c3af --stat`: migration + snapshot + journal + schema hunk only.
- `_journal.json`: entries 30, 31, 32 (`shipping_scan_forms`), 33 strictly in order.
- Own DB `invai_t22_3m`, Redis DB 9, 0001→0033 migrated from zero, `vitest run --reporter=dot src/db`: `Test Files 9 passed (9)`, `Tests 31 passed (31)`, incl. `fk-coverage.test.ts` + `rls-coverage.test.ts` green.
- `dropdb invai_t22_3m`; `redis-cli -n 9 flushdb`: cleaned up.

## Checklist
- company_id/RLS/grants: both `.enableRLS()` + `tenantPolicy`; migration has `ENABLE ROW LEVEL SECURITY` + `USING/WITH CHECK`; no explicit GRANT needed (0001's `ALTER DEFAULT PRIVILEGES` covers it).
- Composite FKs: `address_verifications`→`orders` is `(company_id, order_id)→orders(company_id, id)`, correct. `scan_forms.shipmentIds` is an array, no FK possible (same as existing `shipments.orderItemIds`), not a regression. FK to `companies` single-column is allowed (rule 5). `fk-coverage.test.ts` passed.
- Idempotency: `uniqueIndex(companyId, carrier, date)` on `scan_forms` = one form per carrier+date+shop.
- Expand-only: pure `CREATE TABLE` + new FKs/indexes/policy on the new tables; no existing column touched.
- Missing `SET LOCAL lock_timeout`: absent, doesn't block. `checklist.md` treats "create a new table" as safe-as-one-step, unlike "add FK to an existing big table"; the new FK validates against an empty table (instant), and every other new-table migration here (0026–0029, 0033) also omits the guard. Small residual lock-queue risk against `orders`/`companies` under contention — noted, not blocking.
- Snapshot/journal: `0032_snapshot.json` columns match schema exactly; clean migrate from zero passed.

## Blocking findings
None.
## Optional notes
Make `SET LOCAL lock_timeout` a default header for new-table migrations FK'd to a hot parent, so a contended lock fails fast. Propose folding into `add-tenant-table`.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
