# Lesson 13.3 — The backend: first endpoint, drizzle, a migration

## 1. In one sentence
You'll stand up a tiny backend that `implement()`s the contract from lesson 13.2
against a real Postgres table — defined with drizzle, turned into SQL with a
generated migration, and served over HTTP — so a real `curl` request goes all the way
from the wire to a database row and back.

## 2. Why it exists
The contract package describes *shapes*; it has no idea a database exists. The
backend's job is to make those shapes real: take a validated input, do something
with actual data, return something that matches the declared output (or throw a
declared error). InvAI does this with **drizzle** (a TypeScript query builder that
also generates SQL migrations from your schema) rather than hand-written SQL files or
a heavier ORM, because the same schema file is both "what TypeScript thinks a row
looks like" and "what the migration generator turns into `CREATE TABLE`" — one
definition, not two that can drift.

`implement(contract)` is the piece that connects back to lesson 13.2: it takes the
oRPC contract you wrote and gives you a typed `.handler()` for every procedure, so if
your handler returns the wrong shape, that's a compile error — the same safety net
that made the contract worth writing in the first place.

## 3. How it works

### Step 1 — a database connection
```bash
cd ~/invai-from-zero
mkdir backend && cd backend
pnpm init
pnpm add drizzle-orm pg @orpc/server @orpc/contract zod hono @hono/node-server
pnpm add -D drizzle-kit tsx typescript
pnpm add @invai/contracts   # or link lesson 13.2's package locally
```
`src/db/client.ts`:
```ts
import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import * as schema from "./schema";

const pool = new Pool({ connectionString: "postgres://fz:fz@localhost:5433/fz" });
export const db = drizzle(pool, { schema, casing: "snake_case" });
```

### Step 2 — a drizzle schema
`src/db/schema.ts`:
```ts
import { pgTable, uuid, text, integer, timestamp } from "drizzle-orm/pg-core";

export const widgets = pgTable("widgets", {
  id: uuid().primaryKey().defaultRandom(),
  name: text().notNull(),
  priceCents: integer("price_cents").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});
```
`drizzle.config.ts`:
```ts
import { defineConfig } from "drizzle-kit";
export default defineConfig({
  dialect: "postgresql",
  schema: "./src/db/schema.ts",
  out: "./drizzle",
  casing: "snake_case",
  dbCredentials: { url: "postgres://fz:fz@localhost:5433/fz" },
});
```

### Step 3 — generate and run a migration
```bash
npx drizzle-kit generate --name widgets_init
cat drizzle/0000_widgets_init.sql     # read the SQL it wrote — never skip this
npx drizzle-kit migrate
```
Read the generated SQL before running it, every time — this is how you catch a
schema change that would do something you didn't intend (drop a column, change a
type) before it touches a real database.

### Step 4 — implement the contract
`src/server.ts`:
```ts
import { implement } from "@orpc/server";
import { RPCHandler } from "@orpc/server/fetch";
import { serve } from "@hono/node-server";
import { Hono } from "hono";
import { eq } from "drizzle-orm";
import { contract } from "@invai/contracts";   // from lesson 13.2
import { db } from "./db/client";
import { widgets } from "./db/schema";

const os = implement(contract);

const router = os.widgets.router({
  get: os.widgets.get.handler(async ({ input }) => {
    const [row] = await db.select().from(widgets).where(eq(widgets.id, input.id));
    if (!row) throw new Error("NOT_FOUND");   // lesson 13.4 makes this a typed error
    return { id: row.id, name: row.name, priceCents: row.priceCents };
  }),
  create: os.widgets.create.handler(async ({ input }) => {
    const [row] = await db.insert(widgets).values(input).returning();
    return { id: row.id, name: row.name, priceCents: row.priceCents };
  }),
});

const handler = new RPCHandler(router);
const app = new Hono();
app.use("/rpc/*", async (c, next) => {
  const { matched, response } = await handler.handle(c.req.raw, { prefix: "/rpc" });
  if (matched) return c.newResponse(response.body, response);
  await next();
});
serve({ fetch: app.fetch, port: 3100 });
```

### Step 5 — exercise it for real
```bash
npx tsx src/server.ts &
curl -s -X POST localhost:3100/rpc/widgets/create \
  -H 'content-type: application/json' \
  -d '{"name":"Test Shirt","priceCents":1999}'
# -> {"id":"...", "name":"Test Shirt", "priceCents":1999}
```
Compiling is not verification — this `curl` call, actually hitting your server,
actually writing a row to Postgres, is the thing that proves it works.

## 4. In our code
- `invai-backend/src/db/client.ts:1-17` — the real connection: two pools,
  `appPool` (the limited `invai_app` role, RLS enforced) and `systemPool` (the owner
  role, bypasses RLS, used only for migrations/seed/outbox — lesson 13.4 explains
  why two).
- `invai-backend/drizzle.config.ts` — the real drizzle-kit config: schema at
  `src/db/schema/index.ts`, output to `./drizzle`, `casing: "snake_case"` (so
  `priceCents` in TypeScript becomes `price_cents` in SQL automatically).
- `invai-backend/drizzle/0000_init.sql:1-16` — a real generated migration: a
  `CREATE TABLE`, then `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` right after it —
  the pattern lesson 13.4 builds on top of your plain `widgets` table.
- `invai-backend/src/api/orpc.ts:37` — the real
  `export const os = implement(contract).$context<Context>()`, the exact call your
  `src/server.ts` made, with a typed request `Context` (who's signed in, which
  tenant) layered on, covered fully in lessons 13.4–13.5.
- `invai-backend/src/modules/tenancy/router.ts:12-15` — a real handler,
  `meRouter.get`, shaped exactly like your `widgets.get`: `.handler(({ context }) =>
  withTenant(context.tenant.companyId, (tx) => svc.me(tx, context)))` — note the
  `withTenant(...)` wrapper you don't have yet; that's the whole subject of the next
  lesson.
- `invai-backend/src/api/app.ts:2-3, 44-48` — the real server: both an `RPCHandler`
  (what the web/floor apps actually call) and an `OpenAPIHandler` (REST, generated
  from the same `.route()` metadata) over the same router.

## 5. What it uses
- **drizzle-orm / drizzle-kit** — a TypeScript query builder (write queries as
  TypeScript, not raw SQL strings) that also generates migrations from your schema;
  module 03.2 covers why this over Prisma or hand-written SQL.
- **pg** — the plain PostgreSQL driver drizzle sits on top of.
- **Hono** — a small, fast HTTP framework; InvAI's actual server (`src/api/app.ts`)
  is a Hono app with the oRPC handler mounted inside it.
- **`implement(contract)`** (`@orpc/server`) — turns a contract into a typed builder
  you attach real `.handler()` functions to; this is the piece that makes "backend
  matches contract" a compile-time fact, not a hope.

## 6. Try it yourself
1. `curl -s -X POST localhost:3100/rpc/widgets/get -d '{"id":"<a real
   id from your create call>"}'` — then try it again with a made-up UUID and see your
   plain `throw new Error("NOT_FOUND")` produce an ugly 500, not a clean 404. Lesson
   13.4's typed errors fix exactly this.
2. Open `invai-backend/drizzle/0000_init.sql` and find one table's
   `ENABLE ROW LEVEL SECURITY` line. Your `widgets` table doesn't have this yet —
   query it directly with `psql` and confirm you can see every row from any
   connection, with no tenant restriction at all. That's the gap lesson 13.4 closes.
3. Change `priceCents` in your schema to `price: integer()` (a plain rename) and run
   `drizzle-kit generate` again. Read the generated SQL: does it `ALTER TABLE ...
   RENAME COLUMN`, or does it drop and recreate? This is exactly the kind of question
   "always read the generated SQL before running it" protects you from.

## 7. Common mistakes
- Trusting a remembered drizzle or oRPC API instead of checking `node_modules`. The
  real team's `read-before-change` skill names drizzle, oRPC and several other
  libraries as "newer than training data" — the exact APIs (`implement()`,
  `.route()`, drizzle's `casing` option) can differ from what you'd guess.
- Hand-editing a migration file after it's been applied to a database. InvAI's rule
  is absolute: edit the schema file, regenerate, never hand-edit an applied
  migration — a hand-edited migration can drift from what's actually in the
  database, and the next person who runs migrations has no way to know.
- Returning the wrong shape from a handler and not noticing because you only
  "compiled," never called it. `implement(contract)` catches a shape mismatch at
  compile time *only* if your handler's return type is wrong in a way TypeScript can
  see — a handler that silently returns an extra, undeclared field, or the right
  shape with wrong values, compiles fine. Only an actual `curl` (or a test, lesson
  13.10) proves the values are right.

## 8. Check yourself
<details>
<summary>1. Why does drizzle generate SQL files instead of applying schema changes
to the database directly?</summary>

So there's a reviewable, committable record of exactly what changed and why — the
same reason version control exists for code. It also means the same migration can be
run identically in every environment (your machine, CI, production) instead of each
one drifting toward whatever `drizzle-kit push` happened to do on a given day.
</details>

<details>
<summary>2. What's the difference between a contract-level error (declared in
<code>.errors()</code>, lesson 13.2) and the plain <code>throw new
Error("NOT_FOUND")</code> this lesson used?</summary>

The plain `throw new Error(...)` is just a JavaScript error with no special meaning
to oRPC — it becomes a generic 500 to the caller. A contract-level error (an oRPC
"ORPCError" built from the contract's declared error map) carries a real HTTP status
and a typed shape the caller can check against, which is what actually lets a
frontend handle "not found" differently from "something broke."
</details>

<details>
<summary>3. Your <code>widgets</code> table has no Row-Level Security. What can any
authenticated database connection currently do that it shouldn't be able to?</summary>

See and modify every row in the table, regardless of who it "belongs to" — there's
no concept of ownership enforced by the database at all yet. Right now the only thing
stopping cross-tenant access is... nothing. Lesson 13.4 is entirely about closing this
gap before it ever reaches a real multi-shop system.
</details>

## 9. Words to know
- **drizzle-orm** — a TypeScript query builder: you write queries against typed
  table objects instead of raw SQL strings.
- **drizzle-kit** — drizzle's companion CLI that diffs your schema file against the
  database and generates a migration SQL file.
- **Migration** — a versioned SQL file that changes the database schema; applied in
  order, never hand-edited once it's run against a real database.
- **Handler** — the function attached to one oRPC procedure that actually does the
  work (query the database, return a value or throw an error).
- **Hono** — a small web framework InvAI's real API server is built on, underneath
  the oRPC handlers.
