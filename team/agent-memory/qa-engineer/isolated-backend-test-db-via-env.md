---
name: isolated-backend-test-db-via-env
description: How to run an invai-backend acceptance test against a private named DB/Redis DB without createdb or docker exec psql setup
metadata:
  type: project
---

To run a backend acceptance/vitest file against your own isolated DB (e.g. `invai_t20_qa3`) instead
of the shared `invai_test`, no manual `createdb`/migrate step is needed — `src/test/global-setup.ts`
calls `ensureDatabase` + `runMigrations` automatically against whatever `TEST_DATABASE_URL` /
`TEST_MIGRATION_DATABASE_URL` resolve to (see `src/env.ts`, only honored under `NODE_ENV=test`,
which `vitest` sets).

Command pattern:
```
export TEST_DATABASE_URL="postgres://invai_app:invai@localhost:5432/<your_db>"
export TEST_MIGRATION_DATABASE_URL="postgres://invai:invai@localhost:5432/<your_db>"
export REDIS_URL="redis://localhost:6379/<your_redis_db_index>"
pnpm test <path/to/test.ts>
```

**Why:** `createdb` isn't on PATH on this machine (no local Postgres client tools), and
`docker exec ... createdb` needs a TTY workaround (`docker exec` without `-it`, since stdin isn't a
terminal in the agent shell). Overriding the env vars sidesteps all of that and reuses the project's
own migration/reset code, which also grants `invai_app` correctly (unlike a raw `createdb -T invai`
copy, see [[dev-copy-db-grants]]).

**How to apply:** Cleanup after such a run is `docker exec local-postgres-1 psql -U invai -c "DROP
DATABASE <your_db>;"` and `docker exec local-valkey-1 valkey-cli -n <n> FLUSHDB` (this Valkey image
supports `valkey-cli`, no need to fall back to `redis-cli`).
