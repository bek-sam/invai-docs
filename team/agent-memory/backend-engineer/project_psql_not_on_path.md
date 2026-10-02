---
name: project-psql-not-on-path
description: psql is not installed on this machine's PATH; create/drop scratch Postgres databases via `docker exec local-postgres-1 psql -U invai -d postgres -c "..."` instead.
metadata:
  type: project
---

`psql` is not available directly in the shell on this machine (`command not found: psql`), even
with the pnpm PATH export from CLAUDE.md. Same for a bare `redis-cli`.

**Why:** Discovered creating a private review DB (`invai_t20_rev3o`) for T-20-3. `docker ps` shows
the local Postgres container as `local-postgres-1` (compose project `local`) and Valkey as
`local-valkey-1`.

**How to apply:** To create/drop a scratch test database for a card review or verification pass:
`docker exec local-postgres-1 psql -U invai -d postgres -c "CREATE DATABASE <name> OWNER invai;"`
(and `DROP DATABASE IF EXISTS <name>` to clean up). To flush a scratch Redis DB index used for a
review: `docker exec local-valkey-1 redis-cli -n <n> FLUSHDB`. Then point `TEST_DATABASE_URL`
(`postgres://invai_app:invai@localhost:5432/<name>`), `TEST_MIGRATION_DATABASE_URL`
(`postgres://invai:invai@localhost:5432/<name>`), and `REDIS_URL`
(`redis://localhost:6379/<n>`) at them as usual — the containers still expose the normal host
ports, only the local `psql`/`redis-cli` binaries are missing.

**Getting the role swap wrong is silent, not an error** (hit on T-A5 AC-C3 follow-up): pointing
`TEST_DATABASE_URL` at the owner role (`invai`) instead of `invai_app` doesn't fail — the owner
role bypasses RLS as the table owner, so every `withTenant()` query in the run silently returns
rows across ALL companies instead of just the current one. It surfaces later as a baffling
cross-tenant FK violation (e.g. `purchase_orders_location_id_fk` pointing at another test
company's location) that looks like a product bug but is a test-env credential swap. If a
service test gets the "wrong tenant's row" in a scratch DB, check `TEST_DATABASE_URL`'s role
first.
