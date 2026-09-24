---
name: add-tenant-table
description: Add a new tenant-owned Postgres table in invai-backend with company_id, the RLS tenant policy, composite (company_id, id) foreign keys (S-26), company_id-leading indexes, a generated migration and cross-tenant tests. Use for "new table", "new schema", "store X per shop" or any pgTable change in src/db/schema.
---

# Add a tenant table

A new table that no request can read or write across companies, that fails CI if RLS is missing, and whose
foreign keys can't point at another company's rows.

## When to use
- A card needs data that existing tables can't hold (check first; a migration is a cost).
- You own the module's schema file `src/db/schema/<area>.ts` on the card. backend-foundation co-reviews every
  new table.
- Global, read-only reference data (like `plans`, `trademark_marks`) is different: it uses `publicReadPolicy`,
  and the security-reviewer adds it to `PUBLIC_READ_TABLES` in `src/db/rls-coverage.test.ts`.

## Steps
1. **Read** `src/db/schema/_shared.ts` (`tenantPolicy`, `id`, `timestamps`, `enumText`, `jsonObject`),
   `src/db/schema/tenancy.ts` (`companyId()`), and `src/db/schema/catalog.ts` as the worked example.
2. **Define the table** in `src/db/schema/<area>.ts` from `template.md` (this folder):
   - `id: id()`, `companyId: companyId()`, `...timestamps`.
   - Enum-like columns are `text(enumText(VALUES))`, never pg enums.
   - Money `integer` cents, sizes `doublePrecision` inches (never `integer`, never rounded), times
     `timestamp({ withTimezone: true })`.
   - PII in `encryptedText()` (`src/lib/crypto.ts`), and add it to the purge
     (`src/modules/orders/purge.test.ts` shows the pattern).
   - Extras: `tenantPolicy("<table_name>")`, indexes, then `.enableRLS()`.
3. **Composite tenant-scoped FKs (S-26).** For every reference to another tenant table:
   - The parent gets `uniqueIndex().on(t.companyId, t.id)` if it doesn't have one. That's an extra index on an
     existing table: use `zero-downtime-migration` if the parent is large.
   - The child uses `foreignKey({ columns: [t.companyId, t.parentId], foreignColumns: [parent.companyId, parent.id] })` (drizzle `foreignKey` from `drizzle-orm/pg-core`) instead of `.references(() => parent.id)`.
   - Existing tables still use single-column FKs (backlog B-30). Until yours is composite, the service must
     load the parent under `withTenant` before insert. FK checks ignore RLS.
4. **Indexes lead with `company_id`**: `uniqueIndex().on(t.companyId, t.naturalKey)`, `index().on(t.companyId, t.status)`. Add the natural-key unique index you'll need for idempotent upserts now (see `idempotent-job`).
5. **Export** the table from `src/db/schema/index.ts` if your file is new.
6. **Generate the migration** (never write or edit the SQL of an applied one):
   ```
   export PATH="$HOME/.local/share/pnpm/bin:$HOME/.local/share/pnpm:$PATH"
   cd invai-backend && pnpm db:generate --name <area>_<change>
   ```
   Read the generated `drizzle/NNNN_<area>_<change>.sql`: it must contain `ALTER TABLE "<table>" ENABLE ROW LEVEL SECURITY` and `CREATE POLICY "<table>_tenant" ... TO "invai_app" USING (company_id = ...) WITH CHECK (...)`. Grants come from the default privileges in `drizzle/0001_grants_extensions.sql` and
   `invai-infra/local/init.sql`, so a plain table needs none. An append-only table (like `audit_log`) needs a
   custom migration (`pnpm db:generate --custom --name <area>_<table>_append_only`) with `REVOKE UPDATE, DELETE ON <table> FROM invai_app;`. If the journal collides with another agent's, the later one
   regenerates.
7. **Apply** to the dev DB (`pnpm db:migrate`), then run the tests; `src/test/global-setup.ts` migrates
   `invai_test`.
8. **Tests** in your module's `*.test.ts` (from `template.md`):
   - Write and read under `withTenant(companyA)`.
   - Company B reading A's row by id gets nothing (service returns `NOT_FOUND`, never `FORBIDDEN`).
   - Company B inserting a row that points at A's parent fails (the composite FK) or is rejected by the
     service.
   - Inserting with the wrong `companyId` inside `withTenant` fails the RLS `WITH CHECK`.
9. **Coverage test:** `src/db/rls-coverage.test.ts` finds every table with `company_id` by itself; it must
   stay green. Never edit or skip it (security-reviewer owns it).

## Rules (MUST / MUST NOT)
- MUST have `company_id`, `tenantPolicy()` and `.enableRLS()` in the same migration that creates the table.
- MUST keep the policy plain equality on `company_id` (the shared helper). A custom policy (subquery,
  function, `LIKE`) needs an `EXPLAIN (ANALYZE, BUFFERS)` check at 1,000 tenants and 1M rows before merge
  (research 11 §2.1).
- MUST insert `companyId` explicitly on every row.
- MUST NOT create a view without `WITH (security_invoker = true)`, or a `SECURITY DEFINER` function reachable
  by `invai_app`.
- MUST NOT use `withSystem` to read or write the table from a request path.
- MUST NOT add a trigram/GIN index that doesn't lead with `company_id` (research 11 §2.1 gap G17).
- MUST give new stored data a retention period (research 12 §2.7).

## Done when
- The migration is generated, committed with the schema change, and applies cleanly on `pnpm db:reset && pnpm db:migrate && pnpm db:seed`.
- `pnpm typecheck && pnpm lint && pnpm test` pass in `invai-backend`, including `rls-coverage.test.ts`.
- The cross-tenant read, cross-tenant FK and wrong-`companyId` tests exist and pass.
- backend-foundation and security-reviewer are named as co-reviewers.

## References
- `template.md` (this folder)
- `invai-backend/src/modules/README.md` (rules 3 and 5), `src/db/schema/_shared.ts`,
  `src/db/rls-coverage.test.ts`
- `invai-docs/security/v1-review.md` S-26; `invai-docs/waves/backlog.md` B-30
- `invai-docs/research/12-security-quality-playbook.md` §1.1; `11-platform-scale-playbook.md` §2.1
- Related: `zero-downtime-migration`, `idempotent-job`, `tenant-isolation-audit`
