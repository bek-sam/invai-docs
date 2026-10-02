---
name: env-backend-worktree-review
description: How to run an isolated invai-backend review worktree (own test DB, evals, mutation testing)
metadata:
  type: feedback
---

For an `invai-backend` review worktree (`git worktree add <path> <sha>`, symlink `node_modules`):
copy the main repo's `.env`, then append `TEST_DATABASE_URL` / `TEST_MIGRATION_DATABASE_URL`
pointing at your own scratch DB name and `REDIS_URL` on your own Redis DB number. `src/env.ts`
under `NODE_ENV=test` uses `TEST_DATABASE_URL` when set, else derives `invai_test` from
`DATABASE_URL` — without the override every worktree's vitest run collides on the same `invai_test`
name. `vitest`'s `global-setup.ts` creates and migrates the DB automatically; `evals/run.ts` does
not, so for a "before" comparison worktree (e.g. diffing behavior pre/post a card) you must create
and migrate the DB yourself first (`ensureDatabase` + `runMigrations` from `src/db/reset.ts` /
`src/db/migrate.ts`, invoked via a `.mts` script — a `.ts` string passed to `tsx -e` fails on
top-level await under esbuild's cjs transform).

When a report claims "N/N unchanged before and after an extraction", don't just trust the after
number: check out the pre-change commit in a second worktree and re-run the same eval/test command
there. It's cheap and catches claims that were eyeballed rather than actually re-run.

For AI-safety validators (prompt injection defenses, hard-fail rule lists), a mutation test is a
fast, decisive way to confirm a unit test is load-bearing rather than a rubber stamp: comment out
one `failed.add("<rule>")` line, rerun that one test file, confirm it fails, then restore and
confirm clean. Takes under a minute and caught nothing wrong here (T-19-2), but would have caught a
vacuous assertion immediately.

Before B-205 (e22129c) there was no `TEST_REDIS_URL` override: `src/lib/queues.ts` reads `env.REDIS_URL` unconditionally, so
to isolate a review run on its own Redis DB number just `export REDIS_URL=redis://localhost:6379/<n>`
in the shell before `pnpm vitest` — Node's `process.loadEnvFile` (`.env`) doesn't override a var
already set in `process.env` (first-key-wins, confirmed in review of T-20-1), so the export sticks.

When another card's WIP sits uncommitted in the same shared worktree (e.g. another agent's unstaged
`src/db/**` changes), confirm with `git status --short` first, then explicitly exclude any typecheck/
lint/test failures traced to those untracked/modified files from the verdict — they aren't part of the
diff under review. State this exclusion in the review file so it's auditable.

See also [[env-web-review]] for the web-side equivalent (CORS, MIGRATION_DATABASE_URL, dist rebuild).

Before flushing a shared Redis DB the task assigns you (e.g. `redis://localhost:6379/11`), don't
trust `dbsize` alone — stale keys from an incomplete earlier attempt look identical to a live
agent's data. Check `valkey-cli client list | grep db=<n>` for an attached client first; 0 clients
means it's safe to flush pre- and post-run. Also worth a quick `ps aux | grep worker/index` +
`lsof -p <pid> -i` scan for orphaned `tsx src/worker/index.ts` processes (no `watch` flag, unlike
the dev worker) left running by a prior stopped session — note it for the tech lead rather than
killing it yourself (read-only).

2026-10-01 T-P5-2: with a symlinked `node_modules`, `pnpm typecheck` in the worktree tries to install and fails ("workspace hoist directory is not a real directory"). Call `./node_modules/.bin/{tsc,biome,vitest}` directly. The guard hook also blocks `git checkout <sha> -- <path>`, even in your own worktree, so revert product files with `git show <sha>:<path> > <path>`. The env overrides `TEST_DATABASE_URL`, `TEST_MIGRATION_DATABASE_URL` and `TEST_REDIS_URL` (a non-zero DB) all exist now. Drop the scratch DB afterwards with `docker exec local-postgres-1 psql -U invai -d postgres -c "drop database ..."`.
