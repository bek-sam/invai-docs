---
name: dev-copy-db-grants
description: A dev-DB copy made with `createdb -T invai` can come up without invai_app's table/sequence grants, breaking every login with "permission denied for table users" even though the schema is fine.
metadata:
  type: project
---

Found on wave 20 (`invai_t20_qa_dev`, already on disk from a prior session): Better Auth's
`sign-in/email` returned a 500 with a Postgres `42501 permission denied for table users` error,
even though the copy had the right schema and seed rows. `invai_app` had no grants on the copy at
all, while the source `invai` database (and every table created after) does — grants aren't always
carried by the copy's history the way you'd expect from `CREATE DATABASE ... TEMPLATE`, so don't
assume a `createdb -T invai <name>` copy is usable for anything beyond direct SQL until you've
proven login works.

**How to apply:** before trusting a dev-DB copy for E2E, curl `/api/auth/sign-in/email` against it
once. If you get `permission denied for table <x>`, reapply drizzle's own grants directly (as the
`invai`/migration superuser, from `invai-backend/drizzle/0001_grants_extensions.sql`):
```
GRANT USAGE ON SCHEMA public TO invai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO invai_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO invai_app;
```
Separately: starting your own API on a non-default port also needs `WEB_ORIGIN` (Better Auth's
trusted-origin check) and ideally `BETTER_AUTH_URL` set to match whatever port/origin you're
actually serving the web app on — the default `.env` values (`:5173`/`:3000`) 403 with
`INVALID_ORIGIN` otherwise, which looks like a login bug in Playwright (`waitForURL` timeout on
`/login`) but is purely an env-var mismatch. See [[web-build-needs-vite-api-url]] for the matching
`VITE_API_URL`/CSP piece of running an isolated web+API pair.
