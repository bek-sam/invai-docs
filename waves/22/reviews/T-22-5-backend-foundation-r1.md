# Review of T-22-5 (round 1, migrations only)

- Reviewer: backend-foundation on Opus
- Author: backend-engineer on Opus
- Verdict: approve

Scope: migrations only — `invai-backend` `f6725b8` (0034 `vendor_sheet_deliveries`, 0035 TikTok fee 8→6) and `159c7da` (0035 snapshot), plus the `vendors.ts` schema hunk. Not reviewing router/service/job logic, or `orders.ts` (no hunk in this commit range — confirmed by `git diff 08d1eba f6725b8 -- src/db/schema/orders.ts` empty).

## Evidence I re-ran
| Command | Result |
|---|---|
| `docker exec local-postgres-1 createdb -U invai -O invai invai_t22_5m` + `TEST_DATABASE_URL/TEST_MIGRATION_DATABASE_URL=…/invai_t22_5m REDIS_URL=redis://localhost:6379/9 pnpm exec vitest run --reporter=dot src/db` | from-zero migrate through 0035; `Test Files 9 passed, Tests 31 passed` |
| same DB, `vitest run --reporter=dot src/modules/vendors/delivery.test.ts src/modules/finance/tiktok-fee-backfill.test.ts src/db/rls-coverage.test.ts` | `Test Files 3 passed, Tests 17 passed` — RLS coverage sees the new table |
| `vitest run --reporter=dot src/db/fk-coverage.test.ts` (invai_test) | `3 passed` |
| `dropdb -U invai --force invai_t22_5m` | dropped |
| `python3` diff of `drizzle/meta/0034_snapshot.json` vs `0035_snapshot.json` | `tables` and `policies` identical; `0035.prevId == 0034.id` — confirms 0035 is a pure data (`--custom`) migration, no schema drift |

## Checklist
- **company_id + RLS + grants:** `vendor_sheet_deliveries` has `company_id`, `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`, `CREATE POLICY ..._tenant ... TO invai_app USING/WITH CHECK (company_id = current_setting(...))`. No explicit grants needed — `0001_grants_extensions.sql` has `ALTER DEFAULT PRIVILEGES ... GRANT SELECT, INSERT, UPDATE, DELETE ... TO invai_app`, confirmed by tests passing under `invai_app`.
- **Composite FKs (README rule 5):** both `gang_sheet_id` and `vendor_connection_id` use `foreignKey({ columns: [t.companyId, t.col], foreignColumns: [parent.companyId, parent.id] })` against `gangSheets`/`vendorConnections`, both of which already have `tenantKey(...)` unique keys. `company_id` itself is single-column to `companies`, correct per the rule ("references to users and companies stay single-column"). `fk-coverage.test.ts` green.
- **Idempotent delivery key:** `uniqueIndex().on(companyId, gangSheetId, seq)`. Not a single "one row per sheet" key by itself — `seq` increments per attempt (send = 1, resends = 2..). The actual once-per-click guard is `lockSheet`/row-lock serialization in `delivery.ts` (`resendSheetEmail` locks the sheet row before computing `nextSeq`); the unique index is the DB-level backstop against a genuine race producing two rows at the same seq. Verified in `delivery.test.ts` (duplicate enqueue → skipped, one mail; resend inside window → 429).
- **0035 custom, filtered, idempotent:** `pnpm db:generate --custom` inferred from the snapshot chain (tables/policies byte-identical to 0034, only `id`/`prevId` differ). `WHERE cs.fee_tables @> '[{"channel":"tiktok","transactionPct":8}]'` only touches rows still at the old default; after the `jsonb_set` to 6 a second run finds no matching rows (own test runs it twice, 7.5 preserved). No `SET LOCAL lock_timeout` header — a gap already flagged as a general "fold into template" note in memory (T-22-3), not blocking here: `cost_settings` is one row per company (`uniqueIndex().on(t.companyId)`), not one of the big-table names, so the lock window is short.
- **Import ON CONFLICT unique index (company_id, channel, channel_order_id):** already exists (`src/db/schema/orders.ts:127`, pre-existing migration, not part of 0034/0035) — nothing new added here, so no risk of failing on duplicate rows from this change.
- **Journal 0030..0035:** sequential `idx`, strictly increasing `when`, in order in `_journal.json`.
- **Dev DB note:** 0034/0035 already applied to shared `invai` per the card; I did not touch the shared DB, all evidence above is from my own `invai_t22_5m` migrated from zero.

## Blocking findings
None.

## Optional notes
- 0035 could still start with `SET LOCAL lock_timeout = '5s'` for defense in depth on a busier `cost_settings` table later; not required now given the table's shape.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
