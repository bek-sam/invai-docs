---
name: wave22-t22-2-composite-fks
description: T-22-2 lessons — RLS makes trigram/LIKE indexes unusable for invai_app (leakproof rule); drizzle emits composite FKs before the parent unique keys; composite SET NULL needs a column list; hand-fixing a generated migration before apply
metadata:
  type: project
---

# T-22-2 (2026-09-29): composite tenant FKs, migrate lock, stall settings

- **RLS + trigram search is a dead end for the app role.** An RLS policy is a security barrier, and
  only leakproof operators may become index conditions ahead of it. `textlike` (`LIKE`),
  `texticlike` (`ILIKE`), `similarity_op` (`%`), `ts_match_vq` (`@@`), `arraycontains` are NOT
  leakproof; `texteq` (`=`), `uuid_eq`, `starts_with` (`^@`) are. So under `withTenant` the
  planner never uses a `gin_trgm_ops` condition (proved with EXPLAIN on a 50k-row copy: the same
  query as `invai` owner uses the GIN, as `invai_app` it seq-scans, even with `enable_seqscan =
  off`). The 0001 trigram indexes on orders/order_items/designs have never served a request.
  **Why:** research 11 G17 assumed tenant-leading GIN indexes fix search cost; they can't under RLS.
  **How to apply:** don't add trigram indexes for app-role `ilike` searches; a real fix is a design
  decision (prefix `^@` search with SP-GiST, an external index, or accept per-tenant seq scans).
- **drizzle-kit orders `ADD CONSTRAINT ... FOREIGN KEY` before the parent's new
  `UNIQUE (company_id, id)`** in the same generated file, so the file cannot apply as generated.
  Reorder by hand before anyone applies it (allowed: "never hand-edit an *applied* migration").
- **Composite FK with `set null` needs `ON DELETE SET NULL (<col>)`** (PG 15+ column list) or the
  cascade nulls `company_id`. drizzle's `foreignKey().onDelete("set null")` can't express it; the
  SQL file is the truth, the schema says `set null`, and `fk-coverage.test.ts` checks the shape.
- **DrizzleQueryError wraps pg errors:** assert `rejects.toMatchObject({ cause: { code: "23503" } })`,
  not `{ code }` at the top level.
- **A failing-first coverage test on a scratch DB leaves rows behind** (my CROSS-1 insert made the
  later `VALIDATE CONSTRAINT` fail on the same DB). Drop and recreate the scratch DB after a red
  run that inserted data, before re-migrating it.
- `SET LOCAL lock_timeout` on the advisory-lock wait works because `pg_advisory_lock` is
  session-level: take it inside `BEGIN … COMMIT` with `SET LOCAL statement_timeout = 0`, then
  set the session-level migration timeouts. A pool `options: "-c statement_timeout=200"` is the
  way to prove in a test that the role default is overridden.
- BullMQ stall test: `skipLockRenewal: true` + `lockDuration: 1000` + `stalledInterval: 500` +
  a never-resolving handler + `concurrency >= 2` plays a frozen worker; `maxStalledCount: 1`
  gives exactly one re-run, then `failedReason` matches /stalled/. Close with `worker.close(true)`.
- **A full `vitest run` whose Duration is tens of minutes with 30 s-timeout tests reporting 16-minute
  durations was suspended, not slow**: every failure was time-shaped (expired Shopify OAuth link,
  expired presign 403, "redis timeout", "pool after end" under a stalled job) and the same 6 files
  passed in 14 s on re-run. Re-run the failed files before reading them as regressions; report the
  clean run and the stalled one both.
- Another agent running the full suite in the shared tree sees my half-written batch: write the
  service hunk before its test, or commit the two together, so their run doesn't report my red test.
