# Review of T-1-3 (round 1)

- Reviewer: backend-foundation on Fable
- Author: integrations-engineer on Opus 5.5
- Verdict: **approve**

## Evidence I re-ran
Same clean worktree at `b117997` (parent `293047b`), own DB `invai_test_r13`
(migration applied via `TEST_MIGRATION_DATABASE_URL` as the `invai` owner role, app queries as `invai_app`).

| Command | Result |
|---|---|
| `pnpm test` | `212 passed (212)` (includes a from-scratch migrate of `0001`..`0008` into `invai_test_r13`) |
| `pnpm db:generate --name inventory_po_idempotency --check` (dry run against the committed schema) | no diff — the committed `0008_inventory_po_idempotency.sql` matches what `drizzle-kit` would generate now, so it wasn't hand-edited |
| `docker exec -i local-postgres-1 psql -U invai -d invai_test_r13 -c "\d purchase_orders"` | `submit_attempted_at timestamptz`, nullable, no default — additive, no backfill needed |
| `git diff 293047b b117997 -- drizzle/meta/_journal.json` | one new entry, idx 8, on top of T-1-2's committed 0006/0007 — no journal collision |
| `pnpm typecheck && pnpm lint` | clean |

## Acceptance criteria (migration/foundation angle)
| # | Met? | Evidence |
|---|---|---|
| 3 (new table) | yes | `purchase_order_receipts` follows the module's own conventions exactly: `id()`, `companyId()`, `tenantPolicy(...)`, `.enableRLS()`, snake_case columns, `jsonArray<{lineId, qty}>()` reusing the shared helper rather than a bespoke JSON column. |
| — | yes | `submit_attempted_at` addition to `purchase_orders` is a single nullable column with no default — safe to apply without a lock-heavy rewrite (matches `zero-downtime-migration`'s "additive, nullable" pattern; the table is small so no `CONCURRENTLY`/batching concern applies here). |

## Blocking findings
None on migration soundness, schema conventions, or foundation patterns. I concur with `reviewer`'s and `architect`'s blocking finding on the SanMar/"other" production behavior (`service.ts`, the `if (!adapter)` branch in `submitPo`), but that's a business/contract semantics call outside what I own (schema, migrations, `withTenant`/RLS plumbing) — not duplicating it as my own blocking item. The card can't ship until it clears.

## Checks
- [x] Migration is additive: new table + one nullable column, no data migration, no `db:generate` drift.
- [x] `tenantPolicy()` + `.enableRLS()` on the new table; indexes lead with `company_id`.
- [x] No hand-edited SQL in `0008_inventory_po_idempotency.sql` (confirmed byte-for-byte via dry-run generate).
- [x] No new `withSystem`, no changes to `db/client.ts`, `env.ts`, or other foundation-owned files.
- [x] Seed unaffected (no seed changes in this diff; ran the full suite which exercises `withSystem`-seeded fixtures without error).

## Optional notes (not blocking)
- `env.mocks.supplier` / `SS_ACTIVEWEAR_*` in `src/env.ts` are now dead per the author's own report — I'll pick up removing them (and the matching `.env.example`/runbook rows) in a follow-up card rather than block this one on it, since they're inert, not harmful.
