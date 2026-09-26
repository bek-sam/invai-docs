# Wave 12 plan review — architect, r1

Scope as in the PM review. Read-only against `invai-backend/src/{lib,worker,api,db}`; no DB touched, no code committed.

## Verdict: approve with the changes now applied to the cards and `wave.md`

## Ownership split (the actual request: 4 backend-foundation cards, up to 3 parallel)

Traced real file collisions by reading the code, not just the card text:

- `src/lib/queues.ts` and `src/worker/outbox-relay.ts` are T-12-1's foundation (backoff/jitter semantics, the jobId fix). T-12-3's fairness logic (priority for bulk vs interactive jobs) and its poll-jitter change to `modules/channels/jobs.ts` sit on top of the same file T-12-1 fixes — so **T-12-1 goes first**, not in parallel with the other three.
- `src/worker/index.ts` is genuinely touched by three cards (T-12-1 doesn't need to, corrected above), but only two after that fix: T-12-2 owns the `shutdown()` function (bottom), T-12-3 owns the `Worker` processor callback (top, for the per-tenant semaphore). Named both as distinct regions in `wave.md` rather than granting the whole file to one owner — they don't overlap line-for-line.
- `src/api/app.ts` is touched by T-12-1 (mount `/internal/*`), T-12-2 (`/livez`, `/readyz`), and T-12-5 (headers) — all three are additive (new route or new header line), so genuinely parallel-safe; called out as a coordination point, not a blocker.
- T-12-4 is the cleanest: it lives almost entirely in a new `modules/privacy/*` and a new contract file, with only additive touches elsewhere (`lib/s3.ts` gets a new helper, `db/schema/tenancy.ts` gets one new enum value, `api/router.ts` gets one new line). It's the strongest candidate to run fully in parallel, or first if a 4th slot opens.

Net: **T-12-1 sequenced first; T-12-2, T-12-3, T-12-4 in parallel after**, per the file-level table now in `wave.md`.

## Contract stubs

**DLQ/redrive.** The card and the research doc both say "an admin redrive action... behind `platform.admin`" — that permission doesn't exist. `invai-contracts`' roles are all company-scoped (`ROLES` = owner/admin/office/designer/presser/packer/receiver/vendor); there is no cross-tenant session type in `AuthMode`. Redrive and the failed-job list are inherently cross-tenant (a queue's failed set spans every company). Building it as an oRPC tenant procedure would force a choice between two bad options: invent a fictitious permission no real user has, or grant it to some shop's `owner`, which would let a shop see every other shop's failed jobs. Designed it instead as internal-only Hono routes (`src/api/internal.ts`, header-token gated), matching the shape the research doc itself already assumes for the outbox ("a runbook script, re-drive outbox from time T") — same operation, just reachable over HTTP for convenience. Exact routes and bodies are in `wave.md` stub A.

**Export/delete.** This one *is* tenant-scoped and fits the existing permission model cleanly: added `org.export`/`org.delete`, owner-only. Designed the procedures to reuse three patterns that already exist rather than invent new plumbing:
- The generic `jobs` table + `job.progress` realtime event (already used by every other async action) — added one `JOB_KINDS` value (`"tenant_export"`) instead of a bespoke export-job table.
- The existing `files` + `files.downloadUrl` presigned-GET flow for retrieving the finished zip — no new download endpoint.
- The `.errors({...})` per-procedure pattern already used throughout `invai-contracts` (e.g. `channels.ts`'s `ALREADY_CONNECTED`) for the two new codes, `EXPORT_IN_PROGRESS` and `DELETION_ALREADY_REQUESTED`, rather than adding to `COMMON_ERRORS` (they're domain-specific, not shared across procedures).

Both stubs are written out as literal TypeScript in `wave.md` so the builder isn't guessing at shapes.

## Fairness: checked, BullMQ "groups" is not available

`invai-backend/package.json` and `pnpm-lock.yaml` show only `bullmq@6.3.8` (open source). "Groups" is a `bullmq-pro` (`@taskforcesh/bullmq-pro`) feature — separately licensed, not in the lockfile, not mentioned anywhere else in the repo. Recommended against adding it this wave (a new paid dependency is an owner-track call, and the research doc itself only lists it as "SHOULD (next)", price unverified). T-12-3 now specifies the free mechanism the research doc names as the "MUST (now), cheap version": a per-`{queue, companyId}` Valkey semaphore with `moveToDelayed`/`DelayedError` re-delay, plus BullMQ `priority` for bulk vs interactive job kinds. Sharding into `hash(companyId) % K` sub-queues is kept as a documented fallback, gated on the card's own load-test evidence rather than built speculatively.

## Scope: AWS flagged out

Went through research §§2-5 line by line against the 5 cards. Everything the cards need (rate limiting, health/shutdown, DLQ, export/delete, CSP) runs against local Postgres/Valkey/MinIO with no code-level AWS dependency. Flagged the adjacent items that are AWS/deploy-time and must not leak into this wave: ECS deployment circuit breaker + CloudWatch alarms + ALB health-check path (T-12-2's neighbors in research §4.2), the per-tenant DB-time CloudWatch-style dashboard and `tier` column (T-12-3's neighbors in §2.3/2.5), and confirmed T-12-4's object-storage work is already MinIO-abstracted so it will run unchanged once S3 replaces MinIO later — no action needed now beyond what the card already excludes (KMS).

## Residual concerns

- T-12-1's new alert kinds (`queue_failed_spike`, `outbox_parked`, `ai_breaker_fail_open`) are additive to `ALERT_KINDS`, but any code elsewhere doing an exhaustive `switch` on that union (e.g. an alert-icon map in web/floor) will fail to typecheck until updated — worth a heads-up to whoever owns that, not a blocker for this wave.
- T-12-4's cross-tenant safety criterion (item 8) is the highest-value test in the whole wave given the `pii, tenancy` risk flags; made it explicit that it must use the RLS test-harness pattern (`db/rls-coverage.test.ts`), not a mocked permission check, since that's the class of bug RLS exists to catch and a mock would pass even if RLS itself were misconfigured.
