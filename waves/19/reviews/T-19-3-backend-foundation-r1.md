# Review of T-19-3 (round 1)

- Reviewer: backend-foundation on Sonnet 5
- Author: backend-engineer (digest) on Opus
- Verdict: approve

Scope of this co-review (per card and `wave.md` "Grants"): migration `0029_digest`, the 7 new
tables, and the one-line grant registrations in `src/db/schema/index.ts`, `src/api/router.ts`,
`src/modules/jobs.ts`. I did not re-judge detector logic, ranking, templates or Market watch
(reviewer's + architect's scope) except where they touch tenancy/migration/idempotency.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git worktree add ../invai-backend-bf3-t19-3 013f3d6` (backend HEAD), symlinked `node_modules` | clean checkout |
| `createdb invai_t19_bf3` (empty) + `tsx src/db/migrate.ts` against it (`MIGRATION_DATABASE_URL`) | `[migrate] up to date (invai_t19_bf3)`; 30 migrations applied from zero, 84 tables, 7 `digest_*` tables present |
| `drizzle-kit check` | `Everything's fine 🐶🔥` (journal hashes/order consistent; 0028 before 0029, `when` 1790562160049 < 1790563857559, per A11) |
| `drizzle-kit generate --name _reviewer_drift_check` (disposable, worktree only) | `No schema changes, nothing to migrate 😴` — proves the committed `0029_digest.sql` matches `schema/digest.ts` exactly, from a DB migrated from zero (stronger than checking the shared dev DB, which had 0029 pre-applied by another agent per the author's note) |
| `vitest run src/modules/digest/digest.test.ts src/modules/digest/market.test.ts src/modules/digest/pure.test.ts src/db` (own DB `invai_t19_bf3`, Redis DB 8; acceptance files excluded) | `Test Files 8 passed (8)`, `Tests 60 passed (60)` — includes `rls-coverage.test.ts`, `rls.test.ts`, `timeouts.test.ts`, `migrate.test.ts`, `reference/index.test.ts` |
| `vitest run src/api/authz.test.ts` | `1 passed`, `7 passed` — confirms the vendor/`me.notifications` fix (`013f3d6`, already at HEAD) is in and green |
| `tsc --noEmit` (whole repo, worktree) | clean |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend origin/main` | hits reviewed below; none blocking for this card's files |

## Acceptance criteria (my scope only)
| # | Met? | Evidence |
|---|---|---|
| Card AC1 tables: company_id + RLS + isolation | yes | All 7 tables (`digest_settings`, `digests`, `digest_insights`, `digest_feedback`, `digest_clicks`, `digest_views`, `digest_deliveries`) have `companyId`, `tenantPolicy(...)`, `.enableRLS()`; `rls-coverage.test.ts` green in my own DB run |
| Composite tenant-scoped FKs (S-26) | yes | `digests`/`digest_insights` carry `unique(company_id, id)`; every child FK is `foreignKey({columns:[companyId, parentId], foreignColumns:[parent.companyId, parent.id]})` (`digest_insights_digest_fk`, `digest_feedback_insight_fk`/`_digest_fk`, `digest_clicks_insight_fk`/`_digest_fk`, `digest_views_digest_fk`, `digest_deliveries_digest_fk`) — no single-column `.references()` to a tenant parent |
| Indexes lead with company_id | yes | Every index in `0029_digest.sql` (`digests_company_id_week_key_index`, `digest_insights_company_id_digest_id_fingerprint_index`, `digest_clicks_company_id_insight_id_user_id_index`, etc.) leads with `company_id`; `digest_settings` uses a plain `company_id`-only unique index (one row per shop), also correct |
| Migration additive, generated, no rewrites | yes | `0029_digest.sql` is 7 `CREATE TABLE` + RLS + FKs (`NOT VALID` not needed, nothing pre-existing altered); `drizzle-kit check` and the drift-check `generate` both confirm it is exactly what `db:generate` would produce today |
| Migration order A11 (0028 before 0029) | yes | Journal `_journal.json`: idx 28 `0028_notifications` `when 1790562160049`, idx 29 `0029_digest` `when 1790563857559`; both `src/db/schema/index.ts` grant lines present and additive (`export * from "./notifications"` then `"./digest"`) |
| Grant lines exactly one line each | yes | `src/db/schema/index.ts`: `export * from "./digest";` (1 line). `src/modules/jobs.ts`: `import "./digest/jobs";` (1 line). `src/api/router.ts`: one import line + one router-map entry `digest: digestRouter,` — the same two-line shape every other module router uses (`grep` shows identical pattern for `market`, `privacy`, etc.); not a deviation |
| Jobs idempotent (`idempotent-job`) | yes | `buildJob` jobId `digest-build-${companyId}-${weekKey}` (unique per shop+week, backed by `digests`'s unique `(company_id, week_key)` index + `FOR UPDATE SKIP LOCKED` in `build.ts`); `deliverJob` jobId `digest-deliver-${digestId}` (backed by `digest_deliveries` unique `(company_id, digest_id, user_id, channel)` + the pending/settled row guard); both have `backoff: {type:"exponential", jitter:0.5}` |
| `withSystem` only in due-shop sweep and purge, with a reason | yes | `grep -n withSystem src/modules/digest/*.ts` (non-test files): only `jobs.ts:35` (`dueShops`, comment "the sweep has no tenant yet... the documented exception") and `jobs.ts:146` (`purgeJob`, comment "Cross-tenant retention delete by age only"). No `withSystem` in `build.ts`, `deliver.ts`, `router.ts`, `service.ts` |
| Heavy work in jobs, sends outside DB transactions | yes | `deliver.ts` `deliverDigest`: Tx1 records `pending`/`skipped` intent, `sendUserEmail(...)` called with no open `withTenant`/transaction around it, Tx2 settles `sent`/`failed` — the three-transaction pattern (`idempotent-side-effect`) |
| A7 (email_sends owns send idempotency; digest_deliveries is per-recipient outcome) | yes | `src/db/schema/notifications.ts` `email_sends` (0028) is the durable send-dedupe table; `digest_deliveries` (0029) has no independent send-idempotency key, only the delivery outcome row per (digest, user, channel), matching the schema comment at `digest.ts:240-244` |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git show --stat` on `cadc338`/`bef6158`): `src/modules/digest/**`, `src/db/schema/digest.ts`, `drizzle/0029_digest.sql` + its `meta/`, and exactly the three granted one-line registrations. No other file touched.
- [x] Nothing outside scope for my co-review area (migration/tables/grants); detector/ranking/template/Market-watch content not re-judged here.
- [x] Tests exercise the behavior, and none were weakened for this card's files: scan script hit `vi.mock("../market/service", ...)` in `market.test.ts` (mocks a collaborator to test the "throwing market read" fault path, not the unit under test — legitimate) and `if (!env.isTest)` self-registration in `jobs.ts:184` (identical pattern already used by all 10 other job modules, `grep -rn "env.isTest" src/modules/*/jobs.ts`) and `i.recommendation?.mock` in `render.ts:356` (real product logic for the sample badge on mock market items, not a test shortcut — flagged only because of the word "mock"). None are blocking.
- [x] Tenancy (`withTenant`, RLS on new tables), idempotency, money in cents, en/es text — verified above; money fields are `integer` cents (`impactCents`), templates render en/es (out of my direct scope but no cents/i18n violation seen in the schema or job code).
- [x] Decisions recorded where needed — none needed beyond what's already in `wave.md` Grants/A7/A11, which this migration and these tables follow.

## Optional notes (not blocking)
1. `purgeJob` (`jobs.ts:146`) does an unbounded `delete from digests where week_start < ...` relying on cascade to remove insights/feedback/clicks/views/deliveries in one statement. Fine at current volume (nightly, nothing else in the digest tables approaches migration-sized row counts yet), but if a shop's history grows large this could hold locks longer than the app role's `lock_timeout`. Not a migration concern (no schema change), so not blocking here — worth a scale note if `digests` ever gets into the millions of rows.
2. `deliverDigest` (`deliver.ts`, end of the `for (const r of prep.todo)` loop) throws on the first `failed` recipient, which stops that invocation's loop for any remaining recipients until the job retries. Recovery is complete (the `existing.find(...).status !== "pending" && !== "failed"` guard on the next attempt still emails everyone not yet settled), just delayed by the job's backoff. Not a tenancy/idempotency/migration issue, so outside my blocking scope — noting for the primary reviewer/author's awareness only.
3. The author's report's "Blocked by other owners" item (`authz.test.ts:129` vendor/`me.notifications`) is already resolved at HEAD (`013f3d6`); I confirmed it passes standalone. No action needed from this review.

## Cleanup
- Worktree `../invai-backend-bf3-t19-3` removed (`git worktree remove --force`); confirmed gone from `git worktree list` (only the pre-existing `invai-backend-sec4-r2`, not mine, remains).
- Test DB `invai_t19_bf3` dropped. Redis DB 8 flushed. No processes started (no dev server run; only short-lived `tsx`/`vitest`/`drizzle-kit` invocations).
- Shared dev DB and shared `invai-backend` tree untouched by this review.
