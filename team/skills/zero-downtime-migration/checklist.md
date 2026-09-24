# Migration safety checklist

Postgres 17. "Big table" = anything expected over ~100k rows at pilot scale, and always: `orders`, `order_items`, `order_item_transitions`, `outbox_events`, `audit_log`, `scans`, `inventory_movements`, `ai_jobs`, `buyer_pii`, `shipments`, `labels`. Confirm table names in `src/db/schema/*.ts` before use.

| Change | Safe as one step? | Safe way |
|---|---|---|
| Create a new table | Yes | `add-tenant-table` |
| Add a nullable column, no default | Yes | Plain migration |
| Add a column with a constant default | Yes (PG 11+ doesn't rewrite) | Plain migration. A volatile default (`now()`, `gen_random_uuid()`) rewrites: add nullable, backfill, then set default |
| Add `NOT NULL` to an existing column | **No** | `ADD CONSTRAINT x CHECK (col IS NOT NULL) NOT VALID` → backfill → `VALIDATE CONSTRAINT x` → `SET NOT NULL` (uses the validated check, no scan) → drop the check |
| Add a foreign key | **No** on big tables | `ADD CONSTRAINT ... NOT VALID`, then `VALIDATE CONSTRAINT` in a later migration |
| Add a unique constraint | **No** on big tables | `CREATE UNIQUE INDEX CONCURRENTLY` (online path), then `ADD CONSTRAINT ... UNIQUE USING INDEX` |
| Add an index | Only on small tables | Big tables: `CREATE INDEX CONCURRENTLY IF NOT EXISTS` in `drizzle/online/` (to be created) |
| Drop an index | **No** on hot tables | `DROP INDEX CONCURRENTLY` (online path) |
| Rename a column or table | **No** | New column → dual-write → backfill → switch reads → drop old later |
| Change a column type | **No** | Same as rename. Never `ALTER COLUMN TYPE` on a live table |
| Drop a column | Only after code stopped using it | Remove all reads and writes (grep), deploy, wait one deploy cycle, then drop |
| Change an `enumText` value set | Yes in the DB (it's text) | But the contract enum change follows `contract-deprecation`; old rows keep old values until backfilled |
| Change an RLS policy | Careful | `EXPLAIN (ANALYZE, BUFFERS)` at 1,000 tenants; security-reviewer co-reviews |
| Data fix touching many rows | **No** in a migration | Backfill job on the `reports` queue |

## Hand-written migration header

```sql
SET LOCAL lock_timeout = '5s';--> statement-breakpoint
ALTER TABLE "order_items" ADD CONSTRAINT "order_items_blank_fk" FOREIGN KEY ("company_id", "blank_variant_id")
  REFERENCES "blank_variants" ("company_id", "id") NOT VALID;
```

drizzle splits statements on `--> statement-breakpoint`; keep that marker between statements, as the generated files do.

## Backfill job skeleton

```ts
export const backfillX = defineJob({
  queue: "reports",
  name: "<area>.backfillX",
  input: z.object({ companyId: z.uuid(), afterId: z.uuid().nullish() }),
  jobId: (i) => `backfill-x-${i.companyId}-${i.afterId ?? "start"}`,
  handler: async ({ companyId, afterId }) => {
    const last = await withTenant(companyId, (tx) => fillBatch(tx, afterId ?? null, 2_000)); // returns last id or null
    if (last) await backfillX.enqueue({ companyId, afterId: last }, { delay: 200 });
  },
});
```

`fillBatch` updates only rows still needing it (`where new_col is null and id > $after order by id limit $n`), so a rerun is harmless.

## Review questions
- Does the old code still run against the new schema? Does the new code run against the old schema (for the minutes between migrate and deploy)?
- Which locks does each statement take, and on which table? Is any table in the list above?
- Is there a statement that scans or rewrites a big table?
- Is the drizzle schema in sync, so the next `db:generate` produces nothing unexpected?
