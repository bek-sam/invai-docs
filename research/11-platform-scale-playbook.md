# InvAI platform scale playbook: from 1 shop to 10,000 (researched 2026-09-24)

This playbook tells each role what to do, and when, so InvAI runs well at every size without
building for 10,000 shops on day one. Every rule is a **MUST** (skipping it causes an outage,
a data leak or unbounded cost) or a **SHOULD** (the default; deviate only with a written
reason in `v1-plan.md` §6).

**How this was checked**
- Code claims come from reading the repos on 2026-09-24. File paths are given so you can re-check them.
- External claims link to the source in brackets, for example [S3], and the full list is in §10.
- "Verify" marks behavior I could not confirm without a live AWS account.

**Stages used throughout**

| Stage | Shops | Rough load (assumes 50–300 orders/day per shop) | What matters most |
|---|---|---|---|
| **Now: pilot** | 1–20 | <10k orders/day, <1 job/s on average | Correctness, tenant isolation, backups, knowing when something breaks |
| **Next: growth** | 100s | ~50k orders/day, ~5–20 jobs/s, peaks 10x | Fairness between tenants, connection limits, safe deploys, SLOs |
| **Later: scale** | 1,000s–10,000 | ~0.5–2M orders/day, ~25–250 jobs/s | Limiting how far one failure spreads (cells), per-tenant cost, larger-tenant isolation |

Even 10,000 shops (about 2M orders/day, about 23 writes/s on average) fits within what one
well-sized Postgres primary can handle. **Cells at "later" limit how far one failure spreads;
raw throughput is not the reason for them.** Don't shard for throughput before the metrics in
§1 say so.

---

## 0. The 15 rules that matter most

1. **MUST** run the app in AWS as `invai_app`, which has no BYPASSRLS. Today `sst.config.ts` points `DATABASE_URL` at the RDS master user, so **RLS is off in AWS** (P0 gap).
2. **MUST** put a timeout on every Postgres call: `statement_timeout`, `idle_in_transaction_session_timeout` and `lock_timeout`, set on the role [S7].
3. **MUST** make every job handler idempotent at the database level, using unique keys and upserts. BullMQ `jobId` deduplication only lasts as long as the job is retained [S12, S13].
4. **MUST** add jitter to every retry. Send permanent failures to `UnrecoverableError` so they aren't retried, and alert on the failed set, which serves as InvAI's dead-letter queue (DLQ) [S10, S11].
5. **MUST** give no single tenant more than its fair share of a shared worker pool. Cap per-tenant concurrency now, and add BullMQ Pro Groups or equivalent at growth [S14, S15].
6. **MUST** purge dispatched outbox rows and alert on parked (failed) ones. Today neither happens.
7. **MUST** change the schema only with expand/contract. Run migrations as a separate step before the app rolls out, with `lock_timeout` set. Build indexes with `CONCURRENTLY` outside drizzle's single migration transaction [S16, S17].
8. **MUST** deploy with the ECS deployment circuit breaker and CloudWatch alarm rollback. Split `/livez` from `/readyz`, and drain gracefully on SIGTERM [S19, S20].
9. **MUST** tag every log line, span and metric with `company_id`, `request_id` and `trace_id`. Propagate trace context through the outbox, BullMQ and imaging [S22, S23].
10. **MUST** alert on SLO burn rate (multiwindow, multi-burn-rate), not on raw errors or CPU [S25].
11. **MUST** configure Valkey with `maxmemory-policy noeviction`, a node-based deployment and **cluster mode disabled**. BullMQ needs this, and SST's default does not provide it [S29, S30].
12. **MUST** set RDS backup retention to at least 14 days (35 for production), enable deletion protection and **test a restore every quarter**. SST's default is 7 days [S31].
13. **MUST** keep hard per-tenant budgets on AI spend (the credits ledger already does this). Add a global daily spend circuit breaker, and send bulk AI work through the Batch API [S35, S36].
14. **SHOULD** measure cost per tenant from day one: AI cents, render seconds, job counts, S3 bytes by `companyId/` prefix. Allocate shared infrastructure proportionally [S33, S34].
15. **SHOULD** load-test with k6 arrival-rate scenarios that encode the SLOs as thresholds before each stage transition [S27].

---

## 1. Stage triggers: move up a stage when a metric says so, not by calendar

| Signal (from CloudWatch or your metrics) | Threshold | Action |
|---|---|---|
| RDS CPU p95 over a busy hour | >60% for a week | Go up one instance size (vertical first) |
| RDS `DatabaseConnections` | >70% of `max_connections` | Add a pooler (§2.2) before adding API tasks |
| Queue wait time p95 (`sync`, `render`) | >2x its SLO for 3 days | Scale workers; check per-tenant fairness (§3.4) |
| One tenant's share of queue work or DB time | >20% for a day | Throttle that tenant; consider isolating it (§2.5) |
| Single table size (`order_items`, `outbox_events`, `audit_log`) | >50–100 GB or vacuum falling behind | Partition by time, or archive |
| Valkey memory | >60% | Scale the node; look for leaked `removeOn*` jobs |
| Shops | ~100 | Growth checklist: Multi-AZ, pooler, fairness, SLO alerts |
| Shops | ~1,000 or first enterprise contract | Plan cells (§2.6) and dedicated-tenant options |

---

## 2. Multi-tenant Postgres

### 2.1 RLS: correctness and performance

**What the code already does well**
- Every tenant table has `company_id` and a `tenantPolicy()` (`src/db/schema/_shared.ts`).
- A test fails when any table is missing RLS (`src/db/rls-coverage.test.ts`).
- `withTenant()` uses transaction-local `set_config(..., true)` (`src/db/client.ts`), which is safe with transaction pooling [S3, S5].
- The app role is not the table owner locally (`invai-infra/local/init.sql`).
- Composite indexes lead with `company_id`.

**Rules**
- **MUST (now)** give production the same role setup as local. `sst.config.ts` sets `DATABASE_URL = MIGRATION_DATABASE_URL = master user`, which bypasses RLS. Add a bootstrap step that creates `invai_app` (NOLOGIN plus a login role, `NOBYPASSRLS`, grants only) and a separate `invai_system` role for the relay and cross-tenant jobs. Point `DATABASE_URL` at `invai_app`. Consider `ALTER TABLE ... FORCE ROW LEVEL SECURITY` so that even the owner is filtered when `app.company_id` is set [S1, S2].
- **MUST** keep policy predicates to plain equality on `company_id` against a STABLE expression, as `currentCompanyId` does now. A policy that calls a non-LEAKPROOF function, or uses `LIKE` or a subquery, stops the planner from pushing the user's selective `WHERE` into an index scan [S1, S2]. Any new policy (for example the vendor `IN (select ...)` policy in `vendors.ts`) needs an `EXPLAIN (ANALYZE, BUFFERS)` check against a table with 1M+ rows across 1,000 fake tenants before merge.
- **MUST** make `company_id` the leading column of every index used by tenant queries. **Gap:** the trigram GIN indexes (`orders_order_no_trgm_idx`, `order_items_channel_sku_trgm_idx`, `designs_name_trgm_idx`, in `drizzle/0001_grants_extensions.sql`) span all tenants. At 1,000s of tenants, a short search term matches rows in every tenant and RLS filters them afterwards. **Next:** use `btree_gin` composite indexes, `(company_id, col gin_trgm_ops)`, or tenant-first btree prefix search.
- **SHOULD** keep `withSystem` usage small and audited. Today it covers the relay, the poll fan-out and the PII purge. Every cross-tenant job should read a list of IDs as system, then do per-tenant work inside `withTenant`.
- **SHOULD (later)** consider timing side channels (a query's duration can reveal whether rows exist in another tenant) only for features that expose query timing across tenants [S2]. It's low risk for InvAI today.

### 2.2 Connections and pooling with RLS

**Facts**
- Transaction pooling (PgBouncer, or RDS Proxy multiplexing) is safe only with `SET LOCAL` or `set_config(..., true)`. InvAI already uses those [S5].
- PgBouncer ≥1.21 supports protocol-level prepared statements in transaction mode through `max_prepared_statements` [S6].
- **RDS Proxy pins the session for PostgreSQL on `SET` and `set_config`.** AWS's own docs say "for PostgreSQL setting a variable leads to session pinning", and PostgreSQL has no pinning filter, unlike MySQL [S3, S4]. Because `withTenant` runs `set_config` on every request, **the production RDS Proxy (`proxy: isProd`) will pin essentially every connection**, so it adds cost and latency without multiplexing. The same doc also says calls to stored functions are not inspected for session changes [S3]. A `SECURITY INVOKER` function `app.enter_tenant(uuid)` that calls `set_config('app.company_id', $1, true)` would probably avoid pinning, and it stays safe because the setting is transaction-local. **Verify** with the `DatabaseConnectionsCurrentlySessionPinned` metric before relying on it.

**Rules**
- **MUST (now)** do the connection math before scaling tasks:
  - Each process opens `appPool max 10` + `systemPool max 4` (`src/db/client.ts`).
  - The API can scale to 6 tasks, plus the worker: 7 × 14 = **98 connections**.
  - SST's default RDS instance is `t4g.micro` (`.sst/platform/src/components/aws/postgres.ts`), which has roughly 80–110 `max_connections`.
  - So set `instance` explicitly (for example `t4g.medium` for the pilot), and set `max` from an env var so that tasks × pool stays under 70% of `max_connections`.
- **MUST (now)** set timeouts on the role, not per query, so they survive any pooler (Postgres docs [S7]):
  ```sql
  ALTER ROLE invai_app SET statement_timeout = '15s';
  ALTER ROLE invai_app SET idle_in_transaction_session_timeout = '30s';
  ALTER ROLE invai_app SET lock_timeout = '5s';
  ALTER ROLE invai_system SET statement_timeout = '5min';   -- purge, reports
  ```
  Long reports use `SET LOCAL statement_timeout` inside their own transaction.
- **SHOULD (now)** drop RDS Proxy for the pilot, or keep it only for its failover benefit and accept the pinning. Direct connections with correctly sized pools are simpler.
- **SHOULD (next)** add a pooler once there are more than about 10 tasks: PgBouncer 1.21+ in transaction mode as a small ECS service, or the stored-function trick above behind RDS Proxy (verify it first). Never use session-level `SET` [S5, S6].
- **SHOULD (next)** send heavy read-only reports (profit, exports) to a read replica through a separate `readPool`, still going through `withTenant`.

### 2.3 Noisy neighbors, rate limits and quotas

**What exists**
- Plan limits (`planLimit` in `src/modules/billing/service.ts`).
- AI credits per company (`src/ai/credits.ts`).
- Better Auth per-IP limits on auth routes (`src/auth.ts`). Better Auth's default storage is in-memory, so each task counts separately. **Verify** this, and use Valkey storage when there is more than one task.
- PIN brute-force lockout (`src/lib/ratelimit.ts`).

**Missing:** there is no per-tenant API rate limit and no per-tenant work quota.

**Rules**
- **MUST (now)** add a per-tenant API rate limit (a Valkey token bucket or GCRA, keyed by `company_id`). Keep a separate, higher limit for the floor's station tokens and a stricter one for exports and bulk actions. Return `429` with `Retry-After`. Stripe's layered model is a good template: a request-rate limiter, a concurrent-request limiter, and load shedding that keeps critical traffic flowing [S8].
- **MUST (now)** enforce size quotas at the edge of every bulk action: CSV import rows, items per gang sheet, AI batch size, and files per upload. The file path already has type and byte limits (`src/modules/files/service.ts`).
- **SHOULD (next)** use the AWS fairness playbook: quotas per tenant, admission control before expensive work, and priority for interactive traffic over background traffic [S9].
- **SHOULD (next)** keep per-tenant statistics (`pg_stat_statements` doesn't know tenants). Record DB time per request in the access log, tagged with `company_id` (§5), and review the top-10 tenants by DB time every week.

### 2.4 Big tables and data lifecycle

- **MUST (now)** delete dispatched `outbox_events` rows older than 7 days in batches, from a `reports` scheduler job. **Gap:** nothing deletes them today, so the table grows by one row per state change forever. The partial index keeps the relay fast, but vacuum, backups and PITR restore time all grow with the table.
- **SHOULD (next)** partition append-only, high-volume tables (`outbox_events`, `audit_log`, scan events, `ai_jobs`) by month with native declarative partitioning, and drop old partitions instead of deleting rows.
- **SHOULD (next)** tune autovacuum on hot tables (`order_items`, `stock_levels`): set a lower `autovacuum_vacuum_scale_factor` per table.

### 2.5 Large-tenant isolation

- **SHOULD (next)** give each tenant a `tier` (`pooled` | `priority` | `dedicated`) on `companies`. It does nothing yet, but lets routing code grow into it.
- **SHOULD (later)** move a tenant to a dedicated cell (below) rather than a dedicated database *table* design. Keep one schema everywhere, so a "dedicated" tenant is the same code with a different connection string and queue prefix [S37, S38].

### 2.6 Sharding and cells (later only)

- **Don't shard before the §1 triggers.** A single RDS/Aurora primary plus replicas carries InvAI well into the 1,000s of shops.
- **When needed, use cells, not Citus-style row sharding.** A cell is a full stack (Postgres, Valkey, workers, imaging) serving a set of tenants. A thin routing layer maps `company_id` to a cell. Keep the map in a small global table cached at the edge or API. Benefits:
  - One bad deploy or one runaway tenant takes out at most one cell.
  - Every tenant query already carries `company_id`, so there are no cross-cell joins.
  - AWS recommends cells for multi-tenant SaaS in exactly this shape [S37, S38].
- Citus schema-based sharding is the alternative if you want one logical database. Citus itself advises it for "not to exceed several thousand" tenants, and it makes managed-RDS portability harder [S39].
- **Prerequisites to build now, because they are cheap:**
  - No cross-tenant queries on the request path.
  - Global tables (plans, trademark marks) are read-only and replicable.
  - S3 keys are already `companyId/...`, which is good.
  - Jobs always carry `companyId` in their input, which they already do.

---

## 3. Queues, outbox and jobs

**What the code already does well**
- The transactional outbox is written in the same transaction as the change (`src/lib/outbox.ts`).
- The relay uses `FOR UPDATE SKIP LOCKED`, so several relays can run safely (`src/worker/outbox-relay.ts`).
- The relay gives each job the ID `${eventId}:${jobName}`.
- Jobs are validated by schema at enqueue and in the worker.
- Default `attempts: 5` with exponential backoff (`src/lib/queues.ts`).
- Webhooks are acknowledged fast and deduplicated on `X-Shopify-Webhook-Id` (`src/api/webhooks.ts`).
- There is an idempotency key on inventory movements (`modules/inventory/ledger.ts`).

### 3.1 Exactly-once is an illusion: design for at-least-once

- The outbox guarantees at-least-once publication. The relay can enqueue a job and then crash before it marks the row dispatched [S12, S13].
- BullMQ's `jobId` deduplication only works while that job still exists in Redis. The defaults are `removeOnComplete: { age: 24h, count: 5000 }`, so at growth volumes a completed job can be removed within minutes. **A re-relayed event after that point runs the handler again.**
- **MUST (now)** make every handler with side effects idempotent at the **database or provider** level:
  - Use unique constraints on natural keys (`shipment_id` for labels, `(connection_id, channel_order_id)` for imports).
  - Use `INSERT ... ON CONFLICT DO NOTHING` and check state before transitions (`where state = 'packed'`).
  - Pass an idempotency key to external APIs that accept one. EasyPost label purchase should be guarded by our own `shipments.label_purchased_at` check inside a row lock [S13].
- **MUST** have a unit test for each handler that runs it twice with the same input and asserts one effect.
- **SHOULD** make handlers idempotent before relying on longer `removeOnComplete` windows, and not the other way round.

### 3.2 Retries, jitter, poison messages and the DLQ

- **MUST (now)** add jitter: `backoff: { type: "exponential", delay: 2000, jitter: 0.5 }` [S10]. Without it, every job that failed during an EasyPost or Shopify outage retries at the same moment when the service comes back [S11].
- **MUST (now)** throw `UnrecoverableError` for failures that will never succeed on retry, so they skip the remaining attempts [S10]. Examples: Zod input failure, 4xx validation errors from providers, a missing entity, revoked OAuth. Today a job whose schema doesn't match retries 5 times.
- **MUST (now)** treat the BullMQ failed set (kept 7 days, `removeOnFail`) as the DLQ:
  - Alert when failed-count growth over 15 minutes exceeds N per queue.
  - Build an admin "redrive" action (retry selected failed jobs) behind `platform.admin`.
  - Record `companyId` in the `failed` log line. Today the worker logs `queue`, `job`, `id` and `attempts`, but not the tenant.
- **MUST (now)** alert on parked outbox events. After 10 failed attempts the relay sets `dispatched_at` and `last_error`, and nothing reads them. Expose `count(*) where last_error is not null and attempts >= 10` and page on any non-zero value.
- **SHOULD** use per-queue attempt counts: `ship` gets few attempts with long delays, because a human should look at it, and `sync` gets many attempts with short delays.
- **SHOULD** set explicit timeouts for every external call. Imaging has 120 s and 600 s for compose, which is good. Add them for Anthropic, EasyPost, Shopify and S&S. The job's lock duration must exceed the longest call, or BullMQ will mark the job stalled and run it twice.

### 3.3 Outbox pitfalls specific to this relay

- **Ordering is not guaranteed.** `created_at` is the transaction's start time, and relays run in parallel. **MUST:** handlers never assume event order. They re-read current state from the database (most already do).
- **A Valkey loss loses enqueued jobs.** ElastiCache has no AOF durability, and the outbox rows are already marked dispatched. **MUST (now)** have a runbook script, "re-drive outbox from time T": reset `dispatched_at` to null for rows in a window. This is safe *only because* handlers are idempotent (§3.1).
- **The relay holds its row locks while it talks to Valkey.** Keep `BATCH = 100` and add a relay-lag metric (the age of the oldest undispatched row). `outboxBacklog()` already computes pending and stale counts, so export them.
- **SHOULD (next)** replace the 500 ms poll with `LISTEN/NOTIFY` as a wake-up signal, keeping the poll as a fallback. **Later:** consider logical-replication CDC only if relay lag becomes a problem.

### 3.4 Fairness across tenants

**Today** all tenants share FIFO queues, with fixed concurrency per process (`sync 10`, `render 2`, `ship 5`, `ai 4`, `reports 1`). One shop importing 5,000 orders or composing 40 sheets delays every other shop's labels.
- **MUST (now), cheap version:**
  - Add a per-tenant concurrency cap using a Valkey semaphore keyed `sem:{queue}:{companyId}`, for example at most 2 renders per tenant. When a job can't take the semaphore, re-delay it with `job.moveToDelayed` and `DelayedError`.
  - Lower the BullMQ `priority` for bulk jobs (imports, batch AI, reports) so interactive jobs (label purchase, a single render) go first.
- **SHOULD (next):** use BullMQ Pro **Groups** with `groupId = companyId`, which processes groups round-robin and gives each group its own rate limit [S14, S15]. The cost is a per-organization licence (price unverified). The free alternative is to shard each hot queue into K sub-queues by `hash(companyId) % K` and have workers consume them round-robin.
- **SHOULD (next):** apply rate limits per external API and per connection, not globally. Shopify limits per store, so its token bucket is keyed by `connectionId`.
- **MUST (next):** spread the poll fan-out. `pollChannelsJob` enqueues every connection in the same instant every 10 minutes (`modules/channels/jobs.ts`). At 10,000 connections that is a 10,000-job burst. Give each job a stable delay of `hash(connectionId) % POLL_EVERY_MS`, and prefer webhooks, keeping the poll as a reconciliation safety net.
- **SHOULD (later):** split the worker into separate ECS services per queue class (`sync+ship`, `render`, `ai`, `reports`) so each scales on its own queue depth and a crash in one doesn't stop the others. Autoscale on BullMQ waiting count or wait-time age exported to CloudWatch, not on CPU.

---

## 4. Migrations, deploys, feature flags

### 4.1 Zero-downtime migrations (expand/contract)

**Facts about the current setup**
- `drizzle-orm`'s migrator applies **all pending migrations inside one transaction** (`node_modules/drizzle-orm/pg-core/dialect.js`). Every lock is held until the last statement finishes, and `CREATE INDEX CONCURRENTLY` can't run there [S16].
- `deploy.yml` has **no migration step**.

**Rules**
- **MUST (now)** follow expand, then migrate code, then contract, spread across **separate deploys**:
  1. **Expand:** add the nullable column, table or index. Old code must still work.
  2. Deploy code that writes both the old and new shape, then reads the new one.
  3. **Backfill** in batches (1–5k rows per transaction, keyed by primary-key range, with a sleep between batches, restartable, run as a `reports` job) [S16, S17].
  4. **Contract:** drop the old column only in a later release, after one full deploy cycle.
- **MUST** set `SET lock_timeout = '5s'` at the start of the migration session and retry on timeout. A DDL statement queued behind a long query blocks every query that arrives after it [S17].
- **MUST** use `ADD CONSTRAINT ... NOT VALID` followed by `VALIDATE CONSTRAINT` for foreign keys and checks on big tables. Never rewrite a column's type in place; use expand/contract.
- **MUST** put `CREATE INDEX CONCURRENTLY` in a separate "online" migration runner, which is a small script that runs files from `drizzle/online/` one statement at a time outside a transaction. Mark each file done in its own table.
- **MUST** run migrations as their own step: a one-off ECS task with the backend image and `node dist/migrate.js`, run **before** the service update. The app must tolerate both the old and new schema (see "expand").
- **SHOULD** add a CI check that fails on dangerous DDL in a new migration file: `ALTER COLUMN TYPE`, `SET NOT NULL` without a prior validated check, `CREATE INDEX` without `CONCURRENTLY` on the listed big tables, and `DROP COLUMN` still referenced in code.

### 4.2 Safe deploys, canary, rollback

- **MUST (now)** enable the ECS deployment circuit breaker with rollback on the api and worker services. Attach CloudWatch **deployment alarms** (5xx rate, p95 latency, job failure rate) so ECS rolls back on application-level regressions, not just crashing tasks [S19, S20].
- **MUST (now)** split health checks:
  - `/livez` checks only the process, and is what the ALB and ECS use.
  - `/readyz` checks the DB and Valkey, and is used by dashboards.
  - Today `/health` checks DB and Redis for the ALB. A 30-second database blip would mark every API task unhealthy at once and ECS would replace them all, a self-inflicted outage.
- **MUST (now)** shut down gracefully:
  - The API server has no SIGTERM handler (`src/api/server.ts`).
  - On SIGTERM: stop accepting new connections, close SSE streams with a retry hint, finish in-flight requests, then exit before ECS `stopTimeout` (raise it to 60–120 s for the worker, so BullMQ `worker.close()` can finish the current jobs; the worker already does this).
- **MUST (now)** add an HTTPS listener (443 with an ACM certificate) and redirect 80 to 443. `sst.config.ts` only has `80/http`.
- **SHOULD (next)** use ECS native blue/green with a bake time and a "dark canary" test listener for risky releases [S18, S19]. Tag releases and keep the previous image for 1-click rollback [S21].
- **SHOULD** make the contracts compatible with one version back and one forward: the web SPA and the floor PWA may be one version behind the API for hours (cached service worker). Only add fields, and never remove or rename a procedure in the same release.

### 4.3 Feature flags

- **SHOULD (now)** keep it tiny: a `feature_flags` table (global plus per-company overrides) cached for 30 s in-process, read through an `isEnabled(flag, companyId)` helper that follows the OpenFeature API shape, so a vendor can be plugged in later [S26].
- **MUST** give every risky change (a new channel adapter, the nesting algorithm, AI prompt versions) a flag that is on for internal and pilot tenants first. Give every flag an owner and a removal date; delete flags within 30 days of reaching 100%.
- **SHOULD (next)** use tenant rings: internal → pilot shops → 10% → 100%, with the same ring list used for flags and for canary cells later.

---

## 5. Observability, SLOs, incidents

### 5.1 What exists
- A structured JSON logger in production (`src/lib/log.ts`).
- A `requestId` generated per request (`src/api/context.ts`), **but it is never logged**.
- There is no access log, no OpenTelemetry package in `package.json`, and no metrics.
- `/health` reports whether each integration is mocked, which is useful.

### 5.2 Rules

- **MUST (now)** carry context through `AsyncLocalStorage`. Set `{requestId, companyId, userId|stationId, traceId}` once in `buildContext` and on job start, and have the logger add it automatically. One access-log line per request: `route, procedure, status, duration_ms, db_ms, company_id`.
- **MUST (now)** add OpenTelemetry:
  - Node SDK with HTTP, pg, ioredis and BullMQ instrumentation (`@appsignal/opentelemetry-instrumentation-bullmq` or equivalent) [S22].
  - Python FastAPI instrumentation in imaging.
  - Store the W3C `traceparent` **in the outbox row's payload metadata** at `emit()`, inject it into BullMQ job data at enqueue, extract it in the worker, and forward it as an HTTP header to imaging. A trace then covers click → API → outbox → relay → job → imaging render → S3 [S22, S23].
  - Follow the OTel messaging semantic conventions for span names and attributes [S23].
  - Export to CloudWatch or X-Ray via the ADOT collector sidecar (cheapest on AWS), or to Grafana Cloud or Honeycomb if you want better querying.
- **MUST** put `company_id` on every span as an attribute. **Never** use it as a metric label on high-volume CloudWatch metrics (cost grows with the number of label values). For per-tenant views, query logs and traces instead.
- **SHOULD** record RED metrics (rate, errors, duration) per procedure and per job name, and USE metrics (utilization, saturation, errors) for RDS, Valkey, the worker and imaging CPU and memory [S24]. Queue saturation equals the age of the oldest waiting job per queue.

### 5.3 SLOs and error budgets (start with 5)

| SLO | Now target | Measured by |
|---|---|---|
| API availability (non-4xx) | 99.5% / 28 d | ALB 5xx + app errors |
| API latency: interactive procedures p95 | <400 ms | Access log |
| Floor scan-to-result p95 (the press scan must feel instant) | <300 ms | Access log for `production.scan*` |
| Label purchase job: enqueued → done p95 | <60 s | Job timings |
| Gang-sheet compose: enqueued → file ready p95 | <5 min for a 240" sheet | Job timings |

- **MUST (next)** alert only on **multiwindow, multi-burn-rate** SLO alerts [S25]:
  - **Page** at a 14.4x burn over both 1 h and 5 min.
  - **Page** at 6x over both 6 h and 30 min.
  - **Ticket** at 1x over 3 days.
- Non-SLO pages are limited to data-safety alarms: parked outbox events, backup failure, RDS storage above 85%, Valkey memory above 80%, and the AI spend breaker tripping.
- **SHOULD** use a spent error budget to trigger a reliability sprint, not blame [S25, S28].

### 5.4 Incident response and postmortems

- **MUST (now)** keep a one-page incident runbook in `runbook.md`:
  - Roles: an incident lead and a communicator, even if they are the same person.
  - Severity levels.
  - A status-page link.
  - "First 5 commands" for each alarm.
- **MUST** hold a blameless postmortem for every SEV1/2 within 5 business days: timeline, impact (which tenants, orders delayed), root causes, and action items with owners [S28]. Store postmortems in `invai-docs/incidents/`.
- **SHOULD** have per-tenant impact queries ready: "which companies had failed jobs or 5xx between T1 and T2". This is the payoff for tagging everything with `company_id`.

---

## 6. Performance, load testing, caching, file pipeline

### 6.1 Performance budgets
- **MUST** hold the latency budgets in §5.3 and these build budgets:
  - Web initial JS ≤ 250 KB gzip.
  - Floor PWA initial JS ≤ 150 KB gzip, time to interactive on a mid-range tablet < 2 s.
  - No oRPC list procedure without pagination. `src/lib/pagination.ts` exists; enforce a max page size of 200.
- **SHOULD** log a warning for any query over 200 ms, including the procedure name. Enable `pg_stat_statements` and RDS Performance Insights (SST already enables Performance Insights).

### 6.2 Load testing with k6
- **MUST (before leaving the pilot)** write k6 scripts with **arrival-rate executors** (open model), with the §5.3 SLOs as `thresholds` so the run fails in CI when a budget is missed [S27]. Scenarios:
  1. The floor scan storm: 20 stations × 1 scan/3 s per shop, times the number of shops.
  2. An order import burst: webhooks at 10x normal.
  3. Gang-sheet compose for 5 tenants at once.
  4. Dashboard and list reads.
- **MUST** load-test against staging seeded with **realistic multi-tenant data**: 1,000 companies, a skewed size distribution (a few huge shops, many small ones) and 12 months of orders. RLS plans and index choices only show their problems with many tenants.
- **SHOULD** run a breakpoint test (a ramping arrival rate until failure) before each stage transition, and record the capacity in `runbook.md`.

### 6.3 Caching rules
- **MUST** scope every cache key by tenant: `c:{companyId}:...`. A cache key without a tenant is a data-leak bug.
- **MUST** invalidate through `afterCommit` hooks (they already exist in `db/client.ts`), never before the commit.
- **SHOULD** cache only what is read-heavy and changes rarely: plans, role permissions (already in code), the station-token cache (exists), marketplace category trees, the trademark list. **Don't** cache order or production state; the floor must see the truth.
- **SHOULD** serve static web and floor assets from CloudFront with long `immutable` cache on hashed files and `no-cache` on `index.html` and the service worker (`sst.aws.StaticSite` already uses CloudFront).

### 6.4 File and image pipeline

**What exists**
- Uploads go direct to S3 with a presigned PUT that signs the `content-type` and exact `content-length` (`src/lib/s3.ts`), checked afterwards with `headObject`. Keys are prefixed by `companyId/`.
- Lifecycle rules exist for `sheets/` and `raw/`.
- Imaging reads and writes S3 itself.

**Rules**
- **SHOULD (next)** switch to presigned **POST** with a `content-length-range` policy when files are larger or clients are less trusted. The POST policy is enforced by S3 itself, whereas a PUT depends on the signed header being honored [S40].
- **MUST (now)** put a concurrency limit in imaging:
  - It runs one uvicorn process with sync endpoints on the default threadpool, so dozens of renders can run at once.
  - A 240" sheet needs about 1 GB of RAM (runbook), so 8+ concurrent composes will run the 8 GB task out of memory.
  - Add a semaphore sized to `memory_GB / 1.5` for `/compose` that returns `503 + Retry-After` when full, and treat that as a retryable error in the worker.
- **SHOULD (next)** autoscale imaging on the `render` queue's waiting count, run it on Fargate Spot with on-demand as the base (renders are retryable and idempotent by output key), and split heavy compose from light endpoints (QA, labels) into two services so a compose backlog never delays label PDFs.
- **SHOULD (later)** have imaging consume render jobs directly with the BullMQ Python client [06-tools-backend §3], removing the long HTTP hold in the Node worker.
- **SHOULD** serve downloads of large sheets through CloudFront signed URLs when egress grows [S41]. Keep S3 presigned GETs short (15 min) for PII documents such as labels.
- **MUST** make output keys deterministic (`sheets/{companyId}/{sheetId}/{version}.png`) so a retried render overwrites instead of duplicating.

---

## 7. AWS topology, DR and cost

### 7.1 Topology by stage

| Component | Now (pilot) | Next (100s) | Later (1,000s+) |
|---|---|---|---|
| Compute | ECS Fargate ARM: api ×2 (min), worker ×1, imaging ×1 | api 2–6 autoscaled on requests, worker split per queue class, imaging on Spot scaled on queue depth | Same per cell; Compute Savings Plan |
| Postgres | RDS PG 17 `t4g.medium`, single-AZ, 14-day PITR, deletion protection | `m7g.large` **Multi-AZ**, read replica for reports, PgBouncer | `r7g.xlarge+` Multi-AZ per cell; Aurora only if you need fast failover or many replicas (05 §2) |
| Valkey | 1 node `t4g.small`, **cluster mode off**, `noeviction` parameter group | Primary + replica, Multi-AZ auto-failover | Per cell |
| S3 | One bucket, SSE-KMS, lifecycle | + versioning on `designs/`; Intelligent-Tiering | + Cross-Region Replication for designs |
| Edge | CloudFront for web/floor; ALB with HTTPS | + WAF managed rules and a rate-based rule | + cell router |
| Network | NAT instance, S3 gateway endpoint | NAT gateway (HA) or NAT instance autoscaling | Per cell VPC or shared |

- **MUST (now)** fix these SST defaults, found in `.sst/platform/src/components/aws/*`:
  - `sst.aws.Redis` **defaults to cluster mode enabled** (`cluster: { nodes: 1 }`). BullMQ with a plain `ioredis` client (`src/lib/queues.ts`) needs cluster mode **off**, or a Cluster client with `{hash-tag}` queue prefixes [S29, S30]. Set `cluster: false` and `parameters: { "maxmemory-policy": "noeviction" }`. ElastiCache Serverless is not compatible with BullMQ [S30].
  - `sst.aws.Postgres` defaults to `t4g.micro`, `backupRetentionPeriod: 7` and single-AZ. Set the instance and use `transform` for `backupRetentionPeriod` (14 in staging, 35 in production), `deletionProtection: true`, and `multiAz` once in growth.
  - `api` scaling has min/max but no target. Add `cpuUtilization: 60` and `requestCount`.
- **MUST (now)** run ECS tasks with read-only root filesystems where possible, and keep secrets in `sst.Secret` or SSM only (already done).
- **Choice check:** ECS Fargate is still right for this stage. It has no cluster to operate, SST supports it natively, and imaging needs 8 GB tasks and long runs, which rules out Lambda. Revisit EKS only at cells + 10 engineers. This matches 05-tools-hosting.

### 7.2 Backups and DR targets

| | Now | Next | Later |
|---|---|---|---|
| RPO (data loss) | ≤ 5 min (RDS PITR uploads WAL about every 5 min) [S31] | ≤ 5 min; + cross-region automated backups [S32] | ≤ 1 min with a cross-region replica for top-tier cells |
| RTO (time to restore) | ≤ 4 h (restore PITR to a new instance, repoint via SST) | ≤ 1 h; Multi-AZ gives about 1–2 min for an AZ failure | ≤ 15 min for regional failover in the warm-standby cell |
| S3 | Versioning on designs/art; lifecycle | + CRR for `designs/` | Same |
| Valkey | Treat as rebuildable; outbox re-drive (§3.3) | Replica | Same |

- **MUST** run a restore drill every quarter: restore PITR to a new instance, run the app's smoke test against it, record the actual RTO in the runbook. An untested backup is not a backup [S31].
- **MUST** keep the PII purge (30-day buyer PII, already a job) consistent with backups. Document that backups expire PII within the retention window (35 days).

### 7.3 Cost per tenant

- **SHOULD (now)** write a nightly `tenant_usage_daily` row per company:
  - orders and items imported
  - jobs run per queue and total job seconds
  - render seconds (from imaging timings)
  - AI cents (already in `ai_jobs.costCents`)
  - S3 bytes, from S3 Inventory or Storage Lens grouped by `companyId/` prefix
  - label count
- Allocate the monthly AWS bill (from the Cost and Usage Report, CUR) across tenants proportionally per driver: DB by DB-time, compute by job seconds plus requests, S3 by bytes. This is the AWS SaaS Lens model [S33].
- **SHOULD (next)** turn on ECS split cost allocation data in the CUR for per-service Fargate cost [S34], tag everything with `stage`, `service` and later `cell`, and compare revenue per plan tier against cost per tenant every month. Adjust plan limits when the top 5% of tenants cost more than their plan earns.

---

## 8. LLM cost and latency controls

**What exists (good)**
- One gateway for every Claude call (`src/ai/gateway.ts`).
- Per-company credits with `assertCredits` before each call and a ledger with tokens, cache tokens and cost.
- The PII stripper.
- A versioned prompt registry with a stable cached system prefix (`cache_control`).
- Effort tuned per route (`src/ai/models.ts`).
- `maxTokens` per route.
- A mock provider.

**Rules**
- **MUST (now)** add a **global** daily spend circuit breaker: a Valkey counter of `costCents` per UTC day. Above the threshold, non-interactive AI routes return "queued for later" and the platform owner gets paged. Per-tenant credits don't protect against a bug that loops across all tenants.
- **MUST** cap concurrency per tenant on the `ai` queue (§3.4), and cap assistant turns and tool calls per conversation.
- **SHOULD (now)** send bulk, non-urgent work through the **Message Batches API**: overnight listing drafts for a catalog, re-running trademark checks after the marks list updates, bulk tags. It costs 50% less and results arrive within 24 h [S35]. Prompt caching discounts stack with batch pricing [S35, S36].
- **SHOULD** keep cacheable prefixes byte-stable. Put the system prompt, tool definitions and trademark rules first, and the variable content last. Watch the cache hit rate (`cacheReadTokens / tokensIn`) per route as a metric and alert if it drops below 50% on routes that should hit [S36].
- **SHOULD** cache results, not just prompts: hash `(prompt version, normalized input)` and store the result per tenant (e.g. `trademark_judge` for identical text), with a TTL. Don't call the model twice for the same design text.
- **SHOULD** use a cheaper or faster model tier for `low`-effort routes once there is eval data showing equal quality. Keep this a one-line change in `models.ts`, gated by an eval set in CI.
- **SHOULD (next)** stream long outputs to the UI (the assistant already streams), set a p95 latency SLO per route, and use timeouts plus one retry with jitter for 429/529 responses from the provider.

---

## 9. Role checklists

**Backend engineer**
- MUST: tenant work runs inside `withTenant`; new `withSystem` usage is justified in the PR description.
- MUST: every new handler is idempotent (DB unique key or state guard), has a run-twice test, and throws `UnrecoverableError` for permanent failures.
- MUST: every new index on a tenant table leads with `company_id`; every new policy is plain equality or has an EXPLAIN check at 1,000 tenants.
- MUST: bulk endpoints have quotas and pagination; external calls have timeouts.
- MUST: logs use the logger with context (no bare `console.*`) and never log PII.

**Database and migrations owner**
- MUST: expand/contract across separate deploys; `lock_timeout` 5 s; `CONCURRENTLY` indexes through the online runner; batched, restartable backfills.
- MUST: role-level timeouts; a connection budget table in the runbook; the outbox purge job.
- SHOULD: partition append-only tables at growth; review the top queries by `pg_stat_statements` every week.

**Infra / DevOps**
- MUST (P0): create the `invai_app` and `invai_system` roles in RDS and point the services at them; a migrate task before deploy; HTTPS; Valkey `cluster: false` + `noeviction`; RDS instance size, retention and deletion protection.
- MUST: circuit breaker + alarm rollback; `/livez` for the ALB; worker `stopTimeout` ≥ 60 s; quarterly restore drill.
- SHOULD: ADOT collector; the CUR with split cost allocation; the WAF rate rule; autoscaling on queue depth.

**Imaging engineer**
- MUST: a compose concurrency semaphore with 503 backpressure; deterministic output keys; OTel FastAPI instrumentation that keeps the incoming `traceparent`.
- SHOULD: separate compose and light services; Spot; report render seconds per job for cost attribution.

**Frontend (web, floor)**
- MUST: handle `429`/`503` with `Retry-After` gracefully (the floor must show "retrying", not an error); send the `traceparent` header from fetch (OTel web instrumentation or a manual header); tolerate an API one version ahead.
- SHOULD: stay within the JS budgets; hashed immutable assets; direct-to-S3 uploads only.

**AI engineer**
- MUST: every call through the gateway; per-route `maxTokens`; the global spend breaker; evals before a model change.
- SHOULD: the Batch API for bulk; a result cache; watch the cache hit rate.

**QA**
- MUST: k6 arrival-rate suites with SLO thresholds before each stage transition; a multi-tenant staging seed (1,000 companies, skewed sizes).
- SHOULD: a chaos drill per quarter: kill Valkey, a DB failover, imaging down. Check that jobs recover and the outbox re-drive works.

**Tech lead**
- MUST: review the stage triggers (§1) every month; the SLO review and error budget policy; a postmortem for every SEV1/2.
- SHOULD: a cost-per-tenant review every month; the flag cleanup list.

---

## 10. Current code vs. gaps (verified 2026-09-24)

| # | Area | Status | Evidence | Stage |
|---|---|---|---|---|
| G1 | **RLS is bypassed in AWS**: `DATABASE_URL` = RDS master user | Gap, **P0** | `invai-infra/sst.config.ts` (the `databaseUrl` comment admits it) | Now |
| G2 | Valkey via SST defaults to cluster mode on and no `noeviction` | Gap, **P0** | `.sst/platform/src/components/aws/redis.ts` (`@default { nodes: 1 }`), `sst.config.ts` passes neither | Now |
| G3 | Deploy never runs migrations; the drizzle migrator uses a single transaction | Gap, P0 | `.github/workflows/deploy.yml`, `drizzle-orm/pg-core/dialect.js` | Now |
| G4 | ALB listener is HTTP only | Gap, P0 | `sst.config.ts` `listen: "80/http"` | Now |
| G5 | RDS: `t4g.micro` default, 7-day backups, single-AZ; RDS Proxy will pin with `set_config` | Gap | `postgres.ts` defaults; [S3] | Now |
| G6 | No DB timeouts (`statement_timeout`, idle-in-transaction, lock) | Gap | grep: none in `init.sql` or migrations | Now |
| G7 | `/health` (checks DB + Redis) is the ALB health check, so failures cascade | Gap | `src/api/app.ts`, `sst.config.ts` | Now |
| G8 | No graceful SIGTERM in the API | Gap | `src/api/server.ts` | Now |
| G9 | Retry backoff without jitter; no `UnrecoverableError`; no DLQ alert or redrive | Gap | `src/lib/queues.ts`, `src/worker/index.ts` | Now |
| G10 | Outbox rows never purged; parked events never alerted | Gap | `src/worker/outbox-relay.ts`, no purge job | Now |
| G11 | `jobId` deduplication window shortened by `removeOnComplete.count: 5000` | Risk | `src/lib/queues.ts` | Now (make handlers idempotent) |
| G12 | No per-tenant fairness in queues; poll fan-out is a synchronized burst | Gap | `QUEUE_CONCURRENCY`, `modules/channels/jobs.ts` | Now (cap) / Next (groups) |
| G13 | No per-tenant API rate limit; Better Auth limits probably per-process memory | Gap | `src/lib/ratelimit.ts`, `src/auth.ts` (verify storage) | Now |
| G14 | No OTel, no access log, `requestId`/`companyId` not in logs, worker failure log lacks the tenant | Gap | `package.json`, `src/lib/log.ts`, `src/worker/index.ts` | Now |
| G15 | Imaging has no concurrency limit (1 uvicorn process, sync threadpool, ~1 GB per big sheet on an 8 GB task) | Gap | `invai-imaging/Dockerfile`, `app/main.py` | Now |
| G16 | One Valkey connection per SSE subscriber hits ElastiCache connection limits at scale | Risk | `src/lib/realtime.ts` `subscribe()` | Next |
| G17 | Trigram GIN indexes not tenant-leading | Risk | `drizzle/0001_grants_extensions.sql` | Next |
| G18 | No global AI spend breaker; no Batch API use | Gap | `src/ai/*` | Now / Next |
| G19 | No per-tenant usage table or cost allocation | Gap | none | Now (table) / Next (CUR) |
| G20 | Worker and imaging have no autoscaling; one worker service runs every queue + the relay | Gap | `sst.config.ts` | Next |
| OK | RLS on every tenant table + coverage test; transaction-local `set_config`; outbox in the same tx; `SKIP LOCKED` relay; `jobId` idempotency; webhook dedupe on ID; presigned PUT with signed length; tenant-prefixed S3 keys; per-company AI credits; prompt caching; mocks for every provider; lifecycle rules; KMS; `removal: retain` in prod | Done | Files cited above | n/a |

**Suggested order:** G1 → G2 → G3/G4 → G6/G7/G8 → G9/G10/G11 → G14 → G12/G13/G15 → G5/G18/G19 → the growth items.

---

## 11. Sources

- [S1] Bytebase, "Postgres Row-Level Security Footguns": https://www.bytebase.com/blog/postgres-row-level-security-footguns/
- [S2] pganalyze, "RLS, security invoker views and why LEAKPROOF functions matter": https://pganalyze.com/blog/5mins-postgres-row-level-security-bypassrls-security-invoker-views-leakproof-functions ; AWS, "Multi-tenant data isolation with PostgreSQL RLS": https://aws.amazon.com/blogs/database/multi-tenant-data-isolation-with-postgresql-row-level-security/
- [S3] AWS docs, "Avoiding pinning an RDS Proxy" (PostgreSQL: SET/set_config pin; stored function calls not inspected): https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-proxy-pinning.html
- [S4] AWS re:Post, "Resolve connection pinning issues in RDS Proxy": https://repost.aws/knowledge-center/rds-proxy-connection-pinning-issues ; R. Yen, "Debugging RDS Proxy pinning" (2026): https://richyen.com/postgres/2026/03/12/rds_proxy_pinning.html
- [S5] PgBouncer FAQ and config: https://www.pgbouncer.org/faq.html , https://www.pgbouncer.org/config.html
- [S6] pganalyze, "PgBouncer 1.21 adds prepared statement support in transaction mode": https://pganalyze.com/blog/5mins-postgres-pgbouncer-prepared-statements-transaction-mode
- [S7] PostgreSQL 17 docs, client connection defaults (statement_timeout, lock_timeout, idle_in_transaction_session_timeout): https://www.postgresql.org/docs/17/runtime-config-client.html
- [S8] Stripe, "Scaling your API with rate limiters": https://stripe.com/blog/rate-limiters
- [S9] Amazon Builders' Library, "Fairness in multi-tenant systems": https://builder.aws.com/content/3Eupj3d2bo4fEvlzYbICMZNhQ3B/fairness-in-multi-tenant-systems ; "Avoiding insurmountable queue backlogs": https://builder.aws.com/content/3EuRcgkTP1MI0c7zM8W6HL3WIqA/avoiding-insurmountable-queue-backlogs
- [S10] BullMQ docs, "Retrying failing jobs" (jitter, custom backoff) and "Going to production": https://docs.bullmq.io/guide/retrying-failing-jobs , https://docs.bullmq.io/guide/going-to-production
- [S11] Amazon Builders' Library, "Timeouts, retries, and backoff with jitter": https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/
- [S12] AWS Prescriptive Guidance, "Transactional outbox pattern": https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html
- [S13] "Transactional outbox with at-least-once delivery: designing for duplicate events" (2026): https://oneuptime.com/blog/post/2026-07-22-transactional-outbox-duplicate-events/view ; Stripe, "Designing robust and predictable APIs with idempotency": https://stripe.com/blog/idempotency
- [S14] BullMQ Pro Groups: https://docs.bullmq.io/bullmq-pro/groups/ ; group rate limiting: https://docs.bullmq.io/bullmq-pro/groups/rate-limiting
- [S15] Taskforce.sh, "Rate-limit recipes in NodeJS using BullMQ": https://blog.taskforce.sh/rate-limit-recipes-in-nodejs-using-bullmq/
- [S16] GoCardless, "Zero-downtime Postgres migrations": https://gocardless.com/blog/zero-downtime-postgres-migrations-a-little-help/
- [S17] PostgresAI, "Zero-downtime Postgres schema migrations need this: lock_timeout and retries": https://postgres.ai/blog/20210923-zero-downtime-postgres-schema-migrations-lock-timeout-and-retries
- [S18] AWS, "Amazon ECS enables built-in blue/green deployments" (2025-07): https://aws.amazon.com/about-aws/whats-new/2025/07/amazon-ecs-built-in-blue-green-deployments/
- [S19] AWS docs, "Creating an Amazon ECS blue/green deployment": https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deploy-blue-green-service.html
- [S20] AWS Containers blog, "Automate rollbacks for ECS rolling deployments with CloudWatch alarms": https://www.amazonaws.cn/en/blog-selection/automate-rollbacks-for-amazon-ecs-rolling-deployments-with-cloudwatch-alarms/
- [S21] AWS, "Amazon ECS introduces 1-click rollbacks" (2025-05): https://aws.amazon.com/about-aws/whats-new/2025/05/amazon-ecs-1-click-rollbacks-service-deployments
- [S22] OTel BullMQ instrumentation: https://github.com/appsignal/opentelemetry-instrumentation-bullmq ; https://www.npmjs.com/package/@jenniferplusplus/opentelemetry-instrumentation-bullmq
- [S23] OpenTelemetry messaging semantic conventions: https://opentelemetry.io/docs/specs/semconv/messaging/ ; FastAPI instrumentation: https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html
- [S24] Grafana, "The RED method": https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/ ; B. Gregg, "The USE method": https://www.brendangregg.com/usemethod.html
- [S25] Google SRE Workbook, "Alerting on SLOs" and "Implementing SLOs": https://sre.google/workbook/alerting-on-slos/ , https://sre.google/workbook/implementing-slos/
- [S26] OpenFeature (CNCF): https://openfeature.dev/
- [S27] Grafana k6 docs, scenarios, arrival-rate executors and API load testing: https://grafana.com/docs/k6/latest/using-k6/scenarios/ , https://grafana.com/docs/k6/latest/testing-guides/api-load-testing/
- [S28] Google SRE Book, "Postmortem culture": https://sre.google/sre-book/postmortem-culture/
- [S29] BullMQ, "AWS ElastiCache" (node-based, custom parameter group, `noeviction`; Serverless incompatible): https://docs.bullmq.io/guide/redis-tm-hosting/aws-elasticache
- [S30] Valkey docs, key eviction: https://valkey.io/topics/lru-cache/
- [S31] AWS docs, RDS backup retention and PITR: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.BackupRetention.html
- [S32] AWS, RDS cross-Region automated backups (2026-07 expansion): https://aws.amazon.com/about-aws/whats-new/2026/07/amazon-rds-cross-region-automated-backups-additional-aws-regions/
- [S33] AWS Well-Architected SaaS Lens: https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/saas-lens.html
- [S34] AWS docs, "Understanding split cost allocation data": https://docs.aws.amazon.com/cur/latest/userguide/split-cost-allocation-data.html
- [S35] Anthropic docs, batch processing (50% discount, ≤24 h): https://docs.claude.com/en/docs/build-with-claude/batch-processing
- [S36] Anthropic docs, prompt caching (cache reads ~0.1x input price; stacks with batch): https://docs.claude.com/en/docs/build-with-claude/prompt-caching
- [S37] AWS whitepaper, "SaaS Tenant Isolation Strategies" (pool isolation, noisy neighbor): https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/pool-isolation.html
- [S38] AWS re:Invent 2024 SAS315, "SaaS meets cell-based architecture": https://d1.awsstatic.com/onedam/marketing-channels/website/aws/en_US/events/approved/reinvent-2025/reinvent/2024/slides/sas/SAS315_SaaS-meets-cell-based-architecture-A-natural-multi-tenant-fit.pdf ; AWS Architecture Blog, hybrid multi-tenant stateful services: https://aws.amazon.com/blogs/architecture/building-hybrid-multi-tenant-architecture-for-stateful-services-on-aws/
- [S39] Citus 12, schema-based sharding: https://www.citusdata.com/blog/2023/07/18/citus-12-schema-based-sharding-for-postgres/ ; Crunchy Data, "Designing your Postgres database for multi-tenancy": https://www.crunchydata.com/blog/designing-your-postgres-database-for-multi-tenancy
- [S40] fourTheorem, "The illustrated guide to S3 pre-signed URLs": https://fourtheorem.com/the-illustrated-guide-to-s3-pre-signed-urls/ ; Advanced Web Machinery, "PUT vs POST S3 signed URLs": https://advancedweb.hu/differences-between-put-and-post-s3-signed-urls/
- [S41] AWS docs, CloudFront signed URLs: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-signed-urls.html
- Internal: `invai-docs/research/05-tools-hosting.md` (prices, phased hosting), `06-tools-backend.md` (queue choice, RLS pattern), `build/runbook.md`, `build/architecture-as-built.md`.
