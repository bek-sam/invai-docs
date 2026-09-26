# Wave 12: reliable at scale (local; AWS parts deferred with waves 10 and 11)

- Goal:
  - Jobs retry sensibly, and failures are parked, alerted and redrivable.
  - One busy shop can't starve others.
  - Health checks tell the truth, and shutdown is graceful.
  - Tenant data can be exported and deleted.
  - Web and floor send strict security headers.
  - Imports can't race.
- Rules: `team/agent-brief.md`. **Every prompt says "Don't push".**
- Follow-ups folded in from earlier waves (see each `waves/*/wave.md`, "Follow-ups"): stuck intents and job rows, outbox job-id override, final-failure sweep, Valkey fail-open alert, `floor_requests` retention, the advisory lock around migrate and reference data.

## Cards
| Card | Owner | Co-reviewers | Flags | Model |
|---|---|---|---|---|
| T-12-1 Retries, DLQ, redrive, stuck sweeps (B-17 + follow-ups) | backend-foundation | reviewer, qa-engineer | floor-correctness | opus |
| T-12-2 Health, timeouts, graceful shutdown, migrate lock (B-16 + follow-up) | backend-foundation | platform-sre | — | sonnet |
| T-12-3 Rate limits and queue fairness (B-20), rate limiter in Valkey | backend-foundation | security-reviewer | auth | sonnet |
| T-12-4 Tenant export, deletion and retention (B-23, without KMS) | backend-foundation + compliance-officer | security-reviewer | pii, tenancy | opus |
| T-12-5 CSP and security headers; SVG not served inline (B-24) | web-engineer + floor-engineer | security-reviewer | files | sonnet |
| (P2, if a slot frees) Import races, `ON CONFLICT`, per-connection lock (B-99 rest) | backend-engineer (orders) | — | — | sonnet |

## Ownership split (PM+architect review, r1)

All four backend-foundation cards touch `lib`, `worker` and `api`. **T-12-1 lands first** (it fixes the retry/backoff/jobId semantics in `lib/queues.ts` and `worker/outbox-relay.ts` that T-12-3's fairness code sits on top of, and `T-12-4`/`T-12-2` don't depend on it at all). **T-12-2, T-12-3 and T-12-4 then run in parallel** — their primary files are disjoint; two small shared files are called out below as coordination points, not blockers.

| Card | Primary files (owns) | Shared/coordination files | Sequencing |
|---|---|---|---|
| **T-12-1** | `src/lib/queues.ts` (per-job-type backoff+jitter, `UnrecoverableError` helper); `src/worker/outbox-relay.ts` (jobId fix, 7-day purge, parked-event alert); new `src/worker/sweeps.ts` (generic `jobs`-table sweep, `ai_jobs` sweep); new `src/api/internal.ts` (DLQ redrive route) | `src/api/app.ts` (mounts `/internal/*`, one line); `src/modules/channels/jobs.ts` (adds a stuck-`received` check next to the existing `channels.webhookDeliveries.purge` job); `src/env.ts` (`INTERNAL_ADMIN_TOKEN`) | **Runs first.** Land before T-12-3 touches `channels/jobs.ts`. |
| **T-12-2** | `src/api/server.ts` (SIGTERM drain); `src/db/migrate.ts` (advisory lock); new migration for role-level `statement_timeout`/`idle_in_transaction_session_timeout`/`lock_timeout` | `src/api/app.ts` (adds `/livez`, `/readyz` next to existing `/health` — additive); `src/worker/index.ts` — owns only the `shutdown()` function (bottom of file) | Parallel, after T-12-1. |
| **T-12-3** | `src/lib/ratelimit.ts` (Valkey token bucket); new `src/lib/fairness.ts` (per-tenant semaphore + bulk/interactive priority); `src/auth.ts` (Better Auth → Valkey storage) | `src/api/orpc.ts` or `src/api/context.ts` (rate-limit middleware); `src/worker/index.ts` — owns only the `Worker` processor callback (top of file, distinct region from T-12-2's `shutdown()`); `src/modules/channels/jobs.ts` (poll jitter on `pollChannelsJob`, lands after T-12-1's edit to the same file) | Parallel, after T-12-1. |
| **T-12-4** | `src/modules/privacy/service.ts`, new `src/modules/privacy/jobs.ts`, new `src/modules/privacy/router.ts`; `invai-contracts/src/contract/privacy.ts` (new) | `src/lib/s3.ts` (adds a bulk-delete-by-prefix helper, additive); `src/db/schema/tenancy.ts` (adds `"tenant_export"` to `JOB_KINDS`, additive); `src/api/router.ts` (registers the new router, one line) | Parallel, after T-12-1. Most isolated card — could start immediately if a 4th slot opens. |

Rationale: "ai_jobs" and "production.jobs" in T-12-1's acceptance criteria both resolve to sweeps over existing shared tables (`ai_jobs` and the generic `jobs` table in `db/schema/tenancy.ts`, which already covers `build_sheets`/`regenerate_sheet`/`render_artwork`/`batch_labels`/etc.) — one cross-tenant sweep each in `worker/sweeps.ts`, not per-module changes. This keeps T-12-1 inside `lib`/`worker`/`api` as scoped, instead of spilling into `modules/ai` and `modules/production` (owned by other tracks). The shipping buy/void/push-intent sweep already exists (`shipping/jobs.ts` `stuckIntentSweepJob`, built in wave 2/3) — T-12-1 only needs to confirm coverage, not rebuild it.

## Contract stubs (exact designs)

**A. DLQ / redrive — not an oRPC tenant procedure.** `invai-contracts`' `AuthMode` (`user | floor | station | public`) and `roles.ts` are all company-scoped; there is no cross-tenant "platform admin" role or session, and BullMQ's failed sets and parked outbox rows span every company. Inventing a fake tenant permission for this would be wrong. Instead, T-12-1 adds plain (non-contract) Hono routes, internal-only:

- New `src/api/internal.ts`, mounted in `app.ts` next to `/health`. Every route checks header `X-Internal-Token` against `env.INTERNAL_ADMIN_TOKEN` (new required env var; never shipped to a browser) and 404s if absent — same shape as the runbook's existing "re-drive outbox from time T" script, just callable over HTTP instead of a one-off script.
  - `GET /internal/dlq/failed?queue=<name>` → `{ jobs: [{ id, name, companyId, attemptsMade, failedReason, timestamp }] }` (BullMQ `Queue.getFailed()`) plus parked outbox rows (`outboxBacklog()`-style: `count(*) where last_error is not null and attempts >= MAX_ATTEMPTS`).
  - `POST /internal/dlq/redrive` `{ queue: QueueName, jobIds: string[] }` → calls `job.retry()` per id, returns `{ retried: string[], notFound: string[] }`.
  - `POST /internal/dlq/redrive-outbox` `{ olderThanMinutes?: number }` → resets `dispatched_at` to null for parked outbox rows, returns `{ reset: number }`. Safe only because handlers are idempotent (research §3.1) — say so in the route's comment.
- New alert kinds in `invai-contracts/src/schemas/alerts.ts` `ALERT_KINDS`: `"queue_failed_spike"` (a queue's failed-count growth over 15 min exceeds N) and `"outbox_parked"` (any row with `attempts >= MAX_ATTEMPTS`). Both `severity: "critical"`, `entity: null` (queue-level, not order-level). Raised by a `reports` sweep, read like any other alert — no new paging/CloudWatch integration (deferred, see Scope below).
- Fold in the wave-8 T-8-2 follow-up here: the AI spend breaker's Valkey fail-open currently logs and does not alert; add a matching alert kind `"ai_breaker_fail_open"` and raise it from the same code path.

**B. Export / delete — an oRPC tenant procedure**, new `invai-contracts/src/contract/privacy.ts` (mirrors `contract/tenancy.ts`'s `me` router). Two new permissions in `roles.ts`, `"org.export"` and `"org.delete"`, granted to `owner` only — carved out of `admin`'s `SHOP_ALL` exactly the way `billing.manage` already is, matching the card's literal "owner-triggered" wording.

```ts
export const privacy = base.prefix("/privacy").tag("privacy").router({
  exportTrigger: proc("org.export")
    .route({ method: "POST", path: "/export" })
    .input(z.object({}))
    .output(Job) // existing tenancy `Job`; kind "tenant_export"
    .errors({
      EXPORT_IN_PROGRESS: {
        status: 409, message: "An export is already running",
        data: z.object({ jobId: Id, startedAt: Timestamp }),
      },
    }),
  exportStatus: proc("org.export")
    .route({ method: "GET", path: "/export/{jobId}" })
    .input(z.object({ jobId: Id }))
    .output(Job),
  deleteRequest: proc("org.delete")
    .route({ method: "POST", path: "/delete-request" })
    .input(z.object({ confirm: z.literal(true) }))
    .output(z.object({ scheduledPurgeAt: Timestamp }))
    .errors({
      DELETION_ALREADY_REQUESTED: {
        status: 409, message: "Deletion is already scheduled",
        data: z.object({ scheduledPurgeAt: Timestamp }),
      },
    }),
  deleteCancel: proc("org.delete")
    .route({ method: "POST", path: "/delete-cancel" })
    .input(z.object({}))
    .output(Ok)
    .errors({ NO_DELETION_PENDING: { status: 404, message: "No deletion is pending" } }),
  deleteStatus: proc("org.export")
    .route({ method: "GET", path: "/delete-status" })
    .input(z.object({}))
    .output(z.object({
      status: z.enum(["active", "soft_deleted"]),
      scheduledPurgeAt: Timestamp.nullable(),
    })),
});
```

- Export reuses the existing `jobs` + `files` + `files.downloadUrl` pattern exactly — no new download endpoint. Add `"tenant_export"` to `JOB_KINDS` (`db/schema/tenancy.ts`). The job zips one JSON+CSV pair per tenant table plus the company's uploaded files, uploads the zip via `lib/s3.ts`, creates one `files` row, and puts that file id in `jobs.resultIds`; the owner fetches it with the existing `files.downloadUrl` procedure, unchanged.
- Delete: `deleteRequest` sets `companies.deletedAt` (soft-delete) and schedules `tenantHardPurge` (jobId `hard-purge:{companyId}`, idempotent, `reports` queue, delayed 30 days) which purges rows and S3 objects. `deleteCancel` clears `deletedAt` and cancels the delayed job as long as the purge hasn't run yet.
- New audit actions (`AUDIT_ACTIONS` in `schemas/tenancy.ts`): `"tenant.export_requested"`, `"tenant.delete_requested"`, `"tenant.delete_cancelled"`, `"tenant.purged"`.
- Cross-tenant safety test (required): a second company's `privacy.exportTrigger`/`deleteRequest` call, and the sweep jobs themselves, must never read or touch another `company_id`'s rows — assert with the RLS test harness (`db/rls-coverage.test.ts` pattern), not just a unit mock.

## Fairness: BullMQ "groups" is not available

Checked `invai-backend/package.json` and `pnpm-lock.yaml`: only open-source `bullmq@6.3.8` is installed. "Groups" (round-robin per-`groupId`, its own per-group rate limit) is a `bullmq-pro` (`@taskforcesh/bullmq-pro`) feature — a separately licensed package, not present anywhere in the lockfile. **Decision: do not add BullMQ Pro this wave** (a new paid dependency is an owner-track decision, not a P0 fix).

T-12-3 uses the research doc's free "cheap version" instead:
- A Valkey semaphore keyed `sem:{queue}:{companyId}` capping concurrent jobs per tenant per queue (e.g. at most 2 `render` jobs); a job that can't take the semaphore re-delays itself with `job.moveToDelayed` + `DelayedError` rather than failing.
- Lower BullMQ `priority` for bulk job kinds (`csv_import`, batch AI, `reports`) so interactive jobs (label purchase, single render) go first.
- Sharding each hot queue into K sub-queues by `hash(companyId) % K` stays a documented "SHOULD (next)" — only build it if load-test evidence (the card's own acceptance criterion) shows the semaphore isn't enough at higher tenant counts.

## Scope: AWS-deferred items to flag, not build

- **T-12-1**: "page on any non-zero value" (research §3.2) → implement as the existing in-app `alerts`/`ALERT_KINDS` mechanism only (see stub A above). No PagerDuty/CloudWatch alarm wiring — that's wave 10/11.
- **T-12-2**: ECS deployment circuit breaker, CloudWatch deployment alarms, ALB target-group health-check path, and the real ECS `stopTimeout` value are all deploy-time AWS config — deferred. T-12-2 only builds the process-level `/livez`/`/readyz` split, the SIGTERM drain, and the migrate advisory lock that those future ECS settings will point at.
- **T-12-3**: per-tenant DB-time dashboard and a `tier` column on `companies` (research §2.3/2.5, both "SHOULD next") are out of scope this wave; only the MUST-now Valkey token bucket + semaphore land.
- **T-12-4**: already correctly scopes out AWS KMS. The export/delete object-storage work runs entirely against the existing MinIO-backed `lib/s3.ts` abstraction — no new AWS dependency now, and the same code will run unchanged once S3 replaces MinIO in wave 10.
- **T-12-5**: no AWS dependency — headers are set by the app itself, not a CDN/ALB policy. Confirm this stays true (no assumption of a CloudFront header policy) during review.
- **Grants (tech lead, 2026-09-26):** T-12-1 `worker/index.ts` edit `319027a` approved; T-12-1 may add the new alert kinds to the web `alertKindLabel` (en/es) and `biome format` contracts `vendors.ts`. Migration 0024 also carries T-9-2's missing `vendor_connections.spec` default change.
- T-12-2: grant approved after the fact for the SSE retry-hint edit in `api/events.ts`. Cleanup still owed: `invai_test_t122` and Valkey db 13. The builder's drop was blocked by the permission guard, so the gate cleanup asks the owner.
- T-12-2 review: the migrate advisory-lock wait uses the `invai` role, capped at `statement_timeout` 5 min by 0025. Add `SET LOCAL statement_timeout = 0` plus a `lock_timeout` in `migrate.ts` (backend-foundation follow-up).
- **Grant approved after the fact (tech lead, 2026-09-26):** T-12-3 `1d077e2` sets bulk priority in `lib/queues.ts` for reports and `modules/ai/jobs.ts`.
- **Grant (tech lead, 2026-09-26):** T-12-5 may add a security-headers middleware hunk in backend `api/app.ts`, and change backend SVG file serving to attachment.
- **Grants (tech lead, 2026-09-26):**
  - T-12-4 may add the `KIND_PERMISSIONS` `tenant-export` line in `files/service.ts` (hunk-only).
  - T-12-4's edits to `contract.test.ts` (path param), `roles.test.ts` (one assertion) and `modules/jobs.ts` (one import) are approved after the fact.
- T-12-4 follow-ups:
  - A soft-deleted company must block sign-in during the 30 days (security, P1).
  - Deleting a company must cancel its Stripe subscription (billing).
  - The export zip is capped at 4 GB.
- Grant approved after the fact: T-12-5 r2 edits to the web and floor Dockerfiles, plus the `nginx.conf` templating (`scripts/render-nginx-conf.ts`).
