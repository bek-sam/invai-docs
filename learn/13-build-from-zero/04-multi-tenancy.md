# Lesson 13.4 — Multi-tenancy: `company_id`, RLS, and `withTenant`

## 1. In one sentence
You'll add a `company_id` column to your `widgets` table, turn on Postgres
Row-Level Security (RLS) so the database itself refuses to show or write another
company's rows, and wrap every query in a `withTenant(companyId, fn)` helper that
sets which company a connection is allowed to see for the lifetime of one
transaction.

## 2. Why it exists
InvAI is one piece of software serving many DTF shops. If a backend bug ever let
Shop A's office person query Shop B's orders, that's not a cosmetic glitch — it's a
real data breach of a real business's customer and financial information. The
easiest way to make that bug impossible to miss is to not rely on *every single
query, everywhere, forever* remembering to add `WHERE company_id = ?`. One missed
`WHERE` clause, in one of hundreds of queries written over months by different
people, is exactly the kind of mistake that happens.

RLS flips the responsibility: once a policy is on, the database *itself* silently
filters every query — `SELECT`, `UPDATE`, `DELETE` — to only the rows the current
connection is allowed to see, no matter how the query was written above it. A forgot
ten `WHERE` clause becomes a non-event instead of a breach. `CLAUDE.md` makes this
the project's single non-negotiable rule for tenant data: "Tenant tables have
`company_id` and RLS," enforced by a test that fails if *any* `company_id` table
lacks it.

## 3. How it works

### Step 1 — add `company_id` and a `companies` table
```ts
// src/db/schema.ts
import { pgTable, uuid, text, integer, timestamp, pgPolicy, pgRole, index } from "drizzle-orm/pg-core";
import { sql } from "drizzle-orm";

export const appRole = pgRole("fz_app").existing();
const currentCompanyId = sql`nullif(current_setting('app.company_id', true), '')::uuid`;

export const companies = pgTable("companies", {
  id: uuid().primaryKey().defaultRandom(),
  name: text().notNull(),
});

export const widgets = pgTable("widgets", {
  id: uuid().primaryKey().defaultRandom(),
  companyId: uuid("company_id").notNull().references(() => companies.id, { onDelete: "cascade" }),
  name: text().notNull(),
  priceCents: integer("price_cents").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
}, (t) => [
  index().on(t.companyId),
  pgPolicy("widgets_tenant", {
    for: "all",
    to: appRole,
    using: sql`company_id = ${currentCompanyId}`,
    withCheck: sql`company_id = ${currentCompanyId}`,
  }),
]).enableRLS();
```
`using` controls what an existing row is allowed to match for reads/updates/deletes;
`withCheck` controls what a *new or changed* row is allowed to end up as — you need
both, or an `INSERT` for the wrong company could silently succeed.

### Step 2 — a non-owner role that RLS actually applies to
```sql
-- run once, as the database owner
CREATE ROLE fz_app LOGIN PASSWORD 'fz';
GRANT ALL ON DATABASE fz TO fz_app;
GRANT USAGE ON SCHEMA public TO fz_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO fz_app;
```
This matters more than it looks: RLS policies don't apply to a table's *owner*, or to
any role with `BYPASSRLS`. If your app connects as the same role that ran the
migrations, every policy you write is silently ignored. `fz_app` here is deliberately
a separate, lower-privileged role — `drizzle.config.ts`'s `entities.roles.include`
option tells `drizzle-kit generate` to emit the `pgPolicy`/`GRANT` SQL for this role.

### Step 3 — `withTenant`
```ts
// src/db/client.ts
import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import * as schema from "./schema";

const appPool = new Pool({ connectionString: "postgres://fz_app:fz@localhost:5433/fz" });
export const db = drizzle(appPool, { schema, casing: "snake_case" });

export function withTenant<T>(companyId: string, fn: (tx: typeof db) => Promise<T>): Promise<T> {
  return db.transaction(async (tx) => {
    // set_config(..., true) = transaction-local: never leaks across a pooled connection
    await tx.execute(sql`select set_config('app.company_id', ${companyId}, true)`);
    return fn(tx);
  });
}
```
Every request-scoped query from here on goes through `withTenant(companyId, ...)` —
never straight through `db` for tenant data.

### Step 4 — prove it, don't assume it
This is the step most tutorials skip. Create two companies and a widget for each,
then query as company A for a widget that belongs to company B:
```ts
const a = await withTenant(companyAId, (tx) => tx.query.widgets.findFirst());
const b = await withTenant(companyBId, (tx) =>
  tx.select().from(widgets).where(eq(widgets.id, widgetBelongingToA.id)));
console.log(b); // -> [] : empty, even though the row exists and the id is correct
```
If `b` comes back with the row anyway, something's wrong — either RLS isn't enabled,
the role has bypass rights, or `set_config` isn't actually being applied before the
query runs.

## 4. In our code
- `invai-backend/src/db/schema/_shared.ts:12-33` — the real
  `currentCompanyId`/`tenantMatch`/`tenantPolicy()` your Step 1 copied almost
  verbatim, including the `appRole = pgRole("invai_app").existing()` line.
- `invai-backend/src/db/schema/tenancy.ts:239-268` — a real tenant table,
  `locations`: `companyId: companyId()` (a shared helper for the column + FK),
  `tenantKey(...)`, `index().on(t.companyId)`, `tenantPolicy("locations")`, then
  `.enableRLS()` — the exact five-piece pattern your `widgets` table now follows.
- `invai-backend/src/db/client.ts:44-71` — the real `withTenant`: a transaction,
  `set_config('app.company_id', companyId, true)` with the `true` third argument for
  transaction-local scope — the comment right above it explains why: "pooled
  connections never leak a tenant."
- `invai-backend/src/db/client.ts:86-92` — `withSystem`, the deliberate escape hatch:
  a *second*, owner-role connection that bypasses RLS entirely, reserved for the
  outbox relay, cross-tenant jobs and the seed script. `CLAUDE.md` is explicit that
  `withSystem` is never used for ordinary request code.
- `invai-infra/local/init.sql:1-4, 10-13` — the real role setup: `CREATE ROLE
  invai_app LOGIN PASSWORD 'invai'` plus the `GRANT`/`ALTER DEFAULT PRIVILEGES`
  dance your Step 2 reproduced, with a comment explaining exactly why — "not the
  table owner, no BYPASSRLS, so row-level security applies."

## 5. What it uses
- **Postgres Row-Level Security** — a database feature that filters rows per
  connection based on a policy, not application code; module 03.2 covers why this
  over filtering everything in TypeScript.
- **`set_config(..., true)`** — a Postgres function that sets a session variable
  scoped to the current transaction when the third argument is `true`, which is what
  keeps a pooled connection from ever leaking one request's tenant into the next.
- **drizzle's `pgPolicy`/`.enableRLS()`** — drizzle-kit turns these into the actual
  `CREATE POLICY`/`ALTER TABLE ... ENABLE ROW LEVEL SECURITY` SQL in your generated
  migration.

## 6. Try it yourself
1. Query `widgets` directly with `psql` as the **owner** role (not `fz_app`) with no
   `set_config` call at all. You'll see every company's rows — owners bypass RLS by
   default. Now reconnect as `fz_app` with no `set_config` call: you should see *zero*
   rows (the policy's `using` clause compares against `NULL`, which matches nothing).
   This is the real behavior comment in InvAI's code: "unset means 'no rows.'"
2. Try an `INSERT` as `fz_app` with `app.company_id` set to company A's id, but the
   row's own `company_id` value set to company B. The `withCheck` clause should
   reject it. Remove `withCheck` from your policy (leave only `using`) and try again —
   does it succeed now? This is exactly why both clauses are required.
3. `grep -n "tenantPolicy(" invai-backend/src/db/schema/*.ts | wc -l` — count how many
   real tables carry this exact policy, then look at module 04.2 for the full tenancy
   lesson, including the test that fails the build if a `company_id` table is ever
   missing one.

## 7. Common mistakes
- Connecting the app as the migration/owner role in production-shaped code "to make
  it simpler." If the app role can bypass RLS, every policy you wrote is decoration,
  not a real security boundary — this is the single most important thing to get
  right in this lesson.
- Writing `using` but forgetting `withCheck` (or vice versa). A policy with only
  `using` lets a connection correctly *see* only its own rows, but may still be able
  to *insert or update* a row into another tenant's scope — a real, specific gap this
  project enforces tests against (`tenant-isolation-audit`).
- Calling a query through plain `db` instead of `withTenant(...)` for tenant data —
  without `set_config` having run first in that transaction, the RLS policy sees no
  `app.company_id` at all and (correctly, per the "unset means no rows" rule) returns
  nothing, which can look like "it works" (empty result, no error) right up until it
  looks like a confusing bug report.

## 8. Check yourself
<details>
<summary>1. Why is <code>set_config</code> called with its third argument as
<code>true</code> rather than left at the default?</summary>

`true` makes the setting transaction-local: it's automatically cleared when the
transaction ends. Postgres connections are reused across different requests/tenants
by a connection pool, so without this, one request's tenant setting could leak into
the next request that happens to reuse the same underlying connection.
</details>

<details>
<summary>2. A table has <code>company_id</code> and a correct RLS policy, but the
app connects to Postgres as the table's owner. What actually happens to a
cross-tenant query?</summary>

It succeeds and returns the other tenant's data — RLS policies are not enforced
against the owning role (or any role with BYPASSRLS) by Postgres's design. The column
and the policy exist, but they're not actually providing isolation for that
connection.
</details>

<details>
<summary>3. What's <code>withSystem</code> for, and why doesn't ordinary request
code ever use it?</summary>

It's a second connection, as the owner role, that bypasses RLS entirely — reserved
for genuinely cross-tenant work like the outbox relay (moving events for every
company), the demo seed, and background jobs that must touch more than one tenant at
once. Ordinary request code never uses it because doing so would silently remove the
one safety net (RLS) this whole lesson is about — a bug in `withSystem`-using code
has no database-level backstop at all.
</details>

## 9. Words to know
- **Row-Level Security (RLS)** — a Postgres feature that filters which rows a query
  can see or change, based on a policy, enforced by the database regardless of how
  the query was written.
- **`company_id`** — the column every InvAI tenant table carries, identifying which
  shop (or vendor) a row belongs to.
- **`withTenant(companyId, fn)`** — InvAI's helper that opens a transaction, sets
  the active company for Postgres's RLS policies to read, then runs `fn`.
- **`withSystem(fn)`** — the deliberate, rare exception: a connection that bypasses
  RLS, for cross-tenant infrastructure code only (outbox, seed, jobs).
- **Policy (RLS policy)** — a rule attached to a table (`CREATE POLICY`) that
  defines which rows a given database role may see (`using`) or write (`withCheck`).
