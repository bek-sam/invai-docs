# Review of T-4-1 (round 1): backend-foundation co-review (migrations 0015 and 0016, `floor_requests`, the grants into orders)

- Reviewer: backend-foundation co-review, run by the reviewer agent on Claude Opus 5.5
- Author: backend-engineer (production) on Claude Opus 5.5
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| backend `tsc --noEmit` / `biome check .` / `tsup` at `bdffe6f` | exit 0 / clean / success |
| `vitest run` (full suite, fresh `invai_test_r41` created and migrated by global-setup) | 63 files, 447 passed, including `src/db/rls-coverage.test.ts` and `src/api/authz.test.ts` |
| `tsx src/db/migrate.ts` on `invai_r41_copy` (a copy of `invai`, which the author had already migrated) | "up to date" |
| `\d floor_requests` on the copy | the columns match `0016`; `relrowsecurity = t` |
| `pg_policy` on `floor_requests` | `floor_requests_tenant`, FOR ALL, `company_id = nullif(current_setting('app.company_id', true), '')::uuid` |
| as `invai_app`: no tenant / another tenant / own tenant / insert with another `company_id` | 0 rows / 0 rows / 3 rows / "new row violates row-level security policy" |
| live replay and conflict (see `T-4-1-reviewer-r1.md`) | 1 row per key; `CONFLICT` for another order or reason; refusals store nothing |

## Migrations
- **0015** `ALTER TABLE "orders" ADD COLUMN "pack_override" jsonb;`:
  - The column is nullable with no default, so there's no rewrite (checklist: "Yes, plain migration"). It's an expand-only change: old code ignores the column.
  - Rollback: deploy the previous code; the column is harmless.
  - The `stations.kind` change for `receiving` is `enumText` (plain `text`). `db:generate` produced no SQL, which is correct.
- **0016** `floor_requests`:
  - A new empty table, so a plain `CREATE INDEX` is fine.
  - The FK to `orders` validates against an empty child, so the check is instant. It takes a brief `SHARE ROW EXCLUSIVE` lock on `orders`.
  - Zero-downtime OK.
- Neither file has `SET LOCAL lock_timeout`. The rule applies to hand-written migrations, and these are generated. No migration in the repo sets it, and role-level `lock_timeout` is still a target. Non-blocking; see note 1.
- The journal and snapshots are consistent: idx 15 and 16, and the suite's fresh migrate from 0000 passed.

## `floor_requests` design
- **Tenancy:**
  - `company_id` NOT NULL, FK to companies with cascade;
  - `tenantPolicy`, `.enableRLS()` and the policy in the same migration;
  - indexes lead with `company_id`: a unique `(company_id, kind, idempotency_key)` and `(company_id, order_id)`.
- **Key scope:**
  - The key is per tenant and per kind. The lookup (`floor.ts:1025`) filters kind and key, and RLS adds the company. So two shops can't collide on a key, and a later `qc`/`bin_*` kind (B-27) can't collide with `pack_order`.
  - A replay compares `{orderId, overrideReason}`. A mismatch is `CONFLICT` (`src/lib/errors.ts`), never a second effect (the Stripe model in `idempotent-side-effect`).
- **Concurrency:**
  - The same order is serialized by `SELECT … FOR UPDATE` on the order before the lookup.
  - The same key on two different orders at once: both pass the lookup, then the second insert blocks on the unique index. `onConflictDoNothing` then gives no row, so it throws `CONFLICT` and rolls back its scans, tote release and audit (`floor.ts:1137-1141`).
  - `afterCommit` hooks don't run on a rolled-back transaction (`db/client.ts:47-63`), so no realtime event leaks.
  - There's no test for this race. It's covered by reasoning only; see note 3.
- **Refusals leave nothing:**
  - `FORBIDDEN` is thrown before any read.
  - `PACK_INCOMPLETE`, on-hold `CONFLICT` and "no units" `CONFLICT` are thrown before the first write (`floor.ts:1046-1062`).
  - Verified live: 0 rows, 0 scans, 0 audits, tote untouched.
- **FK shape:** `order_id` uses a single-column FK (`db/schema/production.ts:227`), not the composite FK S-26 asks for. `orders` has no `(company_id, id)` unique index yet, and adding one to a big table needs the online-index path (B-30). The service loads the order under `withTenant` with `FOR UPDATE` before inserting, which is the interim rule in `add-tenant-table`. Accepted.

## Grants into orders
- **`db/schema/orders.ts:106`:** `packOverride: jsonb().$type<PackOverride>()`, nullable. The comment above it (`:104-105`) still says "packed with units missing"; see note 2.
- **`orders/state-machine.ts`, `recomputeOrderStatus` after the `bdffe6f` revert:**
  - `status` is always `deriveOrderStatus(states)`, so the pre-0010 lift to `ready_to_ship` is fully gone. `PRE_READY` is removed, and `pack.test.ts:306` asserts `in_production` for a short order with an override.
  - `clearOverride` is true only when an override exists and every non-cancelled unit is `packed`/`shipped`/`delivered`, or none is left.
  - Checked live: the hand-off kept `in_production`. After the lead QC-passed the missing units, the order became `ready_to_ship` with the override cleared.
  - Cost: one extra indexed PK read on `orders` per item transition (`state-machine.ts:223`). This is acceptable, but the function now only clears a marker. See note 4.
- **`db/schema/tenancy.ts:228`:** `STATION_KINDS` gains `"receiving"`, the one granted line.

## Blocking findings
None.

## Checks
- [x] Only owned or granted paths changed. `floor_requests` is in the production module's schema file, which the role owns when a card allows a migration. It wasn't named in the grants, but it's justified: `today/service.ts:117` counts `scans` with `count(*)`, so an order-level row there would inflate Today.
- [x] Nothing outside scope.
- [x] Tests aren't weakened. The cross-tenant `NOT_FOUND` test is `pack.test.ts:291`. There is no direct wrong-`companyId` `WITH CHECK` test on `floor_requests` (the `add-tenant-table` step 8 list), but I verified it live. See note 3.
- [x] Tenancy, idempotency: as above.
- [x] Decisions recorded (0010).

## Optional notes (not blocking)
1. Add `lock_timeout` to the `invai_app` and `invai` roles, or to `migrate.ts` (`SET lock_timeout = '5s'` before the run), so that a generated `ALTER TABLE orders` can't queue behind a long transaction and stall every order read. This is my own backlog item, not this card's.
2. Update the `orders.ts:104-105` comment to "handed to a lead" (0010).
3. Add two tests: inserting a `floor_requests` row with another company's id inside `withTenant` must fail; and two concurrent `packOrder` calls with one key on two orders must give one effect and one `CONFLICT`.
4. Retention: `add-tenant-table` says new stored data MUST have a retention period. `floor_requests.result` holds the staff name (`byName`). A 30–90 day purge is enough for replay. Add it to B-23 or file a new item.
5. Consider renaming `orderStatusWithOverride`: it no longer changes status, only decides `clearOverride`.
