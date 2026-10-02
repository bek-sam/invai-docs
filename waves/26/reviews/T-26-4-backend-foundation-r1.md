# Review of T-26-4 (round 1)

- Reviewer: backend-foundation on sonnet
- Author: backend-engineer on opus
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `cd invai-backend && OPENAI_API_KEY= ANTHROPIC_API_KEY= pnpm typecheck` | clean, exit 0 |
| `cd invai-backend && OPENAI_API_KEY= ANTHROPIC_API_KEY= pnpm vitest run --reporter=dot src/db src/modules/photos` | 16 files, 84 tests passed, 0 failed (harmless "2 Vite servers from exiting" noise after the run — known pre-existing artifact, not a failure) |
| `git -C invai-backend show --stat 5930d59` + `30618a0` | only owned paths touched: `src/modules/photos/**` (new), `src/db/schema/photos.ts` + `drizzle/0040_photos_sets.sql`, and grant lines in `src/db/schema/index.ts` (1 export line), `src/api/router.ts` (1 import + 1 mount line), `src/modules/jobs.ts` (1 import line), `src/api/orpc.ts`/`src/api/buckets.test.ts` (bucket grants + matching test), `src/integrations/imaging/client.ts` (4 new additive functions only) |

## Tables (`src/db/schema/photos.ts`, `drizzle/0040_photos_sets.sql`)
- `photo_analyses`, `photo_sets`, `photo_compositions`, `photo_images`: all four have `company_id`, `tenantPolicy(...)`, `.enableRLS()`. New, empty tables, so plain `CREATE TABLE`/`CREATE INDEX` (not `CONCURRENTLY`) is correct per `zero-downtime-migration` ("create a new table" is safe as one step).
- Composite `(company_id, id)` FKs throughout: `photo_analyses`→`designs`, `photo_sets`→`designs`, `photo_compositions`→`photo_sets`, `photo_images`→`photo_sets` and →`photo_compositions`. All cascade on delete, matching the comment "rendered images follow the design." `requestedBy`/`createdBy`/`reviewedBy` use single-column `references(() => users.id, {onDelete:"set null"})` — consistent with the existing precedent (`tenancy.ts:309`), fine for an audit/display-only soft reference.
- Unique keys for idempotency, all correctly scoped: `(company_id, design_id)` on `photo_analyses` (one cached analysis per design); `(company_id, idempotency_key)` on `photo_sets` (the `createSet` idempotency key); `(company_id, set_id, garment, view, color_hex)` on `photo_compositions` (no duplicate composition per spec); `(company_id, composition_id, preset)` on `photo_images` (one image per channel preset, matches the "job retries upsert, never duplicate" requirement).
- Indexes lead with `company_id` throughout, including the two `photo_sets` list indexes and the `photo_images` channel/slot index used by `listSets`/`getSet`.
- Journal order confirmed after `0039_ai_photos` (`_journal.json`: idx 39 then 40).
- `rls-coverage`/FK-coverage tests pass with no new exception added (confirmed by reading the test output: no new entries, no skips in the diff).

## `FOR UPDATE` + `charged_at` guard (`service.ts` `recordRenders`, ~line 1150)
Read the full function. Lock order is documented and followed: `SELECT ... FOR UPDATE` on `photoSets` first, then `photoCompositions` (comment: "every writer of both takes them in this order" — consistent lock ordering avoids deadlocks). Charge fires only when `!c.chargedAt && imgs.some(DONE_IMAGE)`, inside the same transaction as the `chargedAt` update — exactly the pattern required, and backed by T-26-3's partial unique index as a second guard. Verified with a real test, not just reading: `photos.test.ts` "renders each composition's images, charges once per composition, and a rerun charges nothing" runs every composition's render job **twice** and asserts exactly 8 ledger rows for 8 compositions, each `chargedAt` set and `creditsCharged === 1`, `imaging.photoRender` called 16 times (not 32) — a real run-twice proof, not just a unit check of the guard in isolation.

## Outbox/queue usage
- `createSet` emits `photo_set.created` (outbox, after commit via the event→job wiring in `jobs.ts`), never renders in the request — confirmed by reading `jobs.ts`'s `onEvent("photo_set.created", dispatchSetJob, ...)` and the service only inserting rows + emitting.
- Jobs use `defineJob` throughout (`analyzeDesignJob`, `renderCompositionJob`, `dispatchSetJob`, `buildZipJob`), each with a stable, business-identity `jobId` (`photo-analysis-${jobId}`, `photo-render-${compositionId}`, `photo-dispatch-${setId}`, `photo-zip-${zipJobId}`) — safe to re-enqueue.
- `renderCompositionJob` runs on the `render` queue at `BULK_PRIORITY`, explicitly lower than gang-sheet compose's default priority, matching the card's "lower priority than gang-sheet compose" requirement.
- `onFinalFailure` marks the composition's images `failed` with a readable message rather than leaving them stuck — correct permanent-failure handling given BullMQ's `UnrecoverableError` isn't used yet anywhere in the codebase (known gap B-17, not this card's job to fix).

## Grant files
Confirmed each touches only its granted line(s): `src/db/schema/index.ts` (+1 export), `src/api/router.ts` (+1 import, +1 mount), `src/modules/jobs.ts` (+1 import), `src/api/orpc.ts` (+`AI_BUCKET_PROCEDURES` set and one `NON_GET_READS` entry, matching ADR 0023 §8 exactly), `src/api/buckets.test.ts` (+1 test case using the new exported set), `src/integrations/imaging/client.ts` (+4 new functions, additive schemas only, nothing existing touched).

## Acceptance criteria (tables/migration/idempotency/outbox lens; full behavior owned by `reviewer`)
| # | Met? | Evidence |
|---|---|---|
| 1 Tables | yes | as above |
| 4 Jobs / once-per-composition charge | yes | as above, with the run-twice test |
| 9 Tenancy tests | yes (partial per author) | `photos.test.ts` "another company gets NOT_FOUND for every procedure that takes an id, and sees none of the sets" — read and confirms a real two-company walk; QA's `photos.acceptance.test.ts` (separate commit `e32f9c5`, not this author's) exists in the tree as required, left untouched by this diff |

## Blocking findings
none.

## Checks
- [x] Only owned paths changed, grant files touched only on granted lines
- [x] Nothing outside scope (pushToShopify/lifestyle correctly left NOT_IMPLEMENTED/null, matching "out of scope: wave 27")
- [x] Tests exercise the behavior; no weakening observed (double-charge test is a genuine run-twice, not a mock of the guard)
- [x] Tenancy (RLS on all 4 new tables, composite FKs, two-company test), idempotency (unique keys + `charged_at` guard + partial index backstop), money in credits not cents (correct unit for this feature)
- [x] Decisions recorded: ADR 0023 covers the charge guard, queue priority and retention plan

## Optional notes (not blocking)
- Author's own gap list (negative-balance race at charge time if credits drop between create and render, `attachToDraft` not refusing a draft of a different design) are real but minor product-correctness items for `reviewer`/`ai-engineer` to weigh, not tenancy/migration/idempotency concerns.
