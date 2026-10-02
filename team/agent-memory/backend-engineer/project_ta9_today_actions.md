---
name: ta9-today-actions
description: T-A9 gotchas - fk-coverage demands (company_id,id) FK targets, guard hook blocks git checkout/pkill, Track E runs in a savepoint
metadata:
  type: project
---
2026-09-30 T-A9: `src/db/fk-coverage.test.ts` fails any tenant FK whose parent key isn't exactly `(company_id, id)`; natural-key FKs like `(company_id, date, key)` must become `set_id`/`action_id` columns. Check it before `db:generate`.
**Why:** cost a regenerate of an already-applied local migration (had to drop tables + the `drizzle.__drizzle_migrations` row in dev and invai_test).
**How to apply:** run `vitest src/db` right after the first `db:generate`. To undo an uncommitted migration: `git show HEAD:drizzle/meta/_journal.json > …` (guard hook blocks `git checkout <path>` and `pkill`; kill tsx parents by saved PID, children exit with them).
Digest snapshot's `trackE` (D9..D13 inputs) is optional and computed in a savepoint; hand-built Snapshots in QA acceptance tests omit it.
