# Review of T-26-4 (round 1)

- Reviewer: reviewer on fable
- Author: backend-engineer on opus
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` / `pnpm lint` (invai-backend @ 5930d59) | exit 0 / exit 0 (480 files, no fixes) |
| `OPENAI_API_KEY= ANTHROPIC_API_KEY= pnpm vitest run src/modules/photos src/api/buckets.test.ts src/db` | exit 0; 16 files, 75 tests passed (rls-coverage + fk-coverage included, no exception added) |
| same env, `src/api/authz.test.ts` | exit 0; 7 passed (walks `photos.*` as anon / no-permission / floor / station / vendor) |
| Mutation proof in worktree `../invai-backend-t264r` (removed after): dropped `!c.chargedAt &&` at `service.ts:1194`, ran `-t "charges once per composition"` | RED: `duplicate key value violates unique constraint "ai_credit_ledger_photo_ref_uq"` (T-26-3 backstop fires first; without it the `ledger toHaveLength(8)` assertion at `photos.test.ts:308` would see 16) |
| `scan-test-weakening.sh invai-backend 30618a0~1`; grant-file diffs of both commits | removed=0 added=190; hits are spies/mocks of imaging and `../ai/*` (dependencies); "test-only branch" hits are T-26-3 files. Grants: one export, one mount, one import, `AI_BUCKET_PROCEDURES` + `photos.estimate` read, one bucket test, additive imaging functions |
| dev DB read-only (`psql`): set `901e408d` | status ready, zip ready 3 files, 8/8 compositions charged, 8 ledger rows, 16 done images; `relrowsecurity = t` and a policy on all 4 `photo_*` tables |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `0040_photos_sets.sql` after `0039_ai_photos` in the journal; 4 tables with `company_id`, `ENABLE RLS`, `*_tenant` policy, composite `(company_id, id)` FKs; unique `(set, garment, view, hex)`, `(composition, preset)`, `(company, idempotency_key)` |
| 2 | yes | `analyzeDesign` tenant-loads via `getDesign` (tenancy walk → NOT_FOUND), `assertCredits` then upsert + `afterCommit` enqueue; `runAnalysis` holds no tx across palette/model; `contrast.ts` WCAG ratio < 3 (test: white warns `light_on_light`, black doesn't); refresh supersedes by `jobId` |
| 3 | yes | tests: estimate 4 comps/2 skips; same key → same id + 1 outbox event; other spec → CONFLICT; CREDITS_EXHAUSTED with 0 rows; >48 → BAD_REQUEST |
| 4 | yes | one `photos.renderComposition` per composition on `render` at `BULK_PRIORITY` (10; `production.buildSheets` keeps default 0); `out_key` built server-side; `recordRenders` locks set then composition `FOR UPDATE`, charges only when `charged_at IS NULL`; run-twice → 8 ledger rows; imaging down → failed, 0 charged; partial → `ready` "1 of 16" |
| 5 | yes | contract `photos.manage`; presser → FORBIDDEN through the router (`photos.test.ts:453`); zip before approval → `not_approved` count |
| 6 | yes | `zipName` = `<channel>/<slot>-<garment>-<view>-<color>.jpg`; fingerprint of channel + approved ids reuses the job (same jobId, 1 enqueue); `getSet` presigns zip only when `ready` |
| 7 | yes | `attachPhotosToDraft` gets approved keys, `aiGenerated`/`syntheticPerformer` from image flags (false for templates); foreign draft → NOT_FOUND (real `getDraft`) |
| 8 | yes | `signed()` returns null unless `isCompanyKey`; test plants a foreign-prefix key → `url: null`; `listSets` signs only the slot-0 lead |
| 9 | partial | 18 photos tests + 2 contrast; two-company walk over 7 procedures + list; QA `photos.acceptance.test.ts` not in tree (wave log: QA writes it before T-26-5; not the author's gap) |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat`): module, schema + migration, granted lines only
- [x] Nothing outside scope (`pushTargets`/`pushToShopify` stay NOT_IMPLEMENTED)
- [x] Tests exercise the behavior, and none were weakened
- [x] Tenancy (`withTenant` everywhere, no `withSystem` in the module, RLS on 4 tables), idempotency (key + unique index; `charged_at` guard + backstop), credits in integers, inches unrounded (`widthIn/heightIn` straight to imaging)
- [x] Decisions recorded where needed (ADR 0023 is the reference; nothing new needed)

## Optional notes (not blocking)
- (a) `service.ts` `attachToDraft`: a draft of another design (same company, same channel) is accepted; the contract comment says "same design". Needs a `PHOTO_BAD_REQUEST_REASONS` entry from the architect (backlog row), then one `draft.designId !== s.designId` check here; `conflict()` would do meanwhile.
- (b) No re-assert at charge: overdraw bounded by one set (≤ 48), same pattern as `ai.createDrafts`; backlog note. (c) `toChecks` drops unknown codes but keeps `passes: false`, so nothing is hidden; `design_drift`/`region_changed` are already in the enum, phase B is safe.
