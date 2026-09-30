Verdict: approve

# Review T-A5 r1 (security co-review — tenancy). Reviewer: security-reviewer (sonnet). Author: backend-engineer (inventory, opus). 2026-09-30
Scope: invai-backend 85fa715 6b531c2 b5ea7d0 only.

## Evidence I re-ran (own DB `invai_sec_a5_test`, app role `invai_app`, migration role `invai`, `REDIS_URL=redis://localhost:6379/14`)
- `vitest run src/api/authz.test.ts src/db/rls-coverage.test.ts src/modules/analytics/inventory-service.test.ts src/modules/analytics/design-service.test.ts src/modules/analytics/export-service.test.ts` → 5 files, 50/50 passed.
- `authz.test.ts` walks all `analytics.*` procedures via `listProcedures(contract)`; contract check confirms `inventoryHealth`, `supplierTrends`, `designLifecycle`, `export` all declare `proc("finance.read")`, `auth: user` (never floor/station).
- `router.ts` diff: all 4 new handlers call `withTenant(tenant.companyId, ...)`. `grep -n "sql\.raw\|withSystem" ` across `inventory-service.ts design-service.ts export-service.ts router.ts reorder.ts inventory/service.ts` → no hits (no `withSystem`, no `sql.raw` anywhere in the diff).
- `inventory-service.ts`/`design-service.ts`: every query is a tagged `sql` template (parameterized), every CTE/join filters `company_id = ${ctx.companyId}` explicitly, including the size-mix, stockout, supplier-trends and design-lifecycle joins across `order_items`/`orders`/`blank_variants`/`purchase_orders`/`designs`/`listings`.
- Market-module call (`design-service.ts`): `getTrendSignal` is called as `tx.transaction((sp) => getTrendSignal(sp, ctx, {designId}))` — a savepoint, matching the brief; a failure is caught, logged (`analytics.design`, companyId, designId, no PII), and returns `null`, so it degrades gracefully instead of leaking or aborting the outer transaction. `getTrendSignal` itself filters `company_id` throughout (`market/service.ts`).
- `reorderSuggestions`/`splitLinesBySizeCurve` (`inventory/service.ts`, under the 2026-09-30 02:05 grant): pure arithmetic over `views`/`live` already built from the tenant-scoped `suppliersStock`/stock-view queries earlier in the same function; no new query, no cross-tenant read introduced.
- `analytics.export` (`export-service.ts`): writes via `objectKey(ctx.companyId, "analytics-export", "csv")` — company-prefixed key, same pattern as `finance.exportProfitCsv`. Download only via `files.downloadUrl` (`files/service.ts`), which checks `fileKey.startsWith(ctx.companyId/)` (`isSafeKey`+prefix, equivalent to `isCompanyKey`) before presigning — cross-tenant key guess still returns `NOT_FOUND`.
- CSV formula-injection guard: shared `toCsv`/`neutralizeFormula` (`lib/csv.ts`) applied to all export rows, incl. this card's new `inventoryHealth`/`supplierTrends`/`designLifecycle` views — leading `=+-@`/tab/CR text cells get a leading `'`.
- Buyer PII: reviewed every response field and every CSV header (`inventoryHealth`, `supplierTrends`, `designLifecycle`, and the `export` sheet builder for all 10 views) — only ids, style/supplier/design labels and money/date numbers; no buyer name, email, address or personalization text anywhere.
- Cleanup: `invai_sec_a5_test` dropped, Redis DB 14 flushed.

## Flags checked
- **tenancy**: pass. Confirmed above (withTenant, company_id filters, savepoint isolation, S3 key prefixing, no withSystem).

## Blocking findings
none

## Optional notes (not blocking)
- None beyond what the primary reviewer already tracks (export CSV column choices for T-A3/T-A4 views not yet checked against a finished screen design — noted in the author's own report, not a security concern).
