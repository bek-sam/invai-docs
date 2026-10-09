# T-30-2: Compiled entry points: api, worker, bootstrap, migrate, reference seed; SMTP env proven against Mailpit

| Field | Value |
|---|---|
| Wave | 30 |
| Scope ref | `always-in-scope: security, reliability` (deploy prep, owner order 2026-10-09; decision 0019 still fences AWS); backlog B-01, B-03 (migrate step), B-59, B-58 (code side) |
| Spec | `waves/24/T-24-2.md` (replaced by this card; KMS part moves to wave 31), `waves/24/reviews/plan-architect.md` (A1 entry points), `research/11` G1/G3, `build/audit-2026-09-24.md` |
| Owner | backend-foundation |
| Reviewer | reviewer (fable) |
| Co-reviewers | security-reviewer (opus) |
| Risk flags | auth (database roles and grants, RLS), migration (release path) |
| Model | opus |

Role file: `.claude/agents/backend-foundation.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/backend-foundation/` (read MEMORY.md first).

## Owned paths (edit)
- `invai-backend/tsup.config.ts`, `invai-backend/package.json` (scripts only; a new dependency needs a reason in the report)
- `invai-backend/src/db/{bootstrap,bootstrap-cli,migrate-cli,reference-seed-cli}.ts` (new), `src/db/migrate.ts`, `src/db/reference/index.ts` (only if the CLI needs an export), their tests (`src/db/*.test.ts`)
- `invai-backend/src/env.ts`, `src/env.test.ts`
- `invai-backend/README.md` (build and release section)
- Report: `invai-docs/waves/30/reports/T-30-2.md`

## Read-only paths
- `invai-backend/Dockerfile` and every `.dockerignore` (platform-sre, T-30-3 runs in parallel), `invai-infra/**` (read `sst.config.ts` lines 85–100 and 450–470 for the env names the release task passes), `invai-infra/local/init.sql` (the local grants to mirror), `drizzle/**` (no new migration)

## Interfaces promised (architect A1, wave 24; SST already uses them)
- `node dist/api/server.js`, `node dist/worker/index.js`, `node dist/db/bootstrap-cli.js`, `node dist/db/migrate-cli.js`, `node dist/db/reference-seed-cli.js`. Migrations are read from the `drizzle/` folder next to `dist/` (in the image `/app/drizzle`). Commit the build config change first (a commit with the five entries building) so T-30-3 can start; tell the tech lead its SHA in a progress line of your report.

## Acceptance criteria
1. `pnpm build` produces exactly those five files; `start:api`/`start:worker` and the README use the new paths. `pnpm dev:api`, `pnpm db:migrate`, `db:reset`, `db:seed` and the gate (`invai-infra/scripts/gate.sh`) behave as before.
2. **bootstrap-cli**: connects as the owner role (`MIGRATION_DATABASE_URL`), takes the app role's name and password from `DATABASE_URL` (or `APP_DB_PASSWORD`, as the SST comments describe), and creates or updates that role as `LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE` with exactly the grants `invai-infra/local/init.sql` and `drizzle/0001_grants_extensions.sql` give `invai_app` (database connect, schema usage, default privileges for tables and sequences, existing tables and sequences). Running it twice changes nothing; it never prints the password or a URL with a password (also not on error). It refuses to run if the app role equals the owner role.
3. **migrate-cli**: runs `runMigrations` from `dist/` with the folder resolved to `<app>/drizzle` (prove it from a directory other than the repo); keeps the advisory lock and `MIGRATION_SESSION` timeouts; exits non-zero with a one-line error on failure. **reference-seed-cli**: `ensureReferenceData` only (plans, trademark marks), no tenant rows, idempotent.
4. The API and worker from `dist/` connect as the app role and RLS applies: on the bootstrapped DB, a query on a tenant table as the app role without a tenant setting returns no rows.
5. **SMTP (B-58 code side).** `SMTP_URL`/`MAIL_FROM` stay in the schema and in `PRODUCTION_KEYS`; production without them and without `ALLOW_MOCKS=true` refuses to boot (a test exists or you add it in `env.test.ts`). With `NODE_ENV=production ALLOW_MOCKS=true SMTP_URL=smtp://localhost:1025`, the compiled API sends one real auth email (sign-up verification or password reset for a user on your throwaway DB, address `@example.test`) and it arrives in Mailpit (`curl localhost:8025/api/v1/search?query=to:...`); delete that message afterwards.
6. Edge: a CLI started with a missing or malformed URL exits non-zero without a stack trace that prints secrets.

## Verification
- `cd invai-backend && pnpm typecheck && pnpm lint && pnpm test` (full suite once at the end, `set -o pipefail`, log file, timeout 600000) and `pnpm build`.
- Exercise for real on a **throwaway Postgres container** (roles are cluster-wide; never run bootstrap against the shared `local-postgres-1`): `docker run -d --name invai-t30-pg -p 5440:5432 -e POSTGRES_USER=invai -e POSTGRES_PASSWORD=invai pgvector/pgvector:pg17` (the image compose uses), then from a copy of `dist/` + `drizzle/` outside the repo: bootstrap twice, migrate twice, reference seed twice (row counts equal), API on `PORT=3132` with `REDIS_URL` on Valkey DB 13, `/health` ok, the RLS check from AC4, the Mailpit check from AC5. Remove the container afterwards (`docker rm -f invai-t30-pg`).
- Record every PID and container you start in the report and stop them all.

## Out of scope
- Dockerfiles, compose, SST (T-30-3 and the owner), KMS field encryption (B-23, wave 31), SES and DKIM (owner, AWS), any new migration.

## Commit and report
- Commit only your paths, message ends with the attribution line. Don't push; only the tech lead pushes after the gate.
- Report ≤ 60 lines in `verify-and-report` format, with progress lines as you go.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
