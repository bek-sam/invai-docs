Verdict: approve

Reviewer: backend-foundation on Sonnet 5 (co-review, migration risk flag)
Author: backend-engineer (finance) on Opus 5.5
Scope: migration `0036_finance_fixed_monthly_cents` only (commit 95e9d69), `src/db/schema/finance.ts`.

## Checks
- Generated, not hand-edited: `drizzle/0036_finance_fixed_monthly_cents.sql` is a single `ALTER TABLE "cost_settings" ADD COLUMN "fixed_monthly_cents" integer;` — matches `db:generate` output shape exactly (no stray SQL).
- Journal order: `meta/_journal.json` idx 36 (`0036_finance_fixed_monthly_cents`), idx 37 (T-A4's `0037_shipping_dest_zone`) — sequential, no collision.
- Additive only: nullable `integer()` column, no default, no rewrite, no lock risk. `ALTER TABLE ... ADD COLUMN` with no default takes only a brief metadata lock (no table rewrite) — safe as-is, `SET LOCAL lock_timeout` not required for a change this small (same precedent as prior single-column-add migrations in this repo).
- Schema type matches contract: money is `integer` cents per `CLAUDE.md` convention — correct for `fixedMonthlyCents`.
- RLS unaffected: existing table, existing `tenantPolicy("cost_settings")` untouched.
- Zero-downtime: old code (unaware of the column) runs unchanged against the new schema; new code treats `null` as "not set" per AC-A6. Expand-only, no contract phase needed.

## Applied to scratch DB
`invai_mig_a1_test`, migrated with `MIGRATION_DATABASE_URL`/`DATABASE_URL` pinned and `REDIS_URL=redis://localhost:6379/13`. `\d cost_settings` shows `fixed_monthly_cents | integer | (nullable, no default)`, policy `cost_settings_tenant` present and unchanged. `drizzle-kit generate` against the migrated DB reported "No schema changes, nothing to migrate" — schema.ts and applied SQL match exactly, no drift. DB dropped after.

## Verdict
approve. No blocking findings.
