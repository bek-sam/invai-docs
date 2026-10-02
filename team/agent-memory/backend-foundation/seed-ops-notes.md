---
name: seed-ops-notes
description: Scratch-stack seed operational gotchas — shared-array clobbering, scheduled job sweeps, env var overrides, and timing
metadata:
  type: feedback
---

Accumulated seed-builder operational lessons (T-20-5 r2, T-A1).

- **Shared insert loop can clobber a per-path decision.** A seed's closed-history block can
  compute a correct per-order value (e.g. on-time/late `shippedAt`) and still have it silently
  overwritten later if that order is also pushed onto a *shared* array (`shippedOrders`) that a
  later, single "shipments" loop uses for both live-flow and historical orders — that shared loop
  recomputed `labeledAt` from scratch for everyone instead of trusting an already-decided value.
  When a seed builder has two code paths feeding one shared insert loop, check whether the shared
  loop clobbers per-path decisions. A starter metrics SQL query (`late_rate_drivers.sql`) run
  against the live seed caught this (0% lateness across every driver), not code reading alone.
- **Scheduled job sweeps fire on registration, not just on events.** The outbox hold only stops
  event-driven jobs; `upsertJobScheduler` sweeps (`today.alertsSweep`, `channels.poll`) fire on
  registration and hit a half-built shop, so a bulk builder upserts every row a sweep can also
  create. `today.generateAlerts` job ids are bucketed per 5 min: re-enqueuing inside a bucket is a
  no-op, a "next tick" proof needs a fresh bucket and must filter `type = 'shop'`.
- **Scratchpad tsx scripts** need a `package.json {"type":"module"}` (else `require(esm)` with a
  top-level await fails) and should import `pg`/drizzle through the backend's `src/db/client`, not
  by package name.
- **`seedOutput()` hardcodes the shared file.** `invai-web/e2e/helpers/api.ts`'s `seedOutput()`
  hardcodes `<backend>/seed-output.json` with no env override, so `api-golden-path.spec.ts`'s
  floor/station tests (8+) can't run against a scratch DB's own seed without writing to the shared
  file — forbidden. Verify the floor/station path by hand instead (`POST /rpc/floor/staff` with
  the scratch seed's own station token + `x-contract-version` header from
  `invai-contracts/src/compat.ts`); don't touch the shared `seed-output.json`.
- **Seed timing varies legitimately.** Back-to-back `db:reset && db:migrate && db:seed` runs on a
  warm Postgres/imaging/MinIO stack can take 31s vs. 543s on a first cold run after an OrbStack
  restart — before flagging a timing anomaly, check MinIO
  (`docker exec local-minio-1 mc ls --recursive local/invai-local/<companyId>/`) for real files
  with plausible timestamps/sizes; that's stronger evidence than wall-clock alone.
- See also [wave-p5-seed-cleanup.md](wave-p5-seed-cleanup.md) for the REDIS_URL/SEED_OUTPUT_FILE
  pinning rule.
