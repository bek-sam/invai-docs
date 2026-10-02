---
name: migration-fk-review-checks
description: Fast checks for hand-edited drizzle migrations (composite FKs, NOT VALID/VALIDATE) and pg_constraint-based coverage tests
metadata:
  type: feedback
---

2026-09-29 T-22-2 r1 (approve):
- Hand-edited drizzle SQL: use a short node script to compare the SQL's ADD CONSTRAINT lines with `drizzle/meta/NNNN_snapshot.json` (table, cols, target, onDelete). Also compare the previous snapshot's FK onDelete per (table, col) to catch delete-semantics drift. Then run `drizzle-kit generate` in a scratch worktree (symlinked node_modules, no DB needed, about 10 s) for the drift check.
- Coverage tests that introspect pg_constraint: mutation-test them by adding a canary constraint to your own scratch test DB, running the test (it must go red), then dropping the canary. This is cheaper than a base-code worktree run.
- `createdb -T invai <copy>` worked even with 2 idle sessions on `invai`. Migrate the copy with `MIGRATION_DATABASE_URL` exported before `tsx src/db/migrate.ts`.
- Composite `ON DELETE SET NULL (<col>)`: drizzle can't express the column list, and the coverage test didn't check `confdelsetcols`. Flag this as a latent regeneration hazard.

**Why:** these gave decisive evidence in minutes, without a full suite.
**How to apply:** use them on any migration or tenancy card that touches FKs or constraints.
