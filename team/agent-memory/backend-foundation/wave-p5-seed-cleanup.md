---
name: wave-p5-seed-cleanup
description: Always pin REDIS_URL and SEED_OUTPUT_FILE before any scratch db:reset/seed run
metadata:
  type: feedback
---

Always export both `REDIS_URL=redis://localhost:6379/<scratch-db-number>` and
`SEED_OUTPUT_FILE=/tmp/<scratch>.json` before running `tsx src/db/reset.ts` or
`tsx src/db/seed/index.ts` against any scratch Postgres database, even a one-off.

**Why:** 2026-10-01 T-P5-1 — the builder ran `reset.ts` once without `REDIS_URL` pinned and
`obliterateQueues` hit the *default* Redis DB 0, wiping real in-flight queues
(sync/render/ship/ai/reports jobs, not recoverable for ad-hoc jobs). A second run without
`SEED_OUTPUT_FILE` overwrote the shared `invai-backend/seed-output.json` with the scratch
company's ids, requiring a station-token reissue to fix. DATABASE_URL/MIGRATION_DATABASE_URL
being correctly scoped to the scratch DB did not protect Redis or the seed-output file — those
have their own, separately-defaulted env vars.

**How to apply:** before the *first* `reset`/`migrate`/`seed` command of any scratch-DB session,
set all three: `DATABASE_URL`/`MIGRATION_DATABASE_URL` (scratch DB), `REDIS_URL` (a scratch Redis
DB number, e.g. `/13`), `SEED_OUTPUT_FILE` (a `/tmp/...json` path). Treat a missing `REDIS_URL` or
`SEED_OUTPUT_FILE` as a hard stop, not a thing to fix after the fact.
