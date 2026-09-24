# Review of T-1-5 (round 2)

- Reviewer: reviewer on Opus 5.5
- Author: ai-engineer on Sonnet 5
- Verdict: approve

Scope: invai-backend `b8d0471` (2 files, both in `src/db/reference/`), on top of `8becdb5` reviewed in
`T-1-5-reviewer-r1.md`. Clean detached worktree at `b8d0471` (`/tmp/r15b-wt`, `node_modules` symlinked, no
`pnpm install`), own test DBs `invai_test_r15r2`, `invai_test_r15a`, `invai_test_r15b` and `invai_test_r15c`.
The worktree also contains `ed8a300` (T-1-3 r2). That commit isn't part of this review.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git diff --stat 8becdb5 b8d0471 -- src/db/reference src/db/migrate.ts src/db/seed src/modules/ai` | `index.test.ts` +8/-3, `index.ts` +5/-3 (comment only) |
| `tsc --noEmit` | exit 0 |
| `biome check .` | `Checked 197 files in 126ms. No fixes applied.` exit 0 |
| `tsup` | `Build success`, exit 0 |
| `vitest run` on `invai_test_r15r2` | `Test Files 39 passed (39)`, `Tests 228 passed (228)` |
| **Parallel reproduction (the r1 blocker):** 3 simultaneous `vitest run src/db/reference/index.test.ts`, on `invai_test_r15a`, `invai_test_r15b` and `invai_test_r15c` | all 3 exit 0, `Tests 3 passed (3)` each (in r1 the same setup failed both runs) |
| The same with 2 runs in parallel, repeated twice | `r1a=0 r1b=0 r2a=0 r2b=0` |
| Derived scratch name under `NODE_ENV=test` (Node 24) | no `TEST_MIGRATION_DATABASE_URL` → `invai_test_ref`; with `…/invai_test_r15a` → `invai_test_r15a_ref` |
| Leftovers after the runs | `pg_database` has no `%_ref` and no `invai_ref_check` (each run drops only its own) |
| `scan-test-weakening.sh invai-backend 8becdb5` | hits are only in `src/modules/inventory/po-safety.test.ts` (from `ed8a300`, T-1-3 r2, not this card). For T-1-5's files: `removed=0` assertion lines, no skip/only/mock |
| Cleanup | dropped `invai_test_r15r2`, `invai_test_r15a`, `invai_test_r15b`, `invai_test_r15c`; worktree removed; shared dev DB untouched |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. idempotent, tenant-free `ensureReferenceData` at the end of `runMigrations` | Yes | unchanged since r1 (CLI and concurrency evidence in r1); `index.ts` change is comment-only |
| 2. marks are versioned reference data; seed outcome unchanged | Yes | unchanged since r1 |
| 3. empty-DB migrate → "Disney" high risk test | Yes | passes in the full run and in 5 parallel-run invocations; assertions unchanged from r1 (which failed on the parent commit) |

## Blocking findings
none. r1 finding 1 (hard-coded `invai_ref_check`) is fixed: `index.test.ts:30` derives
`<run's test DB>_ref`. `ensureDatabase`, `runMigrations` and the `DROP … WITH (FORCE)` all use that name,
and the parallel reproduction now passes.

## Checks
- [x] Only owned paths changed: both files are in `src/db/reference/**`.
- [x] Nothing outside scope: the advisory lock, mark pruning and `PLAN_CATALOG` move went to the backlog,
  as the tech lead asked.
- [x] Tests exercise the behavior, and none were weakened: the only test change is the scratch-DB name;
  every assertion is unchanged.
- [x] Tenancy, idempotency, money in cents, en/es text: unchanged since r1; no new data paths.
- [x] Decisions recorded where needed: none needed.

## Optional notes (not blocking)
- The rewritten comment on the lazy billing import (`index.ts:24-28`) is now accurate.
- If a run is killed before `afterAll`, `<testdb>_ref` is left behind. The next run reuses it (ensure then
  re-migrate is idempotent), so it's harmless.
- The r1 backlog items still stand: advisory lock in `runMigrations`, pruning old `reference:*` marks,
  `PLAN_CATALOG` in a dependency-free module, and a runbook line saying migrate needs the API's full
  secret set.
