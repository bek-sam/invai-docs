Verdict: approve

# Review T-A4 r1 (security co-review — tenancy + PII). Reviewer: security-reviewer (sonnet). Author: backend-engineer (production, shipping, opus). 2026-09-30
Scope: invai-backend efdc193 d256a78 6a5791c 2dce8f3 2e564af only.

## Evidence I re-ran (own DB `invai_sec_a1_test`, `REDIS_URL=redis://localhost:6379/14`)
- `vitest run src/modules/analytics/ src/modules/shipping/zone.test.ts src/api/authz.test.ts src/db/rls-coverage.test.ts src/db/rls.test.ts` → 7 files, 63/63 passed.
- `vitest run src/modules/analytics/operations-service.test.ts` x6 (round-2 fix `2e564af`): **16/16 passed every run**, no flakes — confirms the primary reviewer's r1 blocking finding (nondeterministic tiebreak in sorted cuts) is fixed. Read the fix directly: `operations-service.ts:141-142` `cut()` sort now ends `|| a.key.localeCompare(b.key)`; film-waste `byVendor` SQL `order by waste desc, coalesce(g.vendor_connection_id::text, '')` (~l.181); `pressMinutes` SQL `order by 2, 1` (~l.284). All three spots the reviewer flagged checking are fixed.
- `analytics.operations` (`router.ts`) calls `withTenant(tenant.companyId, ...)`; no `withSystem`. Every join in `operations-service.ts` filters `company_id` explicitly (grep: 15+ hits) in addition to RLS — belt and suspenders on the same tenant across reprints, film waste, waits, press minutes and late drivers.
- `operations-service.ts`: no `sql.raw` at all; every dynamic filter (`channel`) is a bound param inside a conditional `sql` fragment.
- **PII/schema check (AC-A4, the PII flag)**: `git show d256a78 -- src/db/schema/shipping.ts` — the only change is `destZone: smallint()`, with a comment stating the ZIP is read in memory only. `git show efdc193` migration `0037_shipping_dest_zone.sql` is exactly `ALTER TABLE "shipments" ADD COLUMN "dest_zone" smallint;` — one nullable column, nothing else.
- `zone.test.ts:236-245` "shipments has exactly the expected columns": queries `information_schema.columns`, asserts `cols.sort()` **equals** (not just contains) a fixed `SHIPMENT_COLUMNS` list (equality, not containment — the S-34 pattern), plus a regex guard for `zip|addr|street|city|name|phone|email`. Ran it myself (green, above).
- `shipping/service.ts` diff (`d256a78`): `buyLabel` computes `zoneForZips(plan.req.from.zip, plan.req.to.zip)` from ZIPs already held in memory for the label purchase, passes only the resulting zone number (`destZone: number | null`) into `recordLabel`, which writes it to `shipments.destZone` in Tx 2. No new persistence of ZIP/address/name; `toShipment` maps `destZone` straight through, no PII field added to the API output.
- `zone.ts` is a pure function (ZIP3 centroid table → haversine-ish distance bands → zone 1-9), no I/O, no logging.
- Migration sequencing: 0037 applied cleanly after T-A3's 0036 (journal in order), confirmed via `pnpm db:migrate` idempotent-up-to-date per the author's report and my own `psql \d shipments` read showing `dest_zone smallint` present with no other new column.
- Cleanup: test DB dropped, Redis DB 14 flushed.

## Acceptance criteria (my flags only)
- AC-A4 met: zone 1-9 only, exact-column-list test (equality), zone computed in memory, no ZIP/address/name column — verified directly in code and by running the test.
- AC-E4/E5 met: `withTenant` on the only new handler, explicit `company_id` on every query, `authz.test.ts` (`listProcedures`) walks `operations` automatically — verified.

## Blocking findings
none

## Optional notes (not blocking)
- `finance-service.ts` `shippingMargin` groupBy zone (T-A3's file) now reads the real `dest_zone` as of `8c616ef`, so the T-A3 review's note 2 is closed on T-A4's side.
