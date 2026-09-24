# Isolated local stack for real shop data

Real exports never go into the shared dev database (`invai`) or the test database (`invai_test`). Give each dry run its own database, Redis DB index and ports.

**Status:** written from `invai-backend/src/env.ts`, `invai-infra/local/init.sql` and `invai-web/.env.example`, but **not yet exercised end to end**. The first person to run it fixes this file (through `log-lesson` if something was wrong).

```sh
export PATH="$HOME/.local/share/pnpm/bin:$HOME/.local/share/pnpm:$PATH"
SLUG=pilot-a                                  # customer folder slug
DB=invai_dryrun_${SLUG//-/_}

# 1. Database with the same grants and extensions as init.sql
docker exec -i local-postgres-1 psql -U invai -d postgres -c "CREATE DATABASE $DB OWNER invai;"
docker exec -i local-postgres-1 psql -U invai -d $DB <<'SQL'
GRANT USAGE ON SCHEMA public TO invai_app;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;
SQL
# Copy the remaining GRANT / ALTER DEFAULT PRIVILEGES lines from invai-infra/local/init.sql too.

# 2. Environment for the isolated API and worker (Redis DB 7 keeps BullMQ queues apart)
export DATABASE_URL=postgres://invai_app:invai@localhost:5432/$DB
export MIGRATION_DATABASE_URL=postgres://invai:invai@localhost:5432/$DB
export REDIS_URL=redis://localhost:6379/7
export PORT=3150
export WEB_ORIGIN=http://localhost:5180
export BETTER_AUTH_URL=http://localhost:3150

cd invai-backend
pnpm db:migrate                       # schema only; do NOT run db:seed (no demo data mixed in)
pnpm dev:api &                        # API on :3150
pnpm dev:worker &                     # worker on the isolated Redis DB

# 3. Web pointed at the isolated API
cd ../invai-web
VITE_API_URL=http://localhost:3150 pnpm dev --port 5180 &
# Imaging (:8000) is stateless and can be shared.
```

Open http://localhost:5180/signup and create the fresh company.

## Tear down (always)
Delete the real files from MinIO **before** dropping the database: you need the company id to find them. Keys are `<companyId>/<kind>/...` in bucket `invai-local`. `MC_HOST_local` gives `mc` (inside `local-minio-1`) the credentials without writing any config.
```sh
kill %1 %2 %3                          # or the PIDs you started
mcl() { docker exec -e MC_HOST_local=http://invai:invai-secret@localhost:9000 local-minio-1 mc "$@"; }
for CID in $(docker exec -i local-postgres-1 psql -U invai -d $DB -tAc "select id from companies"); do
  [[ $CID =~ ^[0-9a-f-]{36}$ ]] || { echo "not a company id: '$CID', stop"; break; }
  mcl ls --recursive local/invai-local/$CID/          # dry listing: must show only this dry run's files
  mcl rm --recursive --force local/invai-local/$CID/  # required: delete the real shop's files
  mcl ls --recursive local/invai-local/$CID/          # must print nothing
done
docker exec -i local-postgres-1 psql -U invai -d postgres -c "DROP DATABASE $DB WITH (FORCE);"
docker exec -i local-valkey-1 valkey-cli -n 7 FLUSHDB
```
Never run `mc rm` on the bucket root or with an empty id: that deletes the demo shop's files too. `mc rm --dry-run` prints what would go without deleting.
