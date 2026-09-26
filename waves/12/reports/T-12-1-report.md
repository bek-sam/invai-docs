# T-12-1 report: retries, DLQ, redrive and stuck sweeps

Status: **done, not pushed.** Commits:

| Repo | SHA | What |
|---|---|---|
| invai-contracts | `1dcf156` | `ALERT_KINDS` + `queue_failed_spike`, `outbox_parked`, `ai_breaker_fail_open` |
| invai-backend | `2f18b39` | `outbox_events_dispatched_idx` (partial, `dispatched_at is not null`) + migration `0024_outbox_dispatched_idx` |
| invai-backend | `5ffbee6` | main change (queues, relay, sweeps, internal routes, channels, breaker, tests) |
| invai-backend | `319027a` | `worker/index.ts`: processor = `processJob`, `import "./sweeps"` (kept separate, see "Out-of-owned-path edits") |

## Acceptance criteria and their tests

1. **Jitter per job type.** `DEFAULT_BACKOFF = { type: "exponential", delay: 2000, jitter: 0.5 }`. `defineJob().enqueue` runs every backoff through `withJitter()`, so a job with its own backoff (`channels.sync`: exponential 10 s) keeps its type and delay and gains jitter 0.5. Test `lib/queues.test.ts`: 20 enqueues of one job type fail in a real Worker, and each first-retry `job.delay` falls in [1000, 2000] ms with more than one distinct value.
2. **`UnrecoverableError`.** `permanentFailure(reason)` and `isPermanentHttpStatus(status)` (4xx except 408/409/425/429) live in `lib/queues.ts`. `parseJobInput()` turns a Zod failure into `UnrecoverableError`, and `processJob()` (now the worker's processor) uses it. Tests: Zod-invalid data with `attempts: 5` ends `failed` with `attemptsMade === 1`; a provider-mock 422 fails after 1 attempt; a 503 is retried (`delayed`).
3. **DLQ, alert and redrive.** New `src/api/internal.ts` is mounted at `/internal` in `app.ts`, following stub A. `GET /dlq/failed?queue=` returns failed jobs plus `parkedOutbox { count, rows }`. `POST /dlq/redrive` calls `job.retry("failed", { resetAttemptsMade: true })` and returns `{ retried, notFound }`. `POST /dlq/redrive-outbox` returns `{ reset }`.
   - The token is compared in constant time (sha256 + `timingSafeEqual`). A missing header, wrong token or unset env var returns `404 {"error":"not found"}`, identical to an unknown path.
   - The `queue_failed_spike` check is in `worker/sweeps.ts` `checkFailedSpikes`. It runs `ZCOUNT` on the failed set over the last 15 min against N=25. A Valkey flag (`dlq:spike:<queue>`, 15 min TTL, refreshed while the spike lasts) keeps it to one alert per spike.
   - Tests `api/internal.test.ts` and `worker/sweeps.test.ts` cover: 404 on every route for 4 token variants and an unset token; a real failed job is listed, redriven and reaches `completed`; an unknown id lands in `notFound`; below the threshold no alert fires; a spike across 3 ticks and more failures gives exactly 1 alert; a new spike gives a 2nd.
4. **Outbox purge and parked alert.** `purgeDispatchedOutbox` deletes dispatched rows older than 7 days in `limit`-ed batches (5000 per statement). Parked rows (`attempts >= MAX_ATTEMPTS`) and pending rows are kept. It runs as the daily `platform.outboxPurge` job (reports, 04:35 UTC). `alertParkedOutbox` left-joins `alerts` on dedupe key `outbox_parked:<eventId>` and alerts only rows that don't have that alert yet, so a resolved alert is not reopened. Tests: batch size 2 purges 4 old rows and keeps the recent, pending and parked ones; two sweeps give exactly one alert; after the alert is resolved, a third sweep leaves it resolved.
5. **Stuck sweeps.** `sweepStuckJobRows` handles all `JOB_KINDS`. It fails rows that sit `queued` or `running` with `updatedAt` older than 30 min, but only when no live BullMQ job carries their id in `data.jobId`, `importRunId` or `jobRowId`. Live means active, waiting, waiting-children, delayed or prioritized. If any queue has more than 10k live jobs the sweep skips the tick rather than guess. It then publishes the same `job.progress` event as `job-failures.ts`. `sweepStuckAiJobs` fails `ai_jobs` rows still queued or running after 30 min; they have no BullMQ job and no realtime event. Both run in `platform.reliabilitySweep` (reports, every 5 min), where each step is isolated. Tests: an old running row with no Redis job flips to `failed`, with a `publish` spy asserting `job.progress`; a recent row and a row backed by a delayed job are left alone, then failed once that job is removed; a stale `ai_jobs` row is failed and a fresh one is not.
6. **Buy/void/push intents.** Confirmed: `findStuckIntents` selects `buying`, `voiding` and `pushing` rows, and `stuckIntentSweepJob` retries all three. Only buy had an "alerted" test, so I added void (carrier lookup failing) and push (Shopify failing, push job enqueue stubbed) tests to `shipping/jobs.test.ts`. Each asserts `["failed","failed","alerted"]` and its `stuck-intent-<kind>-<id>` alert.
7. **Webhook deliveries.** `channels/jobs.ts` gains `flagStuckWebhookDeliveries` and a sibling job, `channels.webhookDeliveries.stuck`, every 15 min. It flags rows at `received` older than 60 min whose `webhook-<channel>-<deliveryId>` job isn't live. The flag is `detail = "stuck at received: …"`: status stays `received`, and a late job still finishes the row normally. The daily purge job now flags before it deletes. Tests: one alert across two sweeps; a fresh row is untouched; a row with no company is still flagged; the purge flags an 8-day-old stuck row (1 alert) before deleting it.
8. **Outbox jobId fix.** `relayJobId()` prefers the subscriber's own `def.jobId(input)`. If a job under that id has already **finished** (completed or failed, and still retained in Redis), it falls back to `${eventId}:${jobName}`. Tests:
   - A scrap-hash-style job subscribed to two events with the same payload gives one BullMQ job at `queues.sync.getJob(expectedId)` and none under the event ids.
   - After that job completes, a later event still enqueues, under its event id.
   - A job without its own id is still deduped on a re-relay.
9. **AI breaker fail-open alert.** In `ai/breaker.ts`, a Valkey error or timeout now also raises `ai_breaker_fail_open` (critical) on the calling company. It is deduped per company per UTC hour in Postgres, since Valkey is the thing that's down, plus a 10-min in-process throttle so an outage doesn't write on every call. Test `ai/breaker.test.ts`: with `redis.mget` rejecting, 3 calls give 1 alert row; with Valkey up, none.

## Decisions (and why)
- **jobId: the card's rule plus a guard.** Applying "prefer `def.jobId`" as written would silently drop real work. Completed jobs stay in Redis for 24 h, and BullMQ ignores an `add` with an existing id. So a second `design.updated` (id `design-qa-<designId>`) or `cost_settings.changed` (id `profit-range:<company>::`) within 24 h would never run. With the fallback, duplicates collapse only while a job is still pending. Trade-off: if the relay crashes after enqueueing under the own id, and that job finishes before the re-relay, the handler runs twice. Handlers are DB-idempotent (idempotent-job), so this is acceptable.
- **Where alerts go.** `alerts` is a tenant table with no platform company. `queue_failed_spike` goes to each company that owns a failed job in the window; jobs with no `companyId` only produce an error log. `outbox_parked` goes to the event's company.
- **Stuck webhook alert.** `webhook_deliveries.company_id` stays null until the delivery is processed (`finishWebhookDelivery`), so a truly stuck row usually has no shop to alert. It is flagged on the row and logged at error level (the operator signal). A tenant alert (`sync_broken`, warning; no new kind in stub A) is raised only when the company is known. The test covers both cases.
- **`INTERNAL_ADMIN_TOKEN`** is optional (min 32 chars) instead of "required". Making it required would break every existing `.env`. Refusing to boot in production would break `env.test.ts` (not mine), which boots production with only provider keys. Unset means every `/internal` call returns 404, so it fails closed. Added to `.env.example`.
- **`redrive-outbox`** also resets `attempts` to 0. Otherwise a redriven row re-parks after one more failure. `olderThanMinutes` limits the reset to rows created at least that long ago.
- **Migration 0024** includes drizzle's pending `vendor_connections.spec` default change (adds `labelGapIn`). T-9-2 changed the schema and never generated a migration for it, and dropping it would desync the snapshot. It is harmless (column default only).

## Out-of-owned-path edits (need the tech lead's OK)
- `src/worker/index.ts` (commit `319027a`, its own commit so it can be dropped): the processor callback becomes `processJob` (same dispatch, plus the permanent-failure parse), and `import "./sweeps"` is added. Without it, AC2 and the sweeps never run in the real worker. T-12-3 owns this callback next; it can wrap `processJob`.
- `src/modules/shipping/jobs.test.ts`: two added tests only (AC6 asks for them).
- `src/ai/breaker.ts`: AC9 folds the fix in.

## Verification
- `tsc --noEmit` and `biome check .` are clean in invai-backend. Contracts `tsc` is clean. Contracts `biome check .` shows **one pre-existing error** in `src/schemas/vendors.ts` (formatting of `sheetSpecPdfCapError`, from T-9-3's committed code); not touched.
- Full backend `vitest run` on `invai_test_t121` with `REDIS_URL=…/12`: **87 files, 635 tests passed** (the tree also had T-8-6's and the wave 9 reviews' uncommitted edits).
- Real run: the worker (`NODE_ENV=development`, DB `invai_test_t121`, Valkey /12) and the API on :3121 with a token.
  - The sweep ran at start and logged `abandoned job row marked failed` for a seeded 2-hour-old running row; the row became `failed`.
  - A hand-added `shipping.retryStuckIntent` job with bad input and `attempts: 5` ended `failed` with `attemptsMade 1`.
  - curl without the token returned 404. With the token: `/dlq/failed` listed that job; `/dlq/redrive` returned `{"retried":["t121-bad-input"],"notFound":["nope"]}`; `/dlq/redrive-outbox` returned `{"reset":0}`.
- Cleanup: my worker and API were stopped, Valkey DB 12 flushed, `invai_test_t121` dropped.

## Cross-card notes
- **invai-web breaks on the new alert kinds.** `routes/_app/index.tsx` `alertKindLabel` has an exhaustive `switch` over `Alert["kind"]` with no default, so web `typecheck` will fail until someone adds 3 cases and `alerts.kind.*` in `en.ts`/`es.ts` (suggested en: "Background work is failing", "A background step was set aside", "AI spend check was skipped"). This needs the web-engineer, same day.
- **T-12-3:** `lib/queues.ts` now exports `processJob`, `withJitter`, `DEFAULT_BACKOFF` and `LIVE_JOB_STATES`. For the semaphore, re-delay with `moveToDelayed` + `DelayedError`, never `UnrecoverableError`. `channels/jobs.ts` changes are landed; add the poll jitter on top.
- **T-12-2:** migration numbering: I took `0024`. `shutdown()` doesn't need to change for the sweeps (they are ordinary jobs on `reports`).
- **Follow-up (not built):** a stuck `received` webhook row still makes the channel's retry count as a duplicate. Forgetting the row once it's flagged would let the retry through. Paging for the new alert kinds stays deferred (waves 10/11).

## Addendum (tech lead grants, same day)
- `319027a` approved by the tech lead.
- invai-web `fbe4507`: `alertKindLabel` cases + en/es `alerts.kind.*` for the 3 new kinds (by hand). Web tsc clean, biome clean on the 3 files, vitest 14 files / 78 tests pass, `vite build` OK.
- invai-contracts `02518b8`: `biome format` of `src/schemas/vendors.ts` only. Contracts `biome check .` now clean; vitest 4 files / 31 tests pass.
