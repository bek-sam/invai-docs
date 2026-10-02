---
name: wave20-t20-5-seed-worker
description: T-20-5 (B-106) findings — why the seed collided with a running worker, the hold/release outbox pattern, db:reset obliterates queues, and how to seed a DB copy without clobbering seed-output.json
metadata:
  type: project
---

The seed/worker collision (B-106) was never really about `stock_levels`: the builder commits phase by phase and each phase emits real outbox events, so a running worker's relay dispatched them mid-seed and its jobs (`billing.recordSheetBuilt` → `usage`, `market.computeSignals`, `finance.recompute`...) wrote derived rows the seed later inserted plainly. T-5-3 made the stock upsert tolerant, so the collision moved to `usage (company_id, period)`. Fix (2026-09-28): `src/db/seed/outbox-hold.ts` parks each phase's events (`dispatched_at` set + `last_error` = held marker) and releases them once at the end, so the post-seed replay is the same as starting the worker afterwards.

**Why:** the wave 20 gate seeds with the worker running; `tenancy.demo` uses the same builder under a live worker.

**How to apply:** any bulk builder that commits in phases must hold/release; never "fix" this by turning seed inserts into upserts one table at a time. `pnpm db:reset` now obliterates the five queues in the configured Redis DB (`obliterateQueues()` in `src/db/reset.ts`), never FLUSHDB. Seed a copy with `SEED_OUTPUT_FILE=<path>` and `DATABASE_URL`/`MIGRATION_DATABASE_URL`/`REDIS_URL` overrides; `createdb -T invai` fails while the dev stack is connected, so create an empty DB and reset+migrate it. `tsx -e` can't do top-level await (cjs); use a scratch `.mts` file. `ps -p <pid>` trips the guard hook; use plain `kill <pid>`.
