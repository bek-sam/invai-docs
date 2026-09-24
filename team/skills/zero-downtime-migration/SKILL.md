---
name: zero-downtime-migration
description: Change the invai-backend Postgres schema on a live database without locking hot tables or breaking running code - expand, backfill in a job, switch, contract across separate deploys, with lock_timeout and concurrent indexes outside drizzle's single migration transaction. Use for "migration", "add column", "rename column", "backfill", "add index", "NOT NULL", "change type".
---

# Zero-downtime migration

A schema change that never blocks order intake, scans or label buys, and that works with both the old and the
new code running at once.

## When to use
- Any change to `src/db/schema/**` that alters an existing table: add, rename or drop a column, change a type,
  add NOT NULL or a constraint, add an index, backfill data.
- A brand-new table is simple expand; follow `add-tenant-table` and only the "expand" part here.
- Owners: backend-foundation (tooling, co-reviews every migration), backend-engineer (its module's schema
  file).

## Facts that shape this
- `pnpm db:migrate` runs `src/db/migrate.ts`, which calls drizzle's `migrate()`. drizzle applies **all pending
  migrations in one transaction** (`node_modules/drizzle-orm/pg-core/dialect.js`, `session.transaction`). So
  every lock is held until the last statement, and `CREATE INDEX CONCURRENTLY` fails there.
- `invai-infra/.github/workflows/deploy.yml` has no migration step yet (research 11 G3, backlog B-03). Until
  platform-sre adds one, migrations in AWS are a manual owner step: never assume they ran.
- No DB timeouts are set on any role yet (research 11 G6, backlog B-16).
- API and floor clients may be one version behind for hours, and old API tasks keep running during a rolling
  deploy.

## Steps
1. **Classify** each statement with `checklist.md` (this folder). Anything in the "dangerous" column must be
   split into phases.
2. **Plan the phases in the card**, one deploy each:
   1. **Expand:** add the nullable column, the new table, or the new index. Old code must still work.
   2. **Dual-write:** code writes both old and new shapes, still reads the old one.
   3. **Backfill** in a job (step 5).
   4. **Switch:** code reads the new shape. Enforce the constraint now (`NOT VALID` then `VALIDATE`).
   5. **Contract:** drop the old column or table in a later wave, after one full deploy cycle, once grep shows
      no code uses it.
3. **Generate each phase's migration** from the schema file: `pnpm db:generate --name <area>_<change>`. For
   SQL drizzle can't express (constraints `NOT VALID`, `VALIDATE`, data fixes), use a custom migration: `pnpm db:generate --custom --name <area>_<change>` and write the SQL in the generated file before anyone applies
   it.
4. **Start every hand-written migration with the lock guard:**
   ```sql
   SET LOCAL lock_timeout = '5s';--> statement-breakpoint
   ```
   `SET LOCAL` works because drizzle wraps the run in one transaction. On a timeout the whole run rolls back;
   retry it later, don't raise the timeout.
5. **Backfill in a job, never in the migration.** A `defineJob` on the `reports` queue (`src/lib/queues.ts`)
   that:
   - updates 1,000–5,000 rows per transaction, keyed by primary-key range (`where id > $last order by id limit N`);
   - is restartable: it skips rows already done (`where new_col is null`) and stores its cursor in the job
     data or a row;
   - sleeps between batches, and runs per tenant inside `withTenant`, or reads a list of ids with `withSystem`
     and then works per tenant (research 11 §2.1);
   - has a run-twice test (`idempotent-job`).
6. **Indexes on big tables** (`orders`, `order_items`, `outbox_events`, `audit_log`, `scans`,
   `inventory_movements` and anything expected over ~100k rows) need `CREATE INDEX CONCURRENTLY`. That can't
   run inside the drizzle transaction, so:
   - put the statement in `drizzle/online/NNNN_<name>.sql` (to be created), one statement per file, with `IF NOT EXISTS`;
   - run it with the online runner `src/db/migrate-online.ts` (to be created by backend-foundation): outside a
     transaction, one statement at a time, recorded in an `online_migrations` table (to be created);
   - until the runner exists, a new index on a big table goes to the tech lead and is not merged as a plain
     drizzle migration. On small or new tables a normal `CREATE INDEX` in the drizzle migration is fine.
   - Keep the drizzle schema in sync (declare the index in the table extras) so `db:generate` doesn't try to
     create it again. Check the next `db:generate` output is empty for it.
7. **Test the upgrade path** on a copy with data, not just an empty DB: `pnpm db:reset && pnpm db:migrate && pnpm db:seed` on the previous commit, then check out your change and run `pnpm db:migrate` again, then the
   test suite and the API golden path. Don't reset the shared dev DB while other agents are running; use a
   scratch database.
8. **Write the rollback** for each phase in the card: expand phases roll back by deploying the previous code
   (the extra column is harmless); contract phases can't roll back, which is why they come last.

## Rules (MUST / MUST NOT)
- MUST NOT hand-edit a migration that has been applied anywhere. Fix forward with a new one.
- MUST NOT rename or retype a column in place, drop a column still read by deployed code, or add `NOT NULL` to
  a populated column without a validated check first.
- MUST NOT backfill inside a migration file or hold a transaction open across batches.
- MUST add FKs and checks on big tables as `NOT VALID`, then `VALIDATE CONSTRAINT` in a later migration.
- MUST keep `company_id` leading in every new index, and keep RLS on (`add-tenant-table`).
- MUST get backend-foundation as co-reviewer for every migration.

## Done when
- Each phase has its own migration and deploy, listed in the card with its rollback.
- Every hand-written migration starts with `SET LOCAL lock_timeout`; big-table indexes are `CONCURRENTLY`
  through the online path.
- The backfill job exists, is restartable and has a run-twice test.
- Upgrade from the previous commit with seeded data passes, and `pnpm typecheck && pnpm lint && pnpm test`
  plus the API golden path are green.

## References
- `checklist.md` (this folder)
- `invai-docs/research/11-platform-scale-playbook.md` §4.1, §2.2 (role timeouts), §10 G3, G6
- `invai-backend/src/db/migrate.ts`, `drizzle.config.ts`, `drizzle/`
- `CLAUDE.md` ("Migrations"); `invai-docs/waves/backlog.md` B-03, B-16
- Related: `add-tenant-table`, `idempotent-job`, `release-checklist`
