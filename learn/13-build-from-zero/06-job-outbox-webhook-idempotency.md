# Lesson 13.6 — A background job, the outbox, a webhook, idempotency

## 1. In one sentence
You'll move a slow or outward-facing piece of work off the request/response cycle
and onto a BullMQ queue; make it reliably *follow* a database change using a
transactional outbox instead of calling it directly inside the request; and make a
webhook endpoint (and the job it triggers) safe to receive or run twice.

## 2. Why it exists
Three different problems, one connected fix:

1. **Heavy work shouldn't block a request.** Composing an image, calling a carrier
   API, pushing tracking to a marketplace — none of these should make a user's
   browser wait. `CLAUDE.md`'s rule is direct: "Heavy work goes to the job queue."
2. **A side effect needs to happen *because* a database change happened, reliably —
   even if the process crashes right after the change commits.** Calling a job
   directly after a database write, in the same function, has a gap: if the process
   dies between "the write committed" and "the job got enqueued," the job never
   runs, and nothing noticed. The **outbox pattern** closes that gap: the event row
   is written in the *same transaction* as the data change, so it either both
   commits or neither does.
3. **Networks retry, and retries duplicate.** A webhook sender resends when it
   doesn't get a fast 200; a crashed worker's job gets retried by BullMQ itself. If
   "receive a webhook" or "run a job" isn't safe to happen twice, a shop ends up with
   two labels bought, or a double-counted event. `CLAUDE.md`'s rule: "Webhooks,
   payments, labels, tracking pushes and scans are idempotent."

## 3. How it works

### Step 1 — a queue and a job
```bash
pnpm add bullmq ioredis
```
```ts
// src/lib/queue.ts
import { Queue, Worker } from "bullmq";
import { Redis } from "ioredis";

const redis = new Redis("redis://localhost:6380", { maxRetriesPerRequest: null });
export const renderQueue = new Queue("render", { connection: redis });

export const worker = new Worker("render", async (job) => {
  console.log("rendering widget", job.data.widgetId);
}, { connection: redis });
```
A **stable `jobId`** is what makes a job safe to enqueue twice: BullMQ treats two
`.add()` calls with the same `jobId` as "the same job" — the second is a no-op, not
a duplicate run.
```ts
await renderQueue.add("render-widget", { widgetId }, { jobId: `render-${widgetId}` });
```

### Step 2 — the outbox table and `emit()`
```ts
// src/db/schema.ts (add)
export const outboxEvents = pgTable("outbox_events", {
  id: uuid().primaryKey().defaultRandom(),
  companyId: uuid("company_id").notNull(),
  name: text().notNull(),
  payload: jsonb().notNull(),
  processedAt: timestamp("processed_at", { withTimezone: true }),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});
```
```ts
// src/lib/outbox.ts
export async function emit(tx: Tx, companyId: string, name: string, payload: object) {
  await tx.insert(outboxEvents).values({ companyId, name, payload });
}
```
Call `emit()` **inside** the same `withTenant` transaction as the data change:
```ts
await withTenant(companyId, async (tx) => {
  const [row] = await tx.insert(widgets).values(input).returning();
  await emit(tx, companyId, "widget.created", { widgetId: row.id });
  return row;
});
```
A tiny relay, run on a timer, moves unprocessed rows into real jobs:
```ts
async function relay() {
  const pending = await db.select().from(outboxEvents).where(isNull(outboxEvents.processedAt));
  for (const event of pending) {
    if (event.name === "widget.created") {
      await renderQueue.add("render-widget", event.payload, { jobId: `render-${event.id}` });
    }
    await db.update(outboxEvents).set({ processedAt: new Date() }).where(eq(outboxEvents.id, event.id));
  }
}
```

### Step 3 — an idempotent webhook
```ts
app.post("/webhooks/vendor", async (c) => {
  const deliveryId = c.req.header("x-delivery-id");
  if (!deliveryId) return c.json({ error: "missing delivery id" }, 400);

  const inserted = await db
    .insert(webhookDeliveries)
    .values({ deliveryId })
    .onConflictDoNothing()
    .returning();
  if (inserted.length === 0) return c.json({ ok: true }); // already handled — 200, do nothing

  // ... do the actual work, inside its own withTenant/outbox transaction ...
  return c.json({ ok: true });
});
```
`onConflictDoNothing()` against a `UNIQUE` column is the whole trick: the *first*
delivery of a given id inserts and proceeds; every redelivery of the same id hits the
conflict, inserts nothing, and returns 200 immediately without doing the work again.

### Step 4 — exercise it for real
```bash
curl -s -X POST localhost:3100/webhooks/vendor -H 'x-delivery-id: abc123' -d '{}'
curl -s -X POST localhost:3100/webhooks/vendor -H 'x-delivery-id: abc123' -d '{}'
# both return {"ok":true}; check your job/event tables -- the work happened exactly once
```

## 4. In our code
- `invai-backend/src/lib/queues.ts:157-172` — the real `defineJob()`: it parses
  input with the job's own Zod schema, computes a `backoff` with jitter, and passes
  `jobId: jobId ? safeJobId(jobId) : undefined` to BullMQ's `.add()` — the exact
  stable-id trick your Step 1 used by hand.
- `invai-backend/src/modules/shipping/jobs.ts:44-62` — a real job,
  `pushTrackingJob`: `jobId: (i) => \`push-tracking-${i.shipmentId}-${i.attempt}\`,
  options: { attempts: PUSH_MAX_ATTEMPTS, backoff: { type: "exponential", delay:
  5_000 } }`.
- `invai-backend/src/lib/outbox.ts:14-37` — the real `emit()`: validates the payload
  against the event's real schema from `@invai/contracts`, inserts into
  `outbox_events` in the same transaction `tx` the caller is already inside — note it
  takes `tx`, not `db`, so it's structurally impossible to call outside a transaction.
- `invai-backend/src/lib/queues.ts:292-299` — `onEvent(eventName, job, map)`: the
  real relay subscription your hand-written `if (event.name === ...)` block was a
  tiny version of — "a job with its own `jobId` keeps it, so two events that map to
  the same input collapse into one pending job."
- `invai-backend/src/api/webhooks.ts:20-33` and
  `invai-backend/src/modules/channels/sync.ts:693-705` — the real pattern: verify
  signature first (401, nothing written), then `recordWebhookDelivery()` —
  `.insert(webhookDeliveries).values({ channel, deliveryId }).onConflictDoNothing()`
  — exactly your Step 3's trick, with a `forgetWebhookDelivery()` undo path if the
  job fails to enqueue after the row is recorded.
- `invai-docs/team/skills/idempotent-job/SKILL.md`, `idempotent-side-effect/SKILL.md`
  — the full playbooks: stable `jobId` plus a *database-level* idempotency check
  (unique key, upsert, state guard) together, because BullMQ's own dedup only
  prevents a duplicate *enqueue*, not a duplicate *effect* if the same job input
  reaches the handler two different ways.

## 5. What it uses
- **BullMQ** on **Valkey/Redis** — a job queue with retries, backoff and stable job
  IDs; module 03.2 covers why a real queue over "just call it and hope," and the
  "shared Redis flakes" incident (lesson 13.13) covers a real failure this caused
  when two agents' test suites shared one Valkey instance.
- **Outbox pattern** — writing an event in the same transaction as the data change
  it describes, so a crash can never separate "the change happened" from "the event
  was recorded."
- **`onConflictDoNothing()`** (a drizzle/Postgres `ON CONFLICT DO NOTHING` upsert) —
  the simplest reliable idempotency primitive: a unique column plus one `INSERT`
  statement.

## 6. Try it yourself
1. Kill your worker process mid-job (after it logs "rendering" but before it
   finishes) and restart it. Does the same job run again? Check BullMQ's stalled-job
   behavior (`lockDuration`, `stalledInterval`) — this is the real mechanism that
   decides whether a crashed worker's job is retried.
2. Remove the `onConflictDoNothing()` from your webhook handler and send the same
   `x-delivery-id` twice. Count how many rows land in whatever table "the work" wrote
   to — then put the idempotency check back and confirm it's exactly one.
3. `grep -n "export function onEvent" invai-backend/src/lib/queues.ts` then read the
   comment above it about two events mapping to the same job input collapsing into
   one pending job — write down, in your own words, what problem that specifically
   prevents.

## 7. Common mistakes
- Calling the job directly after a database write, in the same function, instead of
  through the outbox. It looks identical in the happy path — the gap only shows up
  on a crash at exactly the wrong moment, which makes it easy to ship and genuinely
  hard to notice in testing.
- Treating "BullMQ dedupes by `jobId`" as the whole idempotency story. It prevents a
  duplicate *job* from being enqueued twice with the same id — it does nothing if
  the *same real-world event* reaches your system through two different paths (a
  webhook redelivery *and* a polling backstop, say) with two different job ids. The
  database-level check (a unique key on the actual thing being deduplicated) is what
  catches that.
- Sharing one Redis/Valkey instance across unrelated test suites or agents running
  in parallel. This project's own lesson log has a real incident from exactly this —
  two agents' tests both touching the same queue names caused confusing, hard-to
  -reproduce flakes. Point each isolated test run at its own Redis database/number.

## 8. Check yourself
<details>
<summary>1. Why does <code>emit()</code> require a transaction (<code>tx</code>)
rather than accepting the plain <code>db</code> connection?</summary>

So the event row can only ever be written as part of the same transaction as the
data change it describes — either both the data change and the event commit
together, or (on a rollback) neither does. Accepting a plain connection would make it
possible to call `emit()` outside any transaction, reopening the exact crash gap the
outbox pattern exists to close.
</details>

<details>
<summary>2. A webhook sender redelivers the same event because it never saw your
200 response (maybe it arrived late). What should happen on the retry?</summary>

The delivery id should already be recorded from the first attempt, so the
`onConflictDoNothing()` insert finds nothing new to insert, the handler returns 200
immediately, and the real work (whatever it is) does not run a second time — even
though, from the sender's point of view, this looks like a fresh delivery.
</details>

<details>
<summary>3. What's the difference between BullMQ's <code>jobId</code> dedup and a
database-level idempotency check, and why do you need both?</summary>

`jobId` dedup prevents the *same enqueue call* from creating a second pending job —
useful but narrow. A database-level check (a unique constraint, an upsert, a state
guard) prevents the *effect* from happening twice regardless of how the handler got
invoked — including cases `jobId` dedup can't see, like two different events mapping
to the same real-world action, or a handler being called directly in a test.
</details>

## 9. Words to know
- **BullMQ** — a Redis/Valkey-backed job queue library for Node, with retries,
  backoff and stable job IDs.
- **Outbox (transactional outbox)** — writing an event row in the same database
  transaction as the change it describes, so a relay can reliably turn it into a job
  later without ever losing it to a crash.
- **Idempotent** — safe to do more than once with the same input, because repeating
  it produces no additional effect beyond the first time.
- **`jobId`** — a stable identifier passed to a job queue so that enqueuing the
  "same" job twice collapses into one.
- **`onConflictDoNothing()`** — a database upsert that silently does nothing when a
  unique-column conflict is hit, instead of erroring — a simple idempotency
  primitive.
