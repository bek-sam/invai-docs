# Report: T-1-5 A fresh production database has its reference data
Author: ai-engineer on Sonnet 5

Card: T-1-5  Owner: ai-engineer  Scope ref: `product/scope.md#mvp-in` item 11 (bug), backlog B-54
Owned (edit): `invai-backend/src/db/reference/**` (new), `invai-backend/src/db/migrate.ts` (only the
`ensureReferenceData` call), `invai-backend/src/db/seed/index.ts` (only stop inserting trademark
marks), tests next to these files.
Read-only: everything else (`modules/billing/service.ts` for `PLAN_CATALOG`, `modules/ai/trademark.ts`
for `checkTrademarks` — both only read/imported, never edited except the two follow-on fixes below).

## Built
- `ensureReferenceData(db)` (`invai-backend/src/db/reference/index.ts`): upserts the plan catalog
  (reusing `PLAN_CATALOG` from `modules/billing/service.ts`, imported lazily so this module stays
  importable without forcing full env validation at import time — same reason `db/migrate.ts` itself
  imports `env` dynamically) and the trademark-mark index (`plans.key` / `(trademark_marks.normalized,
  trademark_marks.kind)` as the upsert keys, `sql`excluded.<col>`` for the multi-row `onConflictDoUpdate`,
  matching the pattern already used in `modules/finance/service.ts:766`). Creates no tenant rows.
- `invai-backend/src/db/reference/trademarks.ts`: the ~470-mark class-25 index, moved verbatim from
  `db/seed/trademarks.ts` (deleted), now InvAI's versioned reference dataset
  (`REFERENCE_DATA_VERSION = "2026-09-24.1"` in `reference/index.ts`; each upserted row's `source`
  is `reference:<version>`, replacing the old `source: "seed"`).
- `invai-backend/src/db/migrate.ts`: `runMigrations` now builds its `drizzle()` handle with
  `{ casing: "snake_case" }` (needed so `ensureReferenceData`'s multi-word columns, e.g. `serialNo` →
  `serial_no`, map correctly — the old bare `drizzle(pool)` only ever ran the raw-SQL migrator, which
  didn't care) and calls `ensureReferenceData(db)` right after `migrate(...)`.
- `invai-backend/src/db/seed/index.ts`: `seedGlobals()` no longer inserts trademark marks (removed the
  `trademarkMarks` insert block and its now-unused imports); it still inserts the plan catalog exactly
  as before. A comment explains why.
- Follow-on fixes in files I own by role (`src/modules/ai/**`) that the move required to keep the repo
  green:
  - `src/modules/ai/service.test.ts`: removed the local `seedMarks()` helper and its `db/seed/trademarks`
    import — the global test setup now populates `trademark_marks` for every test file via
    `ensureReferenceData`, so re-seeding per-file was redundant (and its import path no longer existed).
  - `src/modules/ai/trademark.ts`: updated a doc-comment path reference (`src/db/seed/trademarks.ts` →
    `src/db/reference/trademarks.ts`). No behavior change.
- New test: `invai-backend/src/db/reference/index.test.ts` — migrates a throwaway scratch database
  (`invai_ref_check`, created and dropped in the test itself, never the shared `invai_test*` DB) from
  empty and proves: no tenants, 5 plans, 200+ trademark marks; migrating it again is a no-op; and
  `checkTrademarks` on "Disney shirt" comes back `riskLevel: "high"` and includes `DISNEY` in `matches`.

## Acceptance criteria
| # | Met? | Evidence (command or screenshot) |
|---|---|---|
| 1. `ensureReferenceData(db)` upserts marks + plan catalog, idempotent, no tenants, runs at the end of `runMigrations` so `pnpm db:migrate` on an empty DB leaves the trademark check working | Yes | `src/db/reference/index.test.ts` (all 3 cases pass); manual CLI run below |
| 2. Marks moved from seed into versioned reference data; seed still produces the same demo results | Yes | `db/seed/trademarks.ts` deleted, content now in `db/reference/trademarks.ts`; full `pnpm db:seed` run below completed with the same shape as before (360 orders, 8 shop users + 1 vendor, 108 blanks, 25 sheets, `plans: 5` logged with no `trademarks` line) |
| 3. Test: migrate an empty test DB, trademark check on "Disney" comes back high risk | Yes | `src/db/reference/index.test.ts` › "leaves the trademark check working: a known mark comes back high risk" |

## Checks I ran
| Repo | Command | Result (last lines) |
|---|---|---|
| invai-backend | `pnpm typecheck` | `tsc --noEmit` — no errors |
| invai-backend | `pnpm exec biome check src/db/reference/ src/db/migrate.ts src/db/seed/index.ts src/modules/ai/service.test.ts src/modules/ai/trademark.ts` | "Checked 7 files in 18ms. No fixes applied." (one auto-fixed import-sort issue in `reference/index.ts` before this) |
| invai-backend | `pnpm lint` (whole repo) | "Checked 198 files in 90ms. No fixes applied." — clean; no stray errors from other cards' in-flight files at the time I ran it |
| invai-backend | `TEST_DATABASE_URL=postgres://invai_app:invai@localhost:5432/invai_test_t15 TEST_MIGRATION_DATABASE_URL=postgres://invai:invai@localhost:5432/invai_test_t15 pnpm test` | "Test Files 39 passed (39) — Tests 226 passed (226)" |
| invai-backend | same, filtered to `reference` | "Test Files 1 passed (1) — Tests 3 passed (3)" |

## Exercised for real
- **CLI migrate on an empty DB** (own scratch database, never the shared dev DB or another agent's
  test DB): created `invai_ref_check_cli`, ran
  `MIGRATION_DATABASE_URL=postgres://invai:invai@localhost:5432/invai_ref_check_cli pnpm db:migrate`
  → `[migrate] up to date (invai_ref_check_cli)`. Queried it directly:
  `trademark_marks` = 471, `plans` = 5, `companies` = 0, and
  `select mark, owner from trademark_marks where normalized = 'disney'` → `DISNEY | Disney Enterprises`.
  Dropped the scratch DB afterward.
- **Full demo seed on a second scratch DB** (`invai_ref_check_seed`, not the shared dev DB): ran
  `pnpm db:migrate` then `pnpm db:seed` with `DATABASE_URL`/`MIGRATION_DATABASE_URL` pointed at it.
  Completed end to end (imaging wasn't running locally, so it hit the pre-existing "imaging is down:
  designs get placeholder file keys" fallback — unrelated to this change, and the same thing would
  happen today on `main`): `globals {"plans":5}` (no more `trademarks` count logged — confirms the
  removed insert), 8 shop users + 1 vendor, 108 blanks, 40 designs, 360 orders / 680 items, 25 sheets,
  264 shipments. Verified afterward: `trademark_marks` = 471, all with `source like 'reference:%'`;
  `companies` = 2. Dropped the scratch DB afterward.
- **Vitest scratch-DB test** (`src/db/reference/index.test.ts`): creates and drops `invai_ref_check`
  itself as part of the test run (verified the database was gone afterward with
  `select datname from pg_database where datname like 'invai_ref_check%'` → 0 rows).
- Refused/negative case: not applicable — this card has no permissioned procedure; the closest is
  "creates no tenant rows on an empty DB", which the test asserts directly (`companies` and `users`
  counts are 0 right after migrate, before any seed or sign-up).

## Decisions
- Kept `PLAN_CATALOG` as the single source of truth in `modules/billing/service.ts` (billing's domain)
  rather than duplicating the price list into `db/reference/`; `ensureReferenceData` imports it lazily
  (dynamic `import()`) inside the function body specifically so importing `{ ensureReferenceData }` (as
  `migrate.ts` now does at module top level) doesn't force full `env` schema validation just by being
  imported — only when it actually runs, mirroring the existing dynamic `env` import already in
  `migrate.ts`'s CLI guard. Not recorded as a cross-cutting decision file; it's local to this card.
- `ensureReferenceData` takes a plain `NodePgDatabase` (the same handle `runMigrations` already builds
  for the migrator), not `withSystem`/`Tx` from `db/client.ts` — so it works against whatever database
  URL `runMigrations` was given, including a scratch DB, without needing the app's global
  `MIGRATION_DATABASE_URL`-backed connection pool.
- `source` on upserted trademark rows is now `reference:<REFERENCE_DATA_VERSION>` instead of `"seed"`,
  so a future USPTO bulk loader (B-46, wave 8, out of scope here) can tell reference-managed rows apart
  from its own. No schema change: `trademark_marks.source` was already a free-text column.
- Deleted `db/seed/trademarks.ts` outright rather than leaving a dead duplicate of the mark list next to
  the new `db/reference/trademarks.ts` — leaving both would have let them drift out of sync. This file
  wasn't itself on the card's owned-paths list, but it was the file `db/seed/index.ts` (which is on the
  list) imported, so removing it is part of "stop inserting trademark marks there, now that reference
  data does it." Updated the one other real reference to it, `src/modules/ai/service.test.ts`'s
  `seedMarks()` helper, which is inside `src/modules/ai/**` (owned by this role per `.claude/agents/ai-engineer.md`).

## Known gaps and follow-ups
- I did not run the full imaging-dependent seed with imaging actually up (it wasn't running locally);
  the seed's own pre-existing "imaging is down" fallback covered it, so `seedGlobals()` — the only part
  this card touches — was exercised for real either way. Running the seed with imaging up is unrelated
  to this card's diff.
- I did not run `run-golden-path` or the E2E suites: this card touches no golden-path route, UI, or API
  contract, only migration-time bootstrapping, per the card's risk flag (`migration` only, no `ui`/`ai`
  route flags beyond ownership).
- During this session I hit a real, environment-level hazard worth flagging to the tech lead: partway
  through, migrating my dedicated `invai_test_t15` a second time failed with
  `relation "purchase_order_receipts" already exists`. Root cause: `drizzle/meta/_journal.json`'s
  `when` timestamp for T-1-3's `0008_inventory_po_idempotency` migration didn't match the `created_at`
  drizzle had already recorded for it in `invai_test_t15` (drizzle's migrator decides what to (re)run
  by comparing the journal's `when` against the last-applied `created_at`, not by content hash — see
  `drizzle-orm/pg-core/dialect.js:44-72`), because that migration/journal entry was edited while my
  first test run was in flight. This is T-1-3/integrations-engineer's migration, not mine — I didn't
  touch `drizzle/**` or `src/db/schema/inventory.ts`. I resolved it on my side by dropping and
  recreating my own `invai_test_t15` (never the shared dev DB, never another card's test DB), which
  isn't a fix for the underlying hazard, just a workaround for my own test DB. Flagging so the tech
  lead is aware this class of failure can happen for anyone re-running tests while another agent is
  actively regenerating a migration file — matches the documented risk in `CLAUDE.md` ("If two agents
  collide on the drizzle journal, the later one regenerates").

## Blocked by other owners
- None. (The journal-timestamp issue above is reported as a shared-environment note, not a blocker —
  it didn't block this card once I refreshed my own test DB, and it's outside my owned paths.)

## Processes and data
- Stopped: no long-running processes were started (no `dev:api`/`dev:worker`/imaging server started by
  me).
- Shared dev DB (`invai`): untouched — every command I ran explicitly overrode `DATABASE_URL` /
  `MIGRATION_DATABASE_URL` / `TEST_DATABASE_URL` / `TEST_MIGRATION_DATABASE_URL` to point at my own
  `invai_test_t15` or a disposable scratch database (`invai_ref_check`, `invai_ref_check_cli`,
  `invai_ref_check_seed` — all created and dropped by me). `invai_test_t15` itself was left in place
  (mid-wave convention: it's this card's dedicated test DB, not a scratch DB, so it isn't torn down).
- Other agents' concurrent changes (T-1-3's inventory PO idempotency migration, T-1-2's webhooks work,
  etc.) were present in the shared working tree throughout; I never staged or committed anything outside
  my own paths (confirmed with `git diff --cached --stat` before committing, and `git status --short`
  showed only my paths at commit time).

## Commit (round 1)
`8becdb5` on `main` (invai-backend), 7 files changed (`src/db/migrate.ts`,
`src/db/reference/index.ts`, `src/db/reference/index.test.ts`,
`src/db/reference/trademarks.ts` (renamed from `src/db/seed/trademarks.ts`),
`src/db/seed/index.ts`, `src/modules/ai/service.test.ts`, `src/modules/ai/trademark.ts`).
Committed with an explicit pathspec on both `git add` and `git commit -- <paths>` (not a bare
`git add -A` / `git commit`), per the tech lead's note mid-task about the shared index. Not pushed
(per instructions — the tech lead pushes after the wave's integration gate).

## Round 2 (review findings addressed)

Both round-1 reviews (`invai-docs/waves/1/reviews/T-1-5-reviewer-r1.md`,
`T-1-5-backend-foundation-r1.md`) came back **changes-required**, on one shared blocking finding, plus
one comment fix the tech lead asked for directly:

1. **Blocking — hard-coded scratch DB.** `src/db/reference/index.test.ts:18,32,44` used a fixed name
   (`invai_ref_check`) for its throwaway migration-target database. Both reviewers reproduced two
   concurrent `pnpm test` runs (each on its own `invai_test_*` DB, the normal state during a wave)
   racing each other: one run's `afterAll` (`DROP DATABASE ... WITH (FORCE)`) dropped the database the
   other run was still migrating, and both raced `CREATE EXTENSION`. Fixed by deriving the scratch DB
   name from the run's own test database instead of a constant:
   `` `${new URL(env.MIGRATION_DATABASE_URL).pathname.slice(1)}_ref` `` (so `invai_test_t15` gets
   `invai_test_t15_ref`, `invai_test_t13` gets `invai_test_t13_ref`, etc.) — matching the reviewer's
   suggested fix. The `DROP ... WITH (FORCE)` in `afterAll` was already scoped to the `SCRATCH_DB`
   variable, so no other change was needed there.
2. **Comment fix (tech lead, not from either review's blocking list).** The comment on the lazy
   `await import("../../modules/billing/service")` in `reference/index.ts` claimed the deferred import
   kept `runMigrations`/`db:migrate` "free of the full env schema" — wrong, per both reviews' optional
   notes: `db:migrate`'s CLI guard already loads the full `env` before calling `runMigrations`
   (`migrate.ts`'s `argv` block), so production's key guard (T-1-1) already applied regardless of this
   import. Rewrote the comment to say precisely what the deferral does (keeps *importing*
   `ensureReferenceData` free of `modules/billing/service` and env, for anyone who imports `./reference`
   without calling it) and does not do (make `db:migrate` itself env-free).

Explicitly **not done**, per the tech lead's instruction that non-blocking notes go to the backlog:
a `pg_advisory_lock` around `runMigrations` for concurrent-deploy safety, pruning trademark rows whose
`source` is an old reference-data version, and moving `PLAN_CATALOG` into a dependency-free
`billing/catalog.ts`.

### Re-verification (definition of done, round 2)
| Check | Result |
|---|---|
| `pnpm typecheck` | `tsc --noEmit` — no errors |
| `pnpm exec biome check src/db/reference/ src/db/migrate.ts` | "Checked 4 files in 51ms. No fixes applied." |
| `pnpm lint` (whole repo) | "Checked 198 files in 87ms. No fixes applied." |
| `TEST_DATABASE_URL=…/invai_test_t15 TEST_MIGRATION_DATABASE_URL=…/invai_test_t15 pnpm test` | "Test Files 39 passed (39) — Tests 228 passed (228)" |
| **Concurrency repro, fixed:** two `vitest run reference` processes launched together in the background, one on `invai_test_t15`, one on a second test DB `invai_test_t15b` | Both exit 0, 3/3 each. Logs: run 1 creates and uses `invai_test_t15_ref`; run 2 creates and uses `invai_test_t15b_ref`. No `DROP DATABASE` or `CREATE EXTENSION` race — confirms the exact scenario both reviews reproduced against round 1 now passes. |
| Cleanup after the concurrency repro | Both `*_ref` scratch DBs were already gone (dropped by each run's own `afterAll`); dropped the extra `invai_test_t15b` I created only for this repro (not one of my normal DBs) |

### Commit (round 2)
`b8d0471` on `main` (invai-backend), 2 files changed: `src/db/reference/index.test.ts` (scratch DB name
derivation) and `src/db/reference/index.ts` (comment fix only — no logic change). Committed with
`git add <exact paths>` then `git commit -m "..." -- <exact paths>`; `git status --short` was clean
immediately before and after. Not pushed.
