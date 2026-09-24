# Review of T-1-5 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: ai-engineer on Sonnet 5
- Verdict: changes-required

Scope of review: invai-backend commit `8becdb5` only (7 files), checked out as a clean detached worktree at
`8becdb5` (`/tmp/r15-wt`, node_modules symlinked, removed afterwards). Own test DB `invai_test_r15`.

## Evidence I re-ran
| Command | Result |
|---|---|
| `tsc --noEmit` (worktree at `8becdb5`) | exit 0, no errors |
| `biome check .` | `Checked 197 files in 120ms. No fixes applied.` exit 0 |
| `tsup` (build) | `dist/server.js 66.66 KB` … `Build success`, exit 0 |
| `TEST_DATABASE_URL=…/invai_test_r15 TEST_MIGRATION_DATABASE_URL=…/invai_test_r15 vitest run` | `[reset] created database invai_test_r15` · `Test Files 39 passed (39)` · `Tests 226 passed (226)` |
| New test against the parent commit (`git archive 8becdb5^` + `src/db/reference/index.test.ts` only) | all 3 fail: `expected +0 to be 5`, `expected 0 to be greater than 200`, `expected 'low' to be 'high'`. The test is real proof. |
| Empty scratch DB `invai_r15_cli`, `MIGRATION_DATABASE_URL=…/invai_r15_cli tsx src/db/migrate.ts` | `[migrate] up to date (invai_r15_cli)`, exit 0, 0.73 s total (the process exits; no pools left open by the lazy billing import) |
| Counts on `invai_r15_cli` | `trademark_marks`=471, `plans`=5, `companies`=0, `users`=0, 1 distinct `source` (`reference:2026-09-24.1`), `disney` → `DISNEY|Disney Enterprises` |
| Hand-edit then re-migrate: `starter` price → 19900, `disney` status → `dead`, extra row `zzremoved` | after migrate: price back to 14900, status back to `live`, `zzremoved` still present (1 row) |
| 4 concurrent `db:migrate` on the migrated DB | all exit 0, all `up to date` |
| 3 rounds × 5 concurrent `db:migrate` after `delete from trademark_marks; delete from plans` (races the upsert on empty tables) | all 15 exit 0; 471 marks, 5 plans |
| 3 concurrent `db:migrate` on a brand-new empty DB | 1 ok, 2 fail at `CREATE EXTENSION` (`pg_extension_name_index` duplicate). Pre-existing in `runMigrations`, before the code this commit adds; not introduced here |
| Dataset duplicates: `(normalizeMark(mark), kind)` over `TRADEMARK_MARKS` | 471 keys, 471 distinct (a multi-row `ON CONFLICT DO UPDATE` cannot hit the "affect row a second time" error) |
| Two parallel `vitest run src/db/reference/index.test.ts`, each with its own test DB | **both fail**: run 1 `database "invai_ref_check" does not exist` (dropped under it), run 2 `duplicate key … pg_extension_name_index`. See blocking finding 1 |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend 8becdb5^` | `removed=0 added=7`, `Result: no hits` |
| drizzle 0.45.3 `pg-core/dialect.js` `migrate()` read | uses only `sql.identifier` / `sql.raw`; `casing` touches only schema Column names, so `casing: "snake_case"` cannot change how any migration runs |
| Cleanup | dropped `invai_r15_cli`, `invai_r15_race`, `invai_test_r15`, `invai_test_r15b`; `invai_ref_check` absent; worktree and `/tmp` dirs removed. Shared dev DB untouched |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. `ensureReferenceData(db)` upserts marks + plan catalog, idempotent, no tenants, safe every deploy, runs at the end of `runMigrations` | Yes | CLI migrate on empty DB: 471 marks, 5 plans, 0 companies, 0 users. Re-run and 5-way concurrent runs all exit 0 with the same counts. Called at `src/db/migrate.ts:37` after `migrate()` |
| 2. Marks move to versioned reference data; seed still produces the same demo results | Yes (by inspection) | `seed/trademarks.ts` renamed to `reference/trademarks.ts` (+4 comment lines), `REFERENCE_DATA_VERSION` in `source`. The seed reads no trademark data elsewhere (`git grep -i trademark src/db/seed` → only the new comment), and every documented flow runs `db:migrate` before `db:seed`. I did not re-run the 15–20 min full seed |
| 3. Test: migrate an empty DB, "Disney" check comes back high | Yes | `src/db/reference/index.test.ts` passes at `8becdb5`, fails on the parent (see evidence) |

## Blocking findings
1. `src/db/reference/index.test.ts:18` (with `:32`, `:44`) — the scratch database name is hard-coded
   (`invai_ref_check`), not derived from the run's own test DB. So two `pnpm test` runs on the same Postgres
   share it. One run's `afterAll` does `DROP DATABASE … WITH (FORCE)` under the other, and both race
   `CREATE EXTENSION`. Reproduced: two parallel runs, each on its own test DB, **both failed**
   (`database "invai_ref_check" does not exist` / `duplicate key … pg_extension_name_index`). The team runs
   author, reviewers and other cards' agents at the same time on the local server, each on its own
   `invai_test_*` DB, and this is how every card is verified. So this new test makes any concurrent
   `pnpm test` in the workspace fail at random. CI (one job per service container) is safe. Fix: derive the
   name from the run's test DB (for example `${new URL(env.MIGRATION_DATABASE_URL).pathname.slice(1)}_ref`)
   or add a random suffix. Keep the `DROP … WITH (FORCE)` scoped to that name.

## Checks
- [x] Only owned paths changed (`git diff --stat`): 5 of 7 files are on the card. `seed/trademarks.ts` (deleted
  by rename) is what the owned `seed/index.ts` imported, and moving it is the card's intent.
  `modules/ai/service.test.ts` and `modules/ai/trademark.ts` (comment only) are ai-engineer's own role paths
  and were forced by the move. `migrate.ts` got the `casing` change beyond "only the call", but the call
  needs it (`serialNo` → `serial_no`), and it is harmless to migrations (see evidence). Accepted, not blocking.
- [x] Nothing outside scope: no USPTO loader, no B-46 work.
- [ ] Tests exercise the behavior, and none were weakened. The behavior is tested, and the test fails without
  the change. The scan found no hits. Removing `seedMarks()` from `ai/service.test.ts` is **not** a weakening:
  its assertions (`riskLevel "high"`, `JUST DO IT`, `NIKE` matches) are unchanged and still depend on the
  marks. Those marks now come from the real migrate path in the global setup. `fixtures.ts` never truncates
  `trademark_marks`, and nothing else deletes from it. Unticked only because of blocking finding 1
  (test-harness isolation).
- [x] Tenancy, idempotency, money in cents, en/es text: no tenant tables, no tenant rows created (asserted and
  checked). Upserts are keyed on `plans.key` (PK) and `(normalized, kind)` (unique index), so a replay changes
  nothing. Prices are integer cents from `PLAN_CATALOG`. No user-facing text. No `withSystem` added; the
  owner handle is the migrator's own pool.
- [x] Decisions recorded where needed: none needed. The plan-overwrite semantics already exist in
  `billing/service.ts` `ensurePlanCatalog()`.

## Optional notes (not blocking)
- **Lazy billing import (`reference/index.ts:27`): not a deploy trap today, but the stated reason is wrong.**
  The `db:migrate` CLI already did `await import("../env")` (`migrate.ts:44-45`) before this commit. So in
  production, migrate already needs the full env, including T-1-1's production-key guard (or
  `ALLOW_MOCKS=true`). The billing import adds no new requirement to the CLI. What changes: programmatic
  `runMigrations(url)` now needs a valid env too, and the import pulls `db/client` (two lazy `pg` pools on the
  *global* URLs, never connected; the CLI still exits in 0.7 s), `@invai/contracts` and oRPC into the
  migrate path. The lazy import does not keep migrate free of env; it only delays the import. The plan
  should say this: a migrate task (none exists in `sst.config.ts` yet) must get the same secrets as the
  API. Cleaner later: move `PLAN_CATALOG` to a pure `billing/catalog.ts`.
- **Hand edits are overwritten on every deploy:** plan prices and limits (already true once per API process
  via billing's `ensurePlanCatalog`, so code is the source of truth) and trademark `status`/`owner`/`classes`
  (a mark set to `dead` by hand goes back to `live`). Fine while the dataset is code-owned; say it in the
  runbook.
- **Removed marks are never deleted:** a mark taken off the list, or one whose `kind` changes, stays in
  production and keeps flagging (verified: `zzremoved` survived). Suggest a follow-up: after the upsert,
  delete rows where `source like 'reference:%' and source <> 'reference:<current>'`. Rows from the future
  USPTO loader would be spared.
- Every deploy bumps `plans.updated_at` and rewrites all 471 mark rows (dead tuples, brief row locks). Readers
  aren't blocked. An `IS DISTINCT FROM` `where` on the update would make a real no-op cheap.
- `ensureReferenceData` runs outside the migrator's transaction. If it fails after migrations commit, the
  CLI exits non-zero and a re-run fixes it. Acceptable.
- Concurrent migrate on a brand-new DB fails at `CREATE EXTENSION`, and drizzle's `migrate()` has no
  advisory lock. Both are pre-existing. Worth a `pg_advisory_lock` in `runMigrations` before a real deploy
  pipeline runs migrate from more than one task (backend-foundation / platform-sre follow-up).
