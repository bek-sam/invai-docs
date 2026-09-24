# Review of T-1-5 (round 2)

- Reviewer: backend-foundation (co-review, risk flag `migration`: migrations tooling) on Opus 5.5
- Author: ai-engineer on Sonnet 5
- Verdict: approve

Scope: invai-backend `b8d0471` (`src/db/reference/index.test.ts`, `src/db/reference/index.ts`). Same evidence
run as `T-1-5-reviewer-r2.md`: clean worktree at `b8d0471`, `node_modules` symlinked, own test DBs, all dropped
afterwards.

## Evidence I re-ran
| Command | Result |
|---|---|
| `tsc --noEmit` / `biome check .` / `tsup` at `b8d0471` | exit 0 / `No fixes applied.` / `Build success` |
| `vitest run` on `invai_test_r15r2` | `Test Files 39 passed (39)`, `Tests 228 passed (228)` |
| r1 reproduction: parallel `vitest run src/db/reference/index.test.ts` on separate test DBs | 3-way: 3/3 exit 0; 2-way × 2: 4/4 exit 0 (r1: both runs failed) |
| Derived name (`NODE_ENV=test`, Node 24) | default → `invai_test_ref`; `TEST_MIGRATION_DATABASE_URL=…/invai_test_r15a` → `invai_test_r15a_ref` |
| `pg_database` after runs | no `%_ref`, no `invai_ref_check` |
| `scan-test-weakening.sh invai-backend 8becdb5` | no hits in T-1-5 files (hits only in T-1-3's `po-safety.test.ts`) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. | Yes | unchanged since r1; `index.ts` diff is a comment only |
| 2. | Yes | unchanged since r1 |
| 3. | Yes | test passes serially and in parallel; assertions unchanged |

## Blocking findings
none. The r1 finding is fixed. The scratch DB now follows the run's own `TEST_MIGRATION_DATABASE_URL`, which
restores the per-agent test-DB isolation that `env.ts` and `src/test/**` provide. `CREATE EXTENSION` and
`DROP … WITH (FORCE)` now only ever touch that run's own database (`pg_extension` is per-database, so separate
scratch DBs can't race each other). The 63-byte identifier limit leaves plenty of room for `<testdb>_ref`.

## Checks
- [x] Only owned paths changed (`src/db/reference/**`)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened
- [x] Tenancy / idempotency: unchanged since r1 (no tenant rows, race-safe upserts on existing unique keys)
- [x] Decisions: none needed

## Optional notes (not blocking)
- The corrected comment (`index.ts:24-28`) matches what the code does: only the import is deferred, and
  running migrate still needs the full env.
- My follow-ups from r1 are still open for the backlog: `pg_advisory_lock` around `runMigrations`
  (concurrent `CREATE EXTENSION` and drizzle's lock-free `migrate()`), pruning old `reference:*` marks,
  `modules/billing/catalog.ts`, and a runbook note that the migrate task needs the API's secret set.
