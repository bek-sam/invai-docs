Verdict: changes-required
# Review T-A4 r1: reviewer (opus 5.5), author backend-engineer (opus). Commits efdc193 d256a78 6a5791c 2dce8f3 (invai-backend)

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint` | tsc clean; biome 434 files, no fixes |
| `vitest run` operations-service.test.ts, src/modules/shipping/, src/api/authz.test.ts, src/db/rls-coverage.test.ts (DB `invai_rv4_test`, Redis 13) | 14 files, 124/124 passed |
| `vitest run operations-service.test.ts` x6 | **2 of 6 runs FAIL** "reprint cost by reason, station and vendor": byVendor order flips (finding 1). Parity block ran (not skipped) |
| `scan-test-weakening.sh invai-backend 9228343` | removed=0 added=258; hits = `vi.mock("../../integrations/carriers")` (collaborator, not unit under test) and T-A3's `./shared` mock: OK |
| psql dev DB (read-only) | `shipments` has `dest_zone` only (no zip/addr/name column); 1 labeled row, zone 7; 38 migrations applied |
| 0036 vs 0037 snapshot diff | only `dest_zone smallint` added; SQL = one nullable `ADD COLUMN` |
Live analytics curl not re-run: tech lead's :3151 evidence (owner 200, designer 403 finance.read) accepted; no API started. Test DB dropped, Redis 13 flushed.

## Blocking findings
1. **Medium, flaky test / nondeterministic output** `src/modules/analytics/operations-service.ts:141` sorts cuts by `cost desc, reprints desc` only; the reprint query (l.102-121) has no ORDER BY, so tied rows come back in heap order. The test at `operations-service.test.ts:269-273` expects `Vendor A` before `unknown` (both 500 c / 1 reprint) and fails ~1 run in 3 (seen 2/6). Scenario: the A1 gate's full suite goes red on this file at random; on screen, tied rows swap on each refresh. Fix: add a deterministic tiebreak (e.g. `|| a.key.localeCompare(b.key)`, also for film-waste byVendor l.179) and assert that order, or compare order-insensitively.

## Acceptance criteria
- AC-A4: met. zone.ts pure; zone computed from in-memory ZIPs in Tx 2 (service.ts:925) and written only in `recordLabel`; double buy -> 1 carrier call, zone 8; military -> null; exact column-list test plus regex guard (zone.test.ts:236-245). Rebuy after void rewrites the zone, which is correct.
- AC-B1: met. Reprint/film SQL matches `reprint_cost.sql`/`film_waste_cost.sql` term by term (per-row int terms, same sent-state list); parity tests pass against the real docs SQL.
- AC-B2: met. median null below 100 timed units (contract "not enough scans yet"); suggestion = |median-setting|/setting > 0.25. Boundary untested (non-blocking note a).
- AC-B3: met. latePct null under 30 per cut; group-name labels; test asserts no /caus/ in the whole response.
- AC-B/C-screen1: met. `hasEnoughHistory` false only when every metric is below its minimum; per-metric nulls kept.
- AC-E4/E5: met. every query filters `company_id` inside `withTenant`; A/B test; designer/presser/packer/receiver FORBIDDEN finance.read; authz walk green.

## Scope, ownership, decisions
- Shipping edits: zone.ts(+test), the buy path (import, zone line, `recordLabel` param + set) and one `toShipment` line. The `destZone` mapping is needed for the approved contract field `Shipment.destZone` (else the API never shows the zone AC-A4 asks for): accepted.
- Router diff adds only `operations` + import; T-A3 registrations untouched. Seed tree edits ignored.
- Waits exclude still-waiting items from median/p90: matches contract `StageWait.stillWaiting` text; SQL doc differs (measures to now()) -> data-analyst to align the SQL. Accepted.
- Film waste ignores `channel`: sheets mix channels, no honest attribution; tested and commented. Accepted; T-A7 should label that block as all channels.

## Optional notes (non-blocking)
a. No test pins the 25 % boundary (a LABOR_GAP of 0.4 would still pass). b. Parity block `describe.skipIf(!haveSql)` silently skips in a lone backend CI checkout. c. `hasEnoughHistory` can turn true after one busy import day (30 `needs_mapping` entries); fine per AC wording.

## Checklist
tenancy ok (withTenant, no new withSystem outside tests, no new table) | idempotency ok (buy unchanged, zone in Tx 2) | cents ok | no PII stored/logged | Zod via contract | migration additive nullable | mock carrier path still works | contract additive.
