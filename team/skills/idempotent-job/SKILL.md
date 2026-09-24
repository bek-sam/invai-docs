---
name: idempotent-job
description: Write or change a BullMQ job in invai-backend that is safe to run twice - stable jobId, DB-level idempotency (unique key, upsert, state guard), retries with jitter, UnrecoverableError for permanent failures, per-tenant withTenant, and a run-twice test. Use for "defineJob", "onEvent", "worker", "queue", "background job", "retry", "backfill".
---

# Idempotent job

A job whose second run (a retry, a re-relayed outbox event, a duplicate enqueue) changes nothing, and whose
permanent failures stop retrying and show up in the failed set.

## When to use
- Adding a `defineJob` or `onEvent` in `src/modules/<area>/jobs.ts`, or changing a handler.
- Any heavy work (renders, labels, imports, AI batches): it belongs in a job (owner rule 9).
- For a job that calls an outside API that costs money, sends email or pushes tracking, also follow
  `idempotent-side-effect`.

## Facts that shape this
- `defineJob` (`src/lib/queues.ts`) passes `jobId` through `safeJobId()` because BullMQ forbids `:`.
- The outbox relay (`src/worker/outbox-relay.ts`) enqueues each subscriber with `jobId = ${eventId}:${jobName}`. It is at-least-once: it can enqueue and crash before marking the row dispatched.
- **BullMQ dedupes a `jobId` only while the job still exists in Redis.** Defaults are `removeOnComplete: { age: 24h, count: 5000 }` and `removeOnFail: { age: 7d }`. At growth volume the `count: 5000` cap can drop a
  completed job within minutes, and then the same `jobId` runs again (research 11 §3.1, G11). So the jobId is
  a cheap first filter, never the guarantee.
- `DEFAULT_JOB_OPTIONS` has `attempts: 5` and exponential backoff **without jitter**, and nothing throws
  `UnrecoverableError` yet (research 11 G9, backlog B-17). A Zod failure today retries 5 times.
- The worker (`src/worker/index.ts`) parses input with the job's schema and logs failures without `companyId`.
- Outbox events can arrive out of order. Handlers must re-read current state, never trust the event payload's
  snapshot.

## Steps
1. **Input:** a Zod object that carries `companyId` plus ids only (no PII, no big payloads; job data sits in
   Redis). Never take `companyId` from an unverified webhook body.
2. **jobId:** a stable key from the business identity: `push-tracking-${shipmentId}`, `design-qa-${designId}`.
   Add a version or attempt suffix only when a genuinely new run is intended (as `shipping.pushTracking` does
   with `attempt`).
3. **Handler enters the tenant:** `withTenant(companyId, (tx) => svc.fn(tx, systemContext(companyId), ...))`.
   `withSystem` only for cross-tenant fan-out that reads ids and then enqueues per-tenant jobs.
4. **Make the effect idempotent in the database**, choosing one:
   - **Natural unique key + upsert:** `insert(...).onConflictDoNothing()` or `.onConflictDoUpdate({ target: [t.companyId, t.key], set })`. Example: `inventory_movements.idempotency_key` in
     `modules/inventory/ledger.ts` (`reserve:order_item:${id}:${n}`).
   - **State guard under a row lock:** `select ... .for("update")`, return early if already done (`if (s.trackingPushStatus === "pushed") return "skipped"`), then update in the same transaction. Item states
     change only through `transitionItem`, which rejects an invalid repeat.
   - **Deterministic output keys:** renders write `sheets/{companyId}/{sheetId}/{version}.png`-style keys so a
     rerun overwrites (research 11 §6.4).
5. **Classify failures:**
   - Permanent (Zod parse error, 4xx validation from a provider, entity not found, revoked OAuth, plan limit):
     `throw new UnrecoverableError(msg)` from `bullmq`, after recording the reason on the entity (e.g.
     `lastError`) so a person can see it.
   - Transient (5xx, timeout, 429, imaging down): throw a normal error to retry, or return early and leave the
     entity pending (the catalog QA job returns `{ skipped: true }` when `imaging.isUp()` is false).
   - Check the installed API in `node_modules/bullmq` before using it (BullMQ 6 is newer than training data).
6. **Retries with jitter:** set `options: { backoff: { type: "exponential", delay: 2_000, jitter: 0.5 } }` on
   your job until backend-foundation adds jitter to `DEFAULT_JOB_OPTIONS` (B-17). Use few attempts with long
   delays for `ship` work a human should look at; more attempts for `sync`.
7. **Timeouts:** every external call inside the handler has an `AbortSignal.timeout(...)`, shorter than the
   worker's lock duration, or BullMQ marks the job stalled and runs it twice.
8. **Fairness:** bulk jobs (imports, batch AI, backfills) get a lower `priority` than interactive ones (label
   buy, single render) (research 11 §3.4).
9. **Test it twice** with `runJobInline(job, input)` against `invai_test`:
   ```ts
   await runJobInline(myJob, input);
   await runJobInline(myJob, input);
   expect(await countEffects()).toBe(1);   // one row, one movement, one push
   ```
   Also test: a permanent failure throws `UnrecoverableError`; the handler run for tenant A can't touch tenant
   B's rows.
10. **Exercise it for real:** start the worker (`pnpm dev:worker`), trigger the event, and watch the log line
    `job done`; then enqueue the same input again and confirm nothing changed.

## Rules (MUST / MUST NOT)
- MUST back every jobId with a DB unique key, upsert or state guard. MUST NOT rely on BullMQ dedupe alone.
- MUST NOT assume event order or that an event is delivered once.
- MUST NOT hold a DB transaction open across a slow external call (see `idempotent-side-effect`).
- MUST NOT put buyer PII in job data or error messages.
- MUST NOT retry permanent failures, and MUST NOT swallow transient ones silently.
- MUST use `logger("<area>.jobs")` with `companyId` in the context, never `console.*`.

## Done when
- The handler has a run-twice test asserting one effect, and a permanent-failure test.
- The jobId is stable, the DB guard is named in the report, and backoff has jitter.
- The job ran for real in the worker, including a duplicate enqueue.
- `pnpm typecheck && pnpm lint && pnpm test` pass in `invai-backend`.

## References
- `invai-backend/src/lib/queues.ts`, `src/worker/index.ts`, `src/worker/outbox-relay.ts`,
  `src/modules/README.md` ("Job pattern")
- Worked examples: `src/modules/catalog/jobs.ts`, `src/modules/shipping/jobs.ts`,
  `src/modules/inventory/ledger.ts`
- `invai-docs/research/11-platform-scale-playbook.md` §3.1–3.4, §10 G9–G12
- Related: `idempotent-side-effect`, `zero-downtime-migration` (backfills), `root-cause-bug`
