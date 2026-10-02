---
name: reimport-live-probe
description: Cheap exact-payload re-import probe for orders cards - the Etsy CSV fixture holds dev seed order 3310000001, upload it via files.presignUpload + channels.importCsv on a pg_dump scratch copy
metadata:
  type: feedback
---

For "re-import must not change the order" claims (T-P4-1, decision 0020), don't hand-craft a payload:
`invai-backend/src/integrations/channels/csv/fixtures/etsy-sold-order-items.csv` is the exact payload the
dev seed imported for order `3310000001` (CSV etsy connection, `channel_connections.mode = 'csv'`), so
re-sending it is byte-identical. Recipe (read-only on the shared dev DB):
1. `createdb -O invai invai_rv_<card>` + `pg_dump invai | psql` inside `local-postgres-1` (124 MB, ~20 s).
2. API: `PORT=31xx DATABASE_URL=...invai_app...@/invai_rv_<card> MIGRATION_DATABASE_URL=... REDIS_URL=redis://localhost:6379/<n> ./node_modules/.bin/tsx src/api/server.ts` (no watch, no worker needed for inline CSV imports).
3. Owner cookie sign-in `POST /api/auth/sign-in/email` with `Origin: http://localhost:5173`; oRPC calls are
   `POST /rpc/<ns>/<proc>` with body `{"json":{...}}` and reply `{"json":...}` (e.g. `/rpc/files/presignUpload`,
   `/rpc/channels/importCsv` with `{id, fileKey, format:"etsy"}`). PUT the bytes to `uploadUrl` with the returned headers.
4. Compare `item_count`, per-unit `state`/`is_reprint` and total `order_items` before/after each send; expect
   `ordersUpdated:0, ordersSkipped:4, rowsFailed:1` (row 7 of the fixture is a deliberately bad row).
5. Cleanup: kill API, `pg_terminate_backend` then `dropdb`, flush the Redis DB (check `client list | grep db=<n>` is 0 first).

**Why:** the author's AC6 ran on a scratch dump too; re-doing it independently took ~5 calls and proved the
re-import no-op without touching the shared seed. `finance.recompute` enqueues a job (needs a worker), so for
profit arithmetic rely on the unit tests + `finance.orderProfit` read instead of a live recompute.

**How to apply:** any orders/import or finance card whose AC says "sent twice leaves counts unchanged".
See also [[env-backend-worktree-review]] for the base-commit red proof worktree (symlink node_modules, copy
HEAD test files in, run; `git worktree remove --force` cleans the copied files).
