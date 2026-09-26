# Review of T-12-1 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: backend-foundation on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` (invai-contracts) | clean |
| `pnpm lint` (invai-contracts, `biome check .`) | clean, 46 files |
| `pnpm typecheck` (invai-backend) | clean |
| `pnpm lint` (invai-backend, `biome check .`) | clean, 280 files |
| `pnpm typecheck` (invai-web) | clean |
| `pnpm lint` (invai-web) | clean, 143 files |
| own-DB migrate (`invai_test_review121`, copy of `invai`) | `[migrate] up to date` — migration 0024 already applied cleanly |
| `pnpm vitest run` (invai-backend, own DB `invai_test_review121`, own Redis DB 14→13) | **87 files, 635 tests passed** — matches the report |
| `scan-test-weakening.sh invai-backend origin/main` | hits, all read and non-blocking (below) |
| `scan-test-weakening.sh invai-contracts origin/main` | no hits |
| `scan-test-weakening.sh invai-web origin/main` | 1 hit, belongs to a different, unrelated commit (below) |
| Live API (`PORT=3129`, own DB+Redis, `INTERNAL_ADMIN_TOKEN` set) — `curl` matrix | see AC3 row |
| DB and Redis cleanup | own test DB dropped, own Redis DB flushed, API process killed |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Jitter per job type | yes | `src/lib/queues.ts` `withJitter`/`DEFAULT_BACKOFF`; `queues.test.ts` "20 failures... retry after different, jittered delays" passes, delays land in `[1000,2000]` with >1 distinct value; a job with its own backoff (`ownBackoffJob`, exponential 10s) keeps its delay and gains jitter |
| 2. `UnrecoverableError` | yes | `permanentFailure()`, `isPermanentHttpStatus()`, `parseJobInput()` in `queues.ts`; tests show Zod-invalid input and a 422 both end `failed` with `attemptsMade === 1`; a 503 stays `delayed` at `attemptsMade === 1` |
| 3. DLQ + alert + redrive | yes | `src/api/internal.ts`, mounted at `/internal` (`app.ts:109`), **before** `/rpc/*`'s tenant middleware and outside `/api/v1` — confirmed live: no header → 404, wrong token → 404, unset token → 404 (test + live curl), right token → 200 with real data, unknown `/internal/*` path → 404, `/rpc/internal/dlq/failed` and `/api/v1/internal/dlq/failed` → 404 (not tenant-reachable). `checkFailedSpikes` uses a Valkey `SET NX` flag per queue so one spike alerts once regardless of tick count or failed-job count (tested across 3 ticks) |
| 4. Outbox purge + parked alert | yes | `purgeDispatchedOutbox` batches deletes, keeps parked/pending/recent rows (test); `alertParkedOutbox` dedupes on `outbox_parked:<eventId>` via a left join on `alerts`, so a resolved alert stays resolved on the next sweep (test) |
| 5. Stuck sweeps, no double-processing a slow job | yes | `sweepStuckJobRows` only fails a row when **no** BullMQ job is in `LIVE_JOB_STATES` (active/waiting/waiting-children/delayed/prioritized) referencing it — a job that is merely slow but still `active` is protected by state, not by the 30-min threshold alone. The select→update re-checks `status`/`updatedAt` in the same `where`, closing the race where a job finishes between the scan and the failing update. `ai_jobs` sweep is analogous |
| 6. Buy/void/push intents | yes | Confirmed existing `stuckIntentSweepJob` covers all three; added void/push tests give `["failed","failed","alerted"]` and the right dedupe key, matching the existing buy test's shape |
| 7. Webhook deliveries | yes | `flagStuckWebhookDeliveries`: one flag per row (guarded by `isNull(detail)` in both the select and the update's `where`), alerts only when `companyId` is known, purge flags before deleting; tests cover both the alerted and no-company cases and the purge-then-flag order |
| 8. Outbox jobId fix | yes, with a reasoned, tested deviation — see below | `relayJobId()` prefers the subscriber's own `jobId`, falling back to the event-scoped id both when none is defined **and** when the same-id job has already finished (`completed`/`failed`) |
| 9. AI breaker fail-open alert | yes | `alertFailOpen` in `ai/breaker.ts`, Postgres-hour dedupe key + a 10-min in-process throttle; test forces `redis.mget` to reject 3 times and asserts exactly 1 alert row |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat` per commit): `1dcf156`/`02518b8` (contracts: `schemas/alerts.ts`, `schemas/vendors.ts` biome-only, both granted); `2f18b39`/`5ffbee6` (backend: `lib/queues.ts`, `worker/outbox-relay.ts`, new `worker/sweeps.ts`, new `api/internal.ts`, plus the coordination files `api/app.ts` (1 line), `channels/jobs.ts`, `env.ts`, all named in `wave.md`); `319027a` (`worker/index.ts`, tech-lead-approved per the addendum); `fbe4507` (web: `i18n/en.ts`, `i18n/es.ts`, `routes/_app/index.tsx` — exactly the 3 new alert kinds, tech-lead-granted). No file outside the card's owned/granted/coordination set.
- [x] Nothing outside scope — every change traces to an acceptance criterion or a named grant; migration 0024 additionally carries T-9-2's granted `vendor_connections.spec` default fix, called out in `wave.md`.
- [x] Tests exercise the behavior, and none were weakened. `scan-test-weakening.sh` hits in invai-backend are non-blocking: `vi.spyOn(redis, "mget")` and `vi.spyOn(pushTrackingJob, "enqueue")` mock dependencies of the code under test, not the unit under test itself; `vi.spyOn(realtime, "publish")` is an assertion spy, not a weakening; `if (!env.isTest)` in `sweeps.ts` matches the existing self-registration guard used by every other `modules/*/jobs.ts` (checked: channels, billing, orders, today, inventory, finance, shipping all do the same); the untracked `src/api/orpc.test.ts` and the other modified files listed by the scanner belong to other, uncommitted work already in the shared tree (per the report) and are not part of this card's commits. The 1 hit in invai-web (`fit.test.ts` assertion removal) belongs to commit `80fc945` (T-9-4), not to T-12-1's `fbe4507` — confirmed by `git log -- <file>`.
- [x] Tenancy (`withTenant`, RLS on new tables): no new tables. Cross-tenant reads use `withSystem` (outbox rows, `jobs`/`ai_jobs` sweep candidates — all pre-existing patterns for platform-wide sweeps); every alert write goes through `withTenant(companyId, ...)`. Idempotency: DLQ redrive keyed by job id and state-checked; outbox redrive resets `attempts`/`dispatchedAt` (re-running it is a no-op the second time, since the rows no longer match the `parked()` predicate); stuck-row updates re-verify their own precondition in the `UPDATE ... WHERE`. Money: none touched. En/es: the 3 new alert labels are in both `en.ts` and `es.ts`.
- [x] Decisions recorded: the jobId-fallback deviation, the optional `INTERNAL_ADMIN_TOKEN`, and the `redrive-outbox` attempts-reset are all explained in the report and match the code.

## Optional notes (not blocking)
- **AC8 deviation is correct and net safer than the card's literal wording.** The card says "fall back... only when [the job has] no own id." Implemented literally, a real duplicate business event whose same-id job already completed within its 24h Redis retention would be **silently dropped** (BullMQ ignores `add` on an existing id) — a worse bug than the one being fixed. The author's fallback-on-finished-job extension closes that gap and is covered by its own test (`outbox-relay.test.ts` "once that job finished, a later event still runs"). The accepted trade-off (a relay crash between enqueue and dispatched-mark, racing a fast job completion, could run a handler twice) is fine given `idempotent-job`.
- Cross-card note in the report is accurate and worth the tech lead's attention: web's `alertKindLabel` switch would fail `tsc` without the 3 new cases — already fixed by `fbe4507`, landed same day.
