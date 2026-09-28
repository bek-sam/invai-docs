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

See also [[env-web-review]] for the web-side equivalent (CORS, MIGRATION_DATABASE_URL, dist rebuild).
