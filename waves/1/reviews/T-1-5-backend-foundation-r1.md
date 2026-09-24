# Review of T-1-5 (round 1)

- Reviewer: backend-foundation (co-review, risk flag `migration`: migrations tooling) on Opus 5.5
- Author: ai-engineer on Sonnet 5
- Verdict: changes-required

Scope: invai-backend `8becdb5` only, with a focus on `src/db/migrate.ts`, `src/db/reference/**` and the test
harness. The same evidence run as `T-1-5-reviewer-r1.md` (clean worktree at `8becdb5`, own test DB
`invai_test_r15`, all scratch DBs dropped afterwards).

## Evidence I re-ran
| Command | Result |
|---|---|
| `tsc --noEmit` / `biome check .` / `tsup` at `8becdb5` | exit 0 / `Checked 197 files … No fixes applied.` / `Build success` |
| `vitest run` with `TEST_DATABASE_URL`/`TEST_MIGRATION_DATABASE_URL` → `invai_test_r15` | `Test Files 39 passed (39)`, `Tests 226 passed (226)` |
| `src/db/reference/index.test.ts` on the parent commit | 3/3 fail (`expected +0 to be 5`, `… 'low' to be 'high'`) |
| `tsx src/db/migrate.ts` on empty `invai_r15_cli` | `[migrate] up to date`, exit 0, 0.73 s; marks 471, plans 5, companies 0, users 0 |
| drizzle-orm 0.45.3 `pg-core/dialect.js` `PgDialect.migrate` | journal table DDL, `select … order by created_at`, `sql.raw(stmt)` per statement, insert into `drizzle.__drizzle_migrations` via `sql.identifier`. No Column objects, so `casing` has no effect |
| Re-migrate after hand edits | `starter` 19900 → 14900; `disney` `dead` → `live`; unknown row `zzremoved` kept |
| 4 concurrent migrates (migrated DB); 3 × 5 concurrent migrates with `plans`/`trademark_marks` emptied first | 19/19 exit 0; final 471 marks / 5 plans each round |
| 3 concurrent migrates on a brand-new DB | 2 fail at `CREATE EXTENSION` (pre-existing, before the new code) |
| 2 parallel runs of `reference/index.test.ts`, separate test DBs | both fail (shared `invai_ref_check`), see finding 1 |
| `scan-test-weakening.sh invai-backend 8becdb5^` | no hits |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. idempotent, tenant-free upsert at the end of `runMigrations` | Yes | CLI and concurrency runs above; `migrate.ts:36-37` |
| 2. marks are versioned reference data; seed unchanged in outcome | Yes (inspection) | rename + `REFERENCE_DATA_VERSION` in `source`; the seed reads no marks; full seed not re-run |
| 3. empty DB → "Disney" high risk test | Yes | passes at `8becdb5`, fails on the parent |

## Blocking findings
1. `src/db/reference/index.test.ts:18` (`:32`, `:44`): the hard-coded scratch DB `invai_ref_check` breaks the
   per-agent test-DB isolation that `src/test/**` and `env.ts` (`TEST_*_DATABASE_URL`) exist to provide.
   Two concurrent `pnpm test` runs on the local server (the normal state during a wave) share it. One
   `DROP DATABASE … WITH (FORCE)` kills the other's connections, and both race `CREATE EXTENSION`.
   Reproduced: both parallel runs failed. CI is safe (one job, superuser `invai`, pg17 supports
   `WITH (FORCE)`). The fix is one line: name it after the run's test DB (for example `<testdb>_ref`) or add
   a random suffix.

## Checks
- [x] Only owned paths changed: yes, with justified follow-ons (see the reviewer file). The `casing` change in
  `migrate.ts` is needed and inert for migrations.
- [x] Nothing outside scope.
- [ ] Tests exercise the behavior, none weakened. The behavior is covered and fails without the change. The
  `seedMarks()` removal is not a weakening (assertions intact; the precondition now comes from the real
  migrate path; `fixtures.ts:35` never truncates `trademark_marks`). Unticked only for finding 1.
- [x] Tenancy/idempotency: no tenant table or row. Upsert targets exist: `plans.key` PK, and the unique index
  on `trademark_marks (normalized, kind)` from `schema/ai.ts:146`. Dataset keys are unique (471/471), so the
  multi-row `ON CONFLICT DO UPDATE` is safe. Both tables stay public-read with no app-role writes
  (`rls-coverage.test.ts` green).
- [x] Decisions: none needed.

## Migration tooling assessment (the questions asked of this co-review)
- **`casing: "snake_case"` on the migrate handle:** it does not change how any existing migration runs.
  Confirmed in drizzle 0.45.3 source: `migrate()` builds its SQL only with `sql.identifier`/`sql.raw`, and
  casing applies only to schema Column names. Hash and `created_at` bookkeeping are unchanged.
- **Concurrent deploys:** the new upsert is race-safe (19 concurrent runs, including on empty tables, all
  succeeded). Rows are inserted in the same array order, so lock order is consistent and there's no deadlock.
  The remaining races are pre-existing in `runMigrations`: `CREATE EXTENSION` and drizzle's lock-free
  `migrate()`. Recommend a `pg_advisory_lock` around the whole of `runMigrations` before any multi-task
  deploy runs migrate (my follow-up, not this card).
- **Operator hand edits:** plan rows and mark `status`/`owner`/`classes` are overwritten on every deploy.
  For plans that was already the behavior (billing's `ensurePlanCatalog` does it once per API process), so
  code stays the source of truth. Acceptable; document it in the runbook.
- **Removed marks:** never deleted. A mark taken off the list keeps flagging in production. Non-blocking now
  (the card asks for an upsert); follow-up: prune `source like 'reference:%'` rows that aren't the current
  version.
- **Lazy billing import in the migrate path:** acceptable, not a new deploy trap. The CLI already imported
  `env` before this commit (`migrate.ts:44-45`), so production migrate already needed every production key
  (T-1-1 guard) or `ALLOW_MOCKS=true`. What the import newly drags in: `db/client` (two pools on the
  *global* env URLs, never connected, so the process still exits cleanly), `lib/log`, oRPC and contracts.
  It also makes programmatic `runMigrations(url)` depend on a valid env. The comment's claim ("importable
  without … env") is true only until the function runs. Record in the runbook that the migrate task gets
  the API's full secret set. Better, later: move `PLAN_CATALOG` into a dependency-free
  `modules/billing/catalog.ts` and import it statically.

## Optional notes (not blocking)
- An `IS DISTINCT FROM` guard on both upserts would make repeat deploys true no-ops (no `updated_at` bump, no
  471 dead tuples per deploy).
- `ensureReferenceData` isn't in the migrator's transaction. A failure after migrations commit is fixed by
  re-running migrate. Fine.
- `src/modules/README.md` could mention `src/db/reference` as the home for global reference data (my file;
  I'll pick it up).
