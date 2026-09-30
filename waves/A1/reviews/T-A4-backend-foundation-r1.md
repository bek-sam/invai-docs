Verdict: approve

Reviewer: backend-foundation on Sonnet 5 (co-review, migration risk flag)
Author: backend-engineer (production, shipping) on Opus 5.5
Scope: migration `0037_shipping_dest_zone` only (commit efdc193), `src/db/schema/shipping.ts`.

## Checks
- Generated, not hand-edited: `drizzle/0037_shipping_dest_zone.sql` is a single `ALTER TABLE "shipments" ADD COLUMN "dest_zone" smallint;` — matches `db:generate` output shape.
- Journal order: idx 37, `prevId` chains after T-A3's idx 36 — lands second as the card requires, no collision to regenerate.
- Additive only: nullable `smallint()`, no default, no rewrite. `shipments` is a growing table but a no-default `ADD COLUMN` is metadata-only in PG ≥ 11, so no `lock_timeout` guard needed (same precedent as other single-column adds in this repo, e.g. 0036).
- Type: `smallint` for a 1-9 zone value is correct and minimal; the card leaves the choice between an app-level bound vs a CHECK constraint open — no CHECK was added. Acceptable: zone is set exclusively by the pure `zone.ts` function at label-buy time, never from user input, so app-level bounding is enough here; a CHECK would be defense-in-depth but its absence isn't a migration-safety issue. Noting as an optional follow-up, not blocking.
- RLS unaffected: existing table, existing `shipments_tenant` policy untouched.
- No new PII/address column: confirmed by inspecting the full `\d shipments` column list — only `dest_zone smallint` was added, no zip/address/name column exists on this table.
- Zero-downtime: old code ignores the new column; new code (label-buy path) writes it. Expand-only, old and new code both run fine on this schema.

## Applied to scratch DB
`invai_mig_a1_test`, same run as T-A3 (migrations apply in one transaction, 0036 then 0037). `\d shipments` shows `dest_zone | smallint | (nullable, no default)` at the end of the column list, policy `shipments_tenant` present and unchanged, FKs and indexes all pre-existing. `drizzle-kit generate` reported "No schema changes, nothing to migrate" — no drift between schema.ts and applied SQL. DB dropped after.

## Verdict
approve. No blocking findings.
