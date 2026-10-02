---
name: testing-jobs-reports-queue
description: Gotchas testing BullMQ jobs on invai-backend's "reports" queue (used by today/, digest/, etc.)
metadata:
  type: feedback
---

When writing a Vitest test that runs a real BullMQ Worker against the `reports` queue (today,
digest, alerts jobs):

- The `reports` queue sets a default job `priority` (`REPORTS_BULK_PRIORITY` in `src/lib/queues.ts`),
  so a freshly-added, unprocessed job's real state is `"prioritized"`, not `"waiting"`. Assert
  against `LIVE_JOB_STATES` (exported from `src/lib/queues.ts`) rather than hardcoding `"waiting"`.
- `vitest.config.ts` sets `fileParallelism: false` (files run one at a time, sharing one test DB),
  but functions that page across *every* tenant (e.g. `shopsMissingToday` /
  `sweepTodayActions` in `today/jobs.ts`) will still pick up companies created by *other* test
  files in the same module that never built the entity being checked for — confirmed this
  returned 5 unrelated companies on a scoped call. Test the per-shop helper directly
  (e.g. `requeueBuild`) instead of the broad sweep/pager when you need a deterministic count.
- A real `Worker` with concurrency > 0 grabs a newly-`queue.add()`-ed job almost instantly; there
  is no reliable window to assert "waiting"/"prioritized" state while a worker consuming that
  queue is alive (even `worker.pause(true)` didn't reliably prevent the race in bullmq 6.3.8).
  Put that assertion in a separate `describe` with no worker started at all (safe given
  `fileParallelism: false` — the previous describe's `afterAll` already closed its worker).
- Jobs left in Redis by an aborted test run (e.g. a killed background `pnpm test`) persist across
  later runs that reuse the same claimed Redis DB number and get reprocessed, logging confusing
  errors. Mirror `src/lib/queues.test.ts`'s pattern: `queue.obliterate({ force: true })` in both
  `beforeAll` and `afterAll` for any describe that runs a real Worker on a shared queue name.
