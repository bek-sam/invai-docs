# Review of T-27-3 (round 1)

- Reviewer: backend-foundation on Opus 5.5 (Sonnet 5 session)
- Author: backend-engineer (photos) on Opus
- Verdict: approve

Scope of this co-review: the migration (`invai-backend` 2e14396, `drizzle/0041_photos_lifestyle.sql` +
journal, `src/db/schema/photos.ts`) and the retention job (228ffa4, `src/modules/photos/purge.ts`,
`jobs.ts`). Not a full card review — tenancy/files/marketplace behavior is the primary reviewer's and
security-reviewer's/compliance-officer's.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git show 2e14396 --stat` / `-- src/db/schema/photos.ts` | `photo_pushes` new table + scene cols on `photo_compositions` + `lifestyle` on `photo_sets`; matches migration SQL |
| `cat drizzle/0041_photos_lifestyle.sql` | additive `ADD COLUMN` (nullable or defaulted), one index swap, new table, RLS policy, composite FK |
| `tail drizzle/meta/_journal.json` | idx 41 appended after idx 40 (`0040_photos_sets`), no collision |
| `git show 2e14396 --name-only \| grep 0040` | 0040's SQL/snapshot untouched — not hand-edited |
| `git show 228ffa4 -- src/modules/photos/purge.ts,jobs.ts` | tenant-scoped, batched (500/run), restartable (marks `scene_purged_at`/resets `zip_status`, re-selects unmarked rows next run), nightly scheduler |
| `OPENAI_API_KEY= ANTHROPIC_API_KEY= pnpm vitest run --reporter=dot src/db src/modules/photos` | 18 files / 111 tests passed (the "2 Vite servers" close-timeout message is the known pre-existing harness noise, not a test failure) |

## Acceptance criteria (my scope only)
| # | Met? | Evidence |
|---|---|---|
| company_id + RLS + indexes on `photo_pushes` | yes | `companyId: companyId()`, `tenantPolicy("photo_pushes")`, `.enableRLS()`; migration has `ENABLE ROW LEVEL SECURITY` + `CREATE POLICY ... USING/WITH CHECK (company_id = current_setting(...))`; unique index and a secondary index both lead with `company_id` |
| composite FKs | yes, with one documented exception | `photo_pushes_set_fk` is composite `(company_id, set_id) → photo_sets(company_id, id)` per `add-tenant-table`/B-30. `connectionId`/`listingId` carry no FK at all — a deliberate, commented choice (card's own text: "no FK into the channels module's tables"; checked by the service under the tenant) so this module doesn't reach into `channels`' schema. Acceptable as a cross-module boundary call, not a tenancy gap, since the service re-reads both rows under `withTenant` before use (`push.ts` `pushToShopify`) |
| unique key backing push idempotency | yes | `uniqueIndex().on(t.companyId, t.idempotencyKey)` + stored `requestHash`; `push.ts` looks up by `idempotencyKey`, returns the stored row if the hash matches, throws `CONFLICT` on a changed `imageIds`/target under the same key, and races on insert fall back to re-reading the row (`onConflictDoNothing` + re-select) — the idempotent-side-effect pattern done right |
| additive/safe ALTERs, lock risk | yes | all `ALTER TABLE ... ADD COLUMN` are nullable or have a constant default (metadata-only on PG ≥ 11, no table rewrite); the one `DROP INDEX` + non-concurrent `CREATE UNIQUE INDEX` is on `photo_compositions`, a new (wave 26) small per-set table, not on the "big table" list in `zero-downtime-migration` (orders, order_items, outbox_events, audit_log, scans, inventory_movements) — a plain index swap is fine at this size, matching how 0039/0040 were done |
| journal order after 0040 | yes | idx 41, tag `0041_photos_lifestyle`, timestamp after 0040's; no other card's commits touch the journal in this diff |
| not hand-edited | yes | `src/db/schema/photos.ts` diff maps 1:1 onto the generated SQL (new columns, new table, new unique index); regenerating from the schema in a scratch copy wasn't needed given the direct correspondence and that 0040's files are untouched |
| retention job: tenant-scoped, batched | yes | `purgePhotoFiles()` uses `withSystem` only to read ids/keys (ids-and-keys-only cross-tenant read, same pattern as the PII purge), then writes per company under `withTenant`; `BATCH = 500` per run via the nightly `reports` scheduler; idempotent (guarded by `isNull(scenePurgedAt)` / `zipStatus = "ready"`, a missing S3 object is caught and logged, not thrown) |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`src/db/schema/photos.ts`, `drizzle/0041_*`, `src/modules/photos/{purge,jobs}.ts` — all inside the card's owned globs)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; no weakening seen in the two commits reviewed
- [x] Tenancy (`withTenant`, RLS on the new table), idempotency (unique key + request hash on `photo_pushes`), money/i18n not applicable to this diff
- [x] Decisions recorded where needed — none needed; the no-FK-into-channels choice is documented inline in the schema file's doc comment, matching the card's own text

## Optional notes (not blocking)
- The `photo_pushes.connectionId`/`listingId` lack of any FK (not even single-column) means an orphaned
  row is possible if a connection or listing is hard-deleted; low risk today (no hard-delete path visible for
  either), but worth a line in `src/modules/README.md` if this no-FK-across-module pattern recurs for other
  modules' "tolerated foreign-table read" cases.
- `purgePhotoFiles()` processes at most 500 scenes + 500 zips per invocation with no loop-until-drained; fine
  at current volume (nightly cron, pilot scale), flag to backend-foundation if the backlog ever needs more
  than one run per night.
