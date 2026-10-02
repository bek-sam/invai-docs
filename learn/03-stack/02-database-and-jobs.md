# Lesson 3.2 — drizzle + Postgres RLS, and Valkey/BullMQ

## 1. In one sentence
InvAI stores data in Postgres through drizzle (an ORM that puts row-level security *in the
schema file*, not a separate script), and runs background work through BullMQ on Valkey (a
Redis-compatible store) — both picked because they let the database and the queue enforce
rules the application code would otherwise have to remember to check every time.

## 2. Why it exists
Module 02 showed `withTenant` opening a transaction and RLS filtering rows; module 04 goes
deep on how that's built. This lesson is the "why drizzle, why BullMQ, why not the
alternatives" layer in between — grounded in `invai-docs/research/06-tools-backend.md`'s
actual scored comparisons, not general reputation.

## 3. How it works

### drizzle — RLS lives in the schema, not bolted on after
`invai-docs/research/06-tools-backend.md:66-73` compares **Drizzle** against **Prisma 7** and
**Kysely**:
- Drizzle scored **9.5/10**: "Policies and roles live in the schema (`pgPolicy`, `pgRole`,
  `.withRLS()`), and drizzle-kit generates their migrations." Enabling a transaction-local
  Postgres setting is "trivial" — `tx.execute(sql\`select set_config(...)\`)`.
- Prisma 7 scored **6.5/10**: "No RLS policies in the schema (you manage them in raw SQL
  migrations). The per-query transaction wrapping costs performance and fits badly with
  interactive transactions." Prisma has the best migration DX, but tenant isolation would live
  *outside* the ORM's own types — exactly the kind of gap where a new table could be added
  without anyone remembering to write its RLS policy by hand.
- Kysely (hand-written SQL migrations) was the runner-up at 7.5 — a fallback if you wanted
  more SQL control and less ORM magic.

This is why `invai-backend/src/db/schema/_shared.ts:22-33` can define `tenantPolicy(table)` as
a function that returns a `pgPolicy(...)` object, and every schema file just calls it as one of
the table's "extras" — the policy is *declared next to the columns*, so a reviewer sees in one
file both what a table stores and who's allowed to see which rows of it. Drizzle-kit then
generates the migration SQL for both the table and its policy together (see module 04 lesson
1 for the full walkthrough).

### Postgres itself, and why RLS over an application-layer check
The alternative to RLS is "every query remembers to add `WHERE company_id = ?`." That's one
missed `WHERE` clause away from a cross-tenant leak. RLS moves the check into Postgres itself:
even a buggy query, or a query from code that forgot to scope it, physically cannot return
another tenant's rows, because the database — not the application — enforces the policy.
`invai-backend/src/db/schema/_shared.ts:50-59`'s `tenantKey`/composite-FK comment spells out
why this matters even more at the *foreign key* level: "FK checks ignore RLS, so a single-
column FK would let a row of shop B point at shop A's row." Module 04 covers this in full.

### Valkey/BullMQ — the queue research called "the most important choice"
`invai-docs/research/06-tools-backend.md:77` literally headers this section "Background jobs
and workflows (the most important choice)," and compares **BullMQ** against **Temporal**,
**Inngest**, **Trigger.dev**, **Hatchet**, and **AWS SQS+Lambda**:
- BullMQ scored **9/10** and was the cheapest at every volume tier (~$40-600/mo vs. $1.2k-11k
  for managed alternatives at scale). Its strengths for InvAI specifically: "TypeScript-native,
  with Flows for fan-out, Job Schedulers for per-connection sync, and `jobId` for idempotency,"
  plus an **official Python client**, so `invai-imaging` could in principle consume the same
  queues directly (today it's called over plain HTTP instead — see lesson 3.5).
- Hatchet was the runner-up (8/10): built-in per-tenant fairness and rate limiting that BullMQ
  OSS lacks natively (that needs BullMQ Pro's Groups feature, or a Redis token bucket you build
  yourself).
- Temporal, Inngest and Trigger.dev all scored lower specifically because they bill **per
  execution or per step** — at InvAI's polling volume (order sync every 5-10 min per
  connection, across potentially thousands of connections), that adds up fast; the research
  explicitly recommends avoiding them "for high-frequency polling at Scale."

**Valkey** is Redis-compatible (so BullMQ doesn't know the difference) but under a fully open
license, which is why `invai-infra/local/docker-compose.yml` runs `valkey/valkey:8` rather than
a Redis image. BullMQ's own requirement — `maxRetriesPerRequest: null` and
`maxmemory-policy noeviction` — shows up directly in
`invai-backend/src/lib/queues.ts:17-18`: `new Redis(env.REDIS_URL, { maxRetriesPerRequest: null, lazyConnect: false })`.

The five named queues (`invai-backend/src/lib/queues.ts:19-28`) — `sync`, `render`, `ship`,
`ai`, `reports` — each get their own concurrency limit (`QUEUE_CONCURRENCY`:
`sync: 10, render: 2, ship: 5, ai: 4, reports: 1`), because a slow gang-sheet render shouldn't
starve a fast order-sync poll, and vice versa.

## 4. In our code
- `invai-backend/src/db/schema/_shared.ts:22-33` — `tenantPolicy(table)`, the one function
  every tenant table's RLS policy comes from.
- `invai-backend/src/db/schema/_shared.ts:50-59` — the composite-FK comment explaining why FKs
  between tenant tables can't be single-column.
- `invai-backend/src/db/client.ts:8-13` — the two drizzle instances: `db` (app role, RLS
  enforced) and `systemDb` (owner role, bypasses RLS — migrations, seed, outbox relay only).
- `invai-backend/src/lib/queues.ts:17-28` — the Redis connection options BullMQ requires, the
  five queue names, and their concurrency table.
- `invai-infra/local/docker-compose.yml:9,25` — the pinned Postgres (`pgvector/pgvector:pg17`)
  and Valkey (`valkey/valkey:8`) images the local stack runs.
- `invai-docs/research/06-tools-backend.md:54-77,88-120` — the full scored comparison tables
  this lesson draws from.

## 5. What it uses
- **drizzle-orm / drizzle-kit 0.45.3 / 0.31.11** — the ORM and migration generator; RLS
  policies live in the same schema files as table definitions.
- **Postgres 17 (with pgvector)** — the actual database; RLS is a first-class Postgres
  feature drizzle exposes typed helpers for, not something bolted on.
- **Valkey 8** — the Redis-compatible store backing BullMQ, chosen for its open license;
  functionally identical to Redis for this project's purposes.
- **BullMQ 6.3.8** — the job queue; picked as the cheapest, most TypeScript-native option at
  every volume this project is likely to reach, with a Python client available if
  `invai-imaging` ever needs to consume jobs directly instead of being called over HTTP.

## 6. Try it yourself
1. Open `invai-backend/src/db/schema/finance.ts` (or any schema file) and find where it calls
   `tenantPolicy("<table name>")` — confirm the table name argument matches the `pgTable(...)`
   name right above it.
2. With the local stack up, run
   `docker exec -it $(docker compose -f invai-infra/local/docker-compose.yml ps -q valkey) valkey-cli ping`
   — a `PONG` confirms Valkey is answering BullMQ's protocol.
3. Read `invai-backend/src/lib/queues.ts`'s `QUEUE_CONCURRENCY` table and guess, before
   checking elsewhere, why `reports` gets a concurrency of 1 while `sync` gets 10 — think about
   what kind of work (and what kind of resource contention) each queue name suggests.

## 7. Common mistakes
- Thinking RLS is optional per-table and only needed for "sensitive" data. `CLAUDE.md`'s rule
  7 and the `rls-coverage.test.ts` test (module 04) make this non-negotiable: **every** table
  with a `company_id` column must have RLS, full stop, or a test fails in CI.
- Writing a tenant-to-tenant foreign key the "normal" way
  (`.references(() => parentTable.id)`). Per `_shared.ts:49-58`, this is a real leak vector
  because FK constraint checks run with elevated privilege and ignore RLS. Module 04 lesson 2
  covers the composite-key pattern that replaces it.
- Assuming BullMQ gives you per-tenant fair scheduling "for free." Research
  (`06-tools-backend.md:88`) is explicit that BullMQ OSS needs either BullMQ Pro's Groups
  feature or a hand-built Redis token bucket for per-connection/per-tenant rate limiting —
  module 06 covers how InvAI actually does this.

## 8. Check yourself
<details>
<summary>1. What's the core difference between how Drizzle and Prisma handle Postgres RLS,
and why did that matter for InvAI's choice?</summary>

Drizzle exposes RLS policies as typed schema helpers (`pgPolicy`), generated into migrations
alongside the table — so a policy change is reviewed in the same file as the table it
protects. Prisma manages RLS through raw SQL migrations outside its own schema/type system,
which is an easier place for a new table to slip through without one.
</details>

<details>
<summary>2. Why did Temporal, Inngest and Trigger.dev all score lower than BullMQ for
InvAI specifically, despite being more fully-featured durable-execution platforms?</summary>

They bill per execution or per step, which gets expensive fast at InvAI's actual load shape:
frequent, short polling jobs (order sync every 5-10 minutes per connection) rather than a
small number of long workflows.
</details>

<details>
<summary>3. Why does `invai-infra` run Valkey instead of Redis?</summary>

Valkey is Redis-protocol-compatible (BullMQ can't tell the difference) but ships under a fully
open-source license, unlike Redis's more recent licensing changes.
</details>

## 9. Words to know
- **drizzle-kit** — drizzle's migration generator; reads the schema files and produces SQL
  migration files plus a journal (module 04 covers this in detail).
- **`pgPolicy`** — drizzle's typed representation of a Postgres RLS policy, defined as part of
  a table's schema.
- **Valkey** — an open-source, Redis-protocol-compatible in-memory store; a drop-in
  replacement for Redis in this project.
- **BullMQ `jobId`** — a stable, deterministic key for a job, used as the idempotency
  mechanism so enqueuing the same logical job twice doesn't run it twice (module 06).
