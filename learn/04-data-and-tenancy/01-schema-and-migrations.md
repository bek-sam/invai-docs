# Lesson 4.1 — Schema and migrations: one definition, generated SQL

## 1. In one sentence
Every table in InvAI is defined once, in a TypeScript file under
`invai-backend/src/db/schema/`, and the actual SQL that creates or changes it in Postgres is
**generated** from that definition by drizzle-kit — nobody hand-writes a `CREATE TABLE` or
`ALTER TABLE` statement, and nobody hand-edits a migration that's already been applied.

## 2. Why it exists
Module 03 (lesson 2) explained *why* Drizzle was picked over Prisma: RLS policies live in the
schema file, not in a separate hand-written SQL migration. This lesson is about what that actually
looks like day to day, and why the "generate, don't hand-write" rule is strict enough that
`CLAUDE.md` calls it out directly: *"Never hand-edit an applied migration."* A migration that's
already run in a shared database (or in anyone else's local copy) is a fact about the past — if you
edit the file after the fact instead of writing a new one, your local database and someone else's
disagree about what "migration 0031" actually did, and drizzle-kit's own bookkeeping (the journal)
breaks.

## 3. How it works

### One schema file, one table, one policy
Every tenant table's definition — columns, indexes, foreign keys, *and* its RLS policy — lives in
one `pgTable(...)` call. Take `orderItems` (`invai-backend/src/db/schema/orders.ts:176-234`): the
columns are plain Drizzle column builders (`integer()`, `text()`, `timestamp({ withTimezone:
true })`), a handful of small shared helpers do repeated work —
`invai-backend/src/db/schema/_shared.ts:66` (`id()`, a UUID primary key defaulting to a random
value), `:75` (`timestamps`, the `createdAt`/`updatedAt` pair every table gets), `:82`
(`jsonArray<T>()`/`jsonObject<T>()`, a `jsonb` column typed and defaulted in one call) — and the
table's extras array ends with `tenantKey("order_items", t)` and `tenantPolicy("order_items")`,
followed by `.enableRLS()`. Lesson 4.2 is the deep dive on what those two calls actually do; here
the point is just: they're part of the *same definition* as the columns, not a separate file
someone could forget to update.

### Generating a migration
`invai-backend/drizzle.config.ts` points drizzle-kit at `./src/db/schema/index.ts` (which
re-exports every module's schema file) and an output folder, `./drizzle`. Changing a table means:
edit the schema file, then run `pnpm db:generate --name <module>_<change>`
(`CLAUDE.md`, "Migrations") — drizzle-kit diffs the schema against its own record of the last
migration (`invai-backend/drizzle/meta/_journal.json`, an ordered list of every migration's tag and
timestamp) and writes a new numbered `.sql` file plus a journal entry. Both get committed together.
If two agents (or two developers) generate a migration at the same time and collide on the
journal, `CLAUDE.md`'s rule is simple: the later one regenerates — there's no merge step, because
the journal's order *is* the migration order.

### Why this is safer than it sounds: expand, then contract
A real example from this project's own history: fixing security finding S-26 (composite foreign
keys, lesson 4.2 covers the "why"). The fix touched 49 foreign keys across the schema, but it
shipped as **two** migrations, not one:
- `invai-backend/drizzle/0030_foundation_composite_fks.sql` drops each old single-column FK and
  adds the new composite one with `NOT VALID` — Postgres accepts the new constraint immediately,
  without scanning every existing row to check it (that would need a long lock on a busy table).
- `invai-backend/drizzle/0031_foundation_composite_fks_validate.sql` runs `VALIDATE CONSTRAINT`
  afterward, which *does* scan the table, but only takes a brief lock, and can run whenever it's
  convenient.

This is the "expand, then contract" pattern migrations use whenever a change could lock a busy
table: 0030's own comment explains the one subtlety Drizzle *can't* express — a nullable composite
foreign key that should null out just the referencing column on delete, not `company_id` too,
needs `ON DELETE SET NULL (<col>)` written into the SQL by hand after generation, because
`.onDelete("set null")` in the schema can't carry that column list. The schema stays the source of
truth for intent; the generated SQL file is where a human (or an agent) double-checks the literal
statement before it runs.

## 4. In our code
- `invai-backend/src/db/schema/orders.ts:176-234` — `orderItems`, one table with its columns,
  indexes, a composite foreign key and its RLS policy all in one place.
- `invai-backend/src/db/schema/_shared.ts:66,75,82` — `id()`, `timestamps`, `jsonArray`/
  `jsonObject`: the small shared helpers almost every table uses.
- `invai-backend/drizzle.config.ts` — the schema entry point, output folder, and the comment
  noting drizzle-kit runs as the owner role, never the app role.
- `invai-backend/drizzle/0030_foundation_composite_fks.sql`,
  `invai-backend/drizzle/0031_foundation_composite_fks_validate.sql` — a real expand/contract
  migration pair, with the `NOT VALID` / `VALIDATE CONSTRAINT` split explained in their own
  comments.
- `invai-backend/drizzle/meta/_journal.json` — the ordered record of every migration drizzle-kit
  has generated.
- `invai-backend/src/db/migrate.ts` and its `migrate.test.ts` — how migrations actually get applied
  (worth reading once, to see that it's just "run every pending file, in order, in one
  transaction").

## 5. What it uses
- **Drizzle ORM** — the schema definitions (columns, indexes, foreign keys, RLS policies).
- **drizzle-kit** — the CLI that diffs the schema against the journal and generates migration SQL.
- Plain Postgres DDL (`CREATE TABLE`, `ALTER TABLE ... NOT VALID`, `VALIDATE CONSTRAINT`) — the
  generated output, not something InvAI wraps in its own abstraction.

## 6. Try it yourself
1. Open `invai-backend/src/db/schema/orders.ts` around line 179 (`orderItems`) and, right below it,
   `invai-backend/drizzle/meta/_journal.json`'s last few entries — find the migration tag that
   first created this table (search the `drizzle/` folder for `order_items` if you're not sure
   which number).
2. Read `invai-backend/drizzle/0030_foundation_composite_fks.sql`'s first ten lines (the comment)
   and then its first `ALTER TABLE ... DROP CONSTRAINT` / `ADD CONSTRAINT ... NOT VALID` pair — on
   paper, explain to yourself why adding the constraint as `NOT VALID` first avoids locking the
   whole table.
3. Run `pnpm db:generate --name scratch_test` inside `invai-backend` (with the pnpm PATH export)
   after making a trivial, reversible schema tweak (e.g. adding a comment-only change won't
   generate anything — try adding then removing an unused column) to see what an empty or tiny
   diff actually produces, then discard the change without committing it.

## 7. Common mistakes
- Hand-editing a migration file that's already been applied (to anyone's database, not just your
  own) instead of writing a new migration. `CLAUDE.md` is explicit that this is never allowed —
  the journal and the applied database state both assume migration files never change after the
  fact.
- Running a schema change that needs `ALTER TABLE ... ADD CONSTRAINT` (not `NOT VALID`) directly
  against a large, busy table, locking it for the full validation scan. The composite-FK migration
  pair (0030/0031) is the real example of avoiding exactly this.
- Forgetting that drizzle-kit runs as the Postgres owner role, while the running app connects as
  `invai_app` with no DDL rights (`invai-backend/drizzle.config.ts`'s own comment) — a migration
  is the only place schema changes are allowed to happen at all.

## 8. Check yourself
<details>
<summary>1. Where does an RLS policy for a table actually get defined — a separate migration file,
or somewhere else?</summary>

In the same schema file as the table's columns (a `tenantPolicy("<table>")` call plus
`.enableRLS()` in the table's extras array) — drizzle-kit generates the matching SQL from that one
definition, so the policy can't drift from the table it protects.
</details>

<details>
<summary>2. Why did the composite-foreign-key fix ship as two migrations (0030 and 0031) instead
of one?</summary>

Adding a `NOT VALID` constraint is instant because Postgres skips checking existing rows; a
separate `VALIDATE CONSTRAINT` migration does that check afterward with only a brief lock, instead
of one migration holding a long lock on a busy table while it both adds and fully validates the
constraint.
</details>

<details>
<summary>3. What's one thing Drizzle's schema syntax *can't* express, that 0030's own comment
explains had to be written into the generated SQL by hand?</summary>

`ON DELETE SET NULL (<col>)` on a composite foreign key — nulling out only the referencing column,
not `company_id` too. Drizzle's `.onDelete("set null")` can't carry that column list, so the
generated file was hand-edited before being committed (not after it was applied).
</details>

## 9. Words to know
- **Migration** — a versioned SQL script, generated from the schema, that changes the database;
  applied in order and never edited after the fact.
- **drizzle-kit** — the CLI that diffs the Drizzle schema against its journal and generates
  migration files.
- **Journal** (`meta/_journal.json`) — drizzle-kit's ordered record of every migration it has
  generated, used to detect what's new since the last one.
- **Expand/contract migration** — splitting a risky schema change into a safe "add the new thing
  without fully validating it yet" step and a later "finish validating it" step, to avoid locking
  a busy table for a long scan.
- **`NOT VALID` / `VALIDATE CONSTRAINT`** — a Postgres feature letting a new constraint be added
  instantly (skipping the check on existing rows) and validated separately later.
