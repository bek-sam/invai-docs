# T-P1-1: Per-run test DB and Redis DB; market retry test on fake timers

| Field | Value |
|---|---|
| Wave | P1 |
| Scope ref | `always-in-scope: bug` (reliability; lesson 2026-09-30, third `invai_test` collision) |
| Spec | backlog B-228, B-215 (absorbed), B-229 part 1 |
| Owner | backend-foundation |
| Reviewer | reviewer (opus) |
| Co-reviewers | none (test infra; no migration, no product code) |
| Risk flags | test infra |
| Model | sonnet |

## Owned paths (edit)
- `invai-backend/src/test/**` (`global-setup.ts`, `db-safety.ts` (+ test), `fixtures.ts` only where it reads the test URLs), `invai-backend/vitest.config.ts`, `invai-backend/package.json` (test scripts only), `invai-backend/src/env.ts` (test-URL logic only), `invai-backend/README.md` (testing section)
- Grant: `invai-backend/src/integrations/market/http.test.ts` (test file only)

## Read-only paths
- Everything else in `invai-backend`, `invai-infra/**` (gate scripts, CI), all other repos.

## Acceptance criteria
1. With neither `TEST_DATABASE_URL` nor `TEST_MIGRATION_DATABASE_URL` set, a `vitest` run creates its own DB `invai_test_<pid>` from a migrated template `invai_test_tpl` (template migrated under a Postgres advisory lock, so two runs starting together don't race), points every worker at it, and drops it at teardown. Every worker process sees the same URL (verify the propagation mechanism in the installed Vitest 5 `globalSetup`/`provide` API, not from memory).
2. With `REDIS_URL` unset, the run claims a free Redis DB in 1–14 with a lock key (`SET NX` + TTL, refreshed or long enough for a full suite) and releases it at teardown; DB 0 (dev) and 15 are never picked. If all are taken, it fails with a clear message.
3. Explicit `TEST_DATABASE_URL` / `TEST_MIGRATION_DATABASE_URL` / `REDIS_URL` still win, unchanged (the gate and CI rely on this).
4. Stale per-run DBs from crashed runs (`invai_test_<pid>` whose pid isn't alive on this host and older than 1 hour) are dropped at the next setup; the template and anything not matching the pattern is never touched.
5. B-215: the test-DB guard compares the decoded DB name (`%69nvai` is refused), and the dev DB `invai` is always refused.
6. B-229 part 1: `market/http.test.ts` "gives up after exhausting retries on a persistent 500" uses fake timers (or an injected sleep), runs in under 1 s and still asserts the retry count and the give-up error. No assertion is removed or loosened.
7. **Two full `pnpm test` runs started at the same moment in two shells both pass**, each on its own DB and Redis DB, and leave no `invai_test_<pid>` DB behind.
8. `team/agent-brief.md`'s "pin your own DB" rule can be retired: say in the report exactly what the tech lead should write instead (the tech lead edits that file).

## Verification
- `cd invai-backend && pnpm typecheck && pnpm lint 2>&1 | tail -n 20`
- Two parallel plain runs: `pnpm test --reporter=dot > /tmp/p1a.log 2>&1 &` and the same to `/tmp/p1b.log` (background), then `tail -n 15` each; then `docker exec local-postgres-1 psql -U invai -Atc "select datname from pg_database where datname like 'invai_test%'"` shows only the template (and `invai_test` if it pre-existed).
- One run with explicit `TEST_DATABASE_URL=...invai_p11_test` and `REDIS_URL=redis://localhost:6379/9` uses exactly those.
- `pnpm test src/integrations/market/http.test.ts --reporter=dot` timing.

## Out of scope
- Gate scripts and CI (`invai-infra`); B-227 (backlog). Any product code.

## Budget
- About 2 hours. Stop and tell the tech lead if blocked for 30 minutes.

Commit only your paths (`git add <paths>`). Don't push. Report: `invai-docs/waves/P1/reports/T-P1-1.md`.
