# T-A9 co-review (backend-foundation, round 1) — migration/schema/job only

Reviewer: backend-foundation (sonnet). Author: backend-engineer (opus). Commit: `invai-backend` `522433b`.
Verdict: **approve**

## Scope of this review
Migration `drizzle/0038_today_actions.sql`, `drizzle/meta/_journal.json`, `src/db/schema/digest.ts` (today tables), `src/modules/today/jobs.ts`. Card: `T-A9-digest-today-backend.md`. Ruling: `reviews/plan-architect.md` ruling 2.

## Evidence I re-ran
- `pnpm typecheck` → clean (`tsc --noEmit`, no output).
- `REDIS_URL=redis://localhost:6379/14 pnpm test src/db` → 11 files, 33 passed (RLS coverage + FK coverage included; `invai_test` is migrated fresh by `global-setup.ts`, so this is the scratch-DB apply check).
- `REDIS_URL=redis://localhost:6379/14 pnpm test src/modules/today src/modules/digest` → 11 files, 113 passed, 2 skipped, 1 todo.
- Killed leftover vitest/vite child processes (known 5.0 teardown quirk) after each run; no DB/Redis left running by me.

## Checklist
- **Generated, not hand-edited**: `_journal.json` idx 38 chains after 0037 with a fresh `when` timestamp; SQL shape (statement-breakpoints, `gen_random_uuid()` defaults, policy/FK ordering) matches drizzle-kit's own output style. Matches `schema/digest.ts` 1:1 (3 tables, 3 unique indexes, 2 FKs on `today_actions`/`today_action_clicks`, 1 on each `company_id`→`companies`).
- **Tables have `company_id`, RLS, tenant policy**: yes, all three (`today_action_sets`, `today_actions`, `today_action_clicks`); `ENABLE ROW LEVEL SECURITY` + `CREATE POLICY ..._tenant ... TO invai_app` for each, same shape as every other tenant table.
- **Composite tenant FKs (S-26)**: `today_action_sets`/`today_actions` each carry `UNIQUE(company_id, id)`; `today_actions.set_fk` → `(company_id, set_id)`→`today_action_sets(company_id, id)`; `today_action_clicks.action_fk` → `(company_id, action_id)`→`today_actions(company_id, id)`. This matches the established `digest_clicks`→`digest_insights` pattern, not ruling 2's literal "FK by (date, key)" text — a reasonable, documented deviation (report "Decisions"; schema.ts comment cites the ruling) that keeps the S-26 convention consistent rather than introducing a second FK style.
- **Unique keys**: `today_action_sets(company_id, date)`, `today_actions(company_id, date, key)` — both match ruling 2. `today_action_clicks(company_id, action_id, user_id)` — functionally equivalent to ruling 2's `(company_id, date, key, user_id)` since `action_id` already keys to one `(date, key)` row; first-click-wins semantics preserved (`onConflictDoNothing`, confirmed in `actions.ts` and `actions.test.ts`).
- **Indexes for the read and purge**: `uniqueIndex(company_id, date)` on sets serves the read; `index(company_id, set_id)` on actions serves the join; purge deletes from `today_action_sets` by `date` with cascade to children — no index needed on a 90-day-bounded nightly sweep over one small table, and the sweep's own lookup (`shopsMissingToday`) is a `not exists` against the `(company_id, date)` unique index.
- **No table-rewriting DDL / lock risk**: migration only creates 3 new tables + their own indexes/FKs; no `ALTER` on any existing table. No `lock_timeout` guard needed (new-table precedent, same as 0026–0029/0033).
- **Job pattern**: `buildTodayActionsJob` jobId `today-actions-${companyId}-${date}` (stable, no `:`), DB-level idempotency is the `(company_id, date)` unique insert (`onConflictDoNothing`) — jobId is the first filter, the set row is the guarantee, per `idempotent-job`. Rebuild (`force`) does delete+insert of `today_actions` inside the same `withTenant` transaction. `sweepTodayActions`/`purgeTodayActions` use `withSystem` for the cross-tenant list/delete, each with a written reason comment ("withSystem: the sweep/nightly delete has no tenant"), matching the rule. Backoff has jitter (`{type:"exponential", delay:60_000, jitter:0.5}`). Retention constant (90 days) matches `DIGEST_CONFIG.today.retentionDays`.

## Findings
None blocking.

## Optional notes
- `today_action_clicks` stores redundant `date`/`key` alongside `action_id` (denormalized convenience for the click input shape); harmless, not a schema risk.

## Not reviewed (outside this co-review's scope)
Detector logic (`digest/track-e.ts`, `detectors.ts`), router/permission wiring, i18n copy, `analytics/finance-service.ts` tie-break — left to the primary reviewer and security-reviewer.
