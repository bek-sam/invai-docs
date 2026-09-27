# Review of T-18-3 (round 1)

- Reviewer: backend-foundation on claude-sonnet-5
- Author: backend-engineer (market) on claude-opus-5-5
- Verdict: approve

Scope of this co-review (per the card and `wave.md` grants): migration `0027_market_signals`, the
new tables in `src/db/schema/market.ts`, the one-line grants (`src/db/schema/index.ts`,
`src/api/router.ts`, `src/modules/jobs.ts`), the `src/db/rls-coverage.test.ts` hunk (joint with
security), and the job/idempotency patterns in `src/modules/market/jobs.ts`. I did not re-review
the pure signal engine, rules or feedback logic — `reviewer` and `security-reviewer` already
covered correctness and tenancy there in their round-1 files.

## Evidence I re-ran
Own worktree `../invai-backend-t183-bf` at `72e3e59` (symlinked `node_modules`, ran
`node_modules/.bin/*` directly), own DB `invai_t18_bf` / test DB `invai_t18_bf_test`, Redis DB 8.
All dropped/flushed and the worktree removed at the end.

| Command | Result |
|---|---|
| `tsx src/db/migrate.ts` against a freshly `createdb`'d `invai_t18_bf` | migrated clean from zero to 0027; `\dt market_*` shows exactly the 5 tables |
| `psql \d+` / `pg_policies` on the fresh DB | 4 tenant tables have `<table>_tenant` policy, `FOR ALL`, `USING`/`WITH CHECK` on `company_id`; `market_series_cache` has `market_series_cache_public_read`, `FOR SELECT` only |
| `has_table_privilege('invai_app', 'market_series_cache', 'INSERT'/'UPDATE'/'DELETE'/'SELECT')` | `f, f, f, t` |
| `INSERT INTO market_series_cache ...` as `invai_app` | `ERROR: permission denied for table market_series_cache` |
| `drizzle-kit check` | "Everything's fine" — journal/snapshot consistent, no drift |
| `git show 9dfb0c3 -- drizzle/meta/_journal.json` | one clean append, `idx: 27`, no edits to earlier entries |
| `vitest run src/modules/market src/db/rls-coverage.test.ts src/db/*.test.ts` (own test DB, Redis DB 8) | 8 test files passed, 1 failed (`market.acceptance.test.ts`, QA-owned); 98 passed / 6 failed / 2 skipped total |
| `vitest run src/modules/market/service.test.ts -t "refreshDemand stores only taxonomy queries"` | 1 passed (the round-2 S-34 fix, `72e3e59`) |
| `tsc --noEmit -p .` | 1 pre-existing error, in `src/modules/ai/service.ts` (T-18-4's file, not touched by any T-18-3 commit; confirmed by `git log --oneline -- src/modules/ai/service.ts` showing only T-18-4 commits) |
| Read `drizzle/0027_market_signals.sql` in full | pure `CREATE TABLE`/`ENABLE ROW LEVEL SECURITY`/`CREATE POLICY`/`REVOKE` — no `ALTER` of an existing table, so no rewrite/lock risk; the hand-appended `REVOKE INSERT, UPDATE, DELETE ON market_series_cache FROM invai_app` matches the existing precedent in `drizzle/0013_carriers_webhook_events.sql` (`carrier_webhook_events`) |
| Diffed the 4 commits + `1b57f13`'s `src/db/schema/ai.ts` hunk | exactly the paths the card and wave.md grants list; nothing extra |

## Acceptance criteria (this review's lens: AC1 tables/migration/grants, AC2 jobs)
| # | Met? | Evidence |
|---|---|---|
| 1 Tables, RLS, global cache, migration safety | yes | 4 tenant tables: `company_id` via `companyId()`, `tenantPolicy(...)` + `.enableRLS()` in the same migration, every index leads with `company_id` (`uniqueIndex().on(t.companyId, ...)`, `index().on(t.companyId, ...)`). `market_series_cache`: no `company_id` column, `publicReadPolicy`, `REVOKE` for the app role — matches ADR 0015 and the `trademark_marks`/`carrier_webhook_events` precedents. Migration is pure expand (new tables only, no `ALTER` on existing large tables), so no `lock_timeout`/`CONCURRENTLY` need applies. Journal append is clean (one entry, `idx: 27`, nothing rewritten). `drizzle-kit check` and a from-zero migrate both confirm no drift |
| 2 Jobs: stable ids, schedulers self-register, `withSystem` only where justified | yes | Every `defineJob`'s `jobId` is derived from stable business identity (`companyId` + local day, or `+ sorted designIds` for a design-scoped run) — no random or attempt-numbered ids. `scheduleMarketJobs()` self-registers both schedulers at import (`if (!env.isTest) scheduleMarketJobs().catch(...)`), following the `today/jobs.ts` pattern. Every `withSystem` call carries a written reason in a comment: `assertCompany` ("the job has no tenant yet"), the nightly `refreshDemand` (global cache, ADR 0015, repeated at each of its 3 call sites), and `marketSweep` (cross-tenant fan-out that only reads ids then enqueues per-tenant jobs) — no `withSystem` in a request path. `refreshPricing`'s provider call happens outside any transaction (read plan under `withTenant`, call provider, then a second `withTenant` to persist), matching `idempotent-side-effect` |
| Grants (schema/index.ts, api/router.ts, jobs.ts, rls-coverage.test.ts) | yes | `schema/index.ts`: one `export * from "./market";` line. `api/router.ts`: one import line + one `market: marketRouter` key (the minimum needed to register a namespace, not scope creep). `modules/jobs.ts`: one `import "./market/jobs";` line. `rls-coverage.test.ts`: exactly the two authorized edits (`market_series_cache` added to `PUBLIC_READ_TABLES` and to the app-role-cannot-write array), both additive, nothing else in the file touched |
| `1b57f13`'s `src/db/schema/ai.ts` hunk (T-18-4's grant, co-reviewed here) | yes | One line, `"market_niche"`, appended at the end of `CREDIT_KINDS` (an `enumText`-backed text column, not a pg enum, so no migration is needed or generated) — additive, matches convention, comment explains the route still charges `sku_suggestion` until switched |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git show --stat` on all 4 commits: `src/modules/market/**` minus QA's acceptance files, `src/db/schema/market.ts` + its migration + meta, and exactly the granted lines in `src/db/schema/index.ts`, `src/api/router.ts`, `src/modules/jobs.ts`, `src/db/rls-coverage.test.ts`; `1b57f13`'s single-line `ai.ts` hunk is T-18-4's own granted path)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened (the `rls-coverage.test.ts` hunk is additive only; `72e3e59` strengthens an existing assertion, doesn't loosen one; no `.skip`/`.only`/removed assertions in any of the 4 commits' files)
- [x] Tenancy (`withTenant` on all router/service paths; RLS + tenant policy on the 4 tenant tables; the one authorized exception is public-read + write-revoked); idempotency (job ids stable, run-twice behavior verified by the reviewer's and my own re-run of the round-1 evidence — no duplicate rows on the fresh migrate); money in cents (`c2057df` fixes the one place `ProductPrice.price` was double-multiplied); migration is expand-only, no rewrite, journal consistent
- [x] Decisions recorded where needed (ADR 0015 governs the global-cache design; the S-34 gap security-reviewer found in round 1 is now closed by `72e3e59`, which I independently confirmed asserts Set-equality against `CANONICAL_QUERIES`, not mere containment)

## Optional notes (not blocking)
- The `tsc` error in `src/modules/ai/service.ts` at `72e3e59` is outside T-18-3's owned paths and outside every commit I reviewed here (`git log --oneline -- src/modules/ai/service.ts` shows only T-18-4 commits touching it); it's already tracked by T-18-4's own review, not this card's problem.
- The 6 failing `market.acceptance.test.ts` cases I reproduced on my own fresh DB match exactly the set both round-1 reviews already routed to T-18-2 (mock shapes/comparable counts) and QA (dollars-vs-cents fixture bug, ISO-week offset); nothing new, no regression from `c2057df` or `72e3e59`.
- Single-column FKs on `designId` (not the composite `(company_id, id)` form `add-tenant-table` describes) are consistent with the rest of the codebase today (backlog B-30 — composite tenant FKs aren't the convention yet); not a defect specific to this card.
