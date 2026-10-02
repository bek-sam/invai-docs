# T-26-4: Backend `photos` module: photo sets, render jobs, credits, approval, zip, attach

| Field | Value |
|---|---|
| Wave | 26 |
| Scope ref | `product/scope.md#listing-photos` (SCR-008) |
| Spec | `specs/listing-photos.md` |
| Owner | backend-engineer (area: photos, new module) |
| Reviewer | reviewer (fable) |
| Co-reviewers | backend-foundation (sonnet, new tables and migration); security-reviewer (opus, tenancy and files) |
| Risk flags | tenancy, files, migration, payments (AI credits) |
| Model | opus |

## Read first
- `.claude/agents/backend-engineer.md`; playbooks `add-backend-feature`, `add-tenant-table`, `idempotent-job`, `idempotent-side-effect`.
- `invai-backend/src/modules/README.md`, a recent module with jobs as the pattern (`src/modules/digest/**` or `market/**`), `src/lib/queues.ts` (`defineJob`), `src/lib/s3.ts` (`objectKey`, `isCompanyKey`, `presignGet`), `src/db/client.ts` (`withTenant`), `src/ai/credits.ts`, `src/modules/catalog/service.ts` `productMockup` (~line 888: design files, blank hex), `src/integrations/imaging/client.ts`.
- Contract `invai-contracts/src/contract/photos.ts` (T-26-1), ADR 0023; `wave.md` "Agreed interfaces"; stubs from T-26-3 (`analyzeDesignForPhotos`, `attachPhotosToDraft`, credit constants).
- `invai-docs/team/agent-brief.md` (tests isolate themselves; scratch stack rules).

## Owned paths (edit)
- `invai-backend/src/modules/photos/**` (new; the QA acceptance file `photos.acceptance.test.ts` there is qa-engineer's, read-only for you)
- `invai-backend/src/db/schema/photos.ts` (new) and its migration (`pnpm db:generate --name photos_sets`), committed together
- Grants (one line each, stage only your lines): `src/db/schema/index.ts` (export), `src/api/router.ts` (mount `photos`), `src/modules/jobs.ts` (import `./photos/jobs`), `src/api/orpc.ts` (`bucketFor`: route `photos.analyzeDesign`, `photos.createSet`, `photos.pushToShopify` to the `ai` bucket; any non-GET read on the NON_GET_READS list) and `src/api/buckets.test.ts` (the matching cases) (plan review item 1)
- Grant: `src/integrations/imaging/client.ts`, additive functions only (`photoPalette`, `photoTemplates`, `photoRender`, `photoZip`) with their response schemas; integrations-engineer's file, nobody else edits it this wave

## Read-only paths
- `src/ai/**`, `src/modules/ai/**` (T-26-3), `src/modules/catalog/**`, every other module, `src/lib/**`, `src/test/**`, `invai-contracts/**`, `invai-imaging/**`, `invai-web/**`.

## Depends on
- T-26-1 (contract), T-26-2 (imaging routes committed), T-26-3 stubs committed.

## First commit (before anything else, right after T-26-1 lands)
`src/modules/photos/router.ts` with every `photos.*` handler stubbed (typed "not available yet" error) plus the `router.ts` mount line, so backend typecheck is green again for T-26-3 (plan review item 2). Then build the rest.

## Interfaces promised
- Router handlers for every `photos.*` procedure in the contract except `pushToShopify` (wave 27: return the contract's "not available yet" error until then).

## Acceptance criteria
1. **Tables.** `photo_sets`, `photo_compositions` (set, garment, view, color hex; `charged_at`) and `photo_images` (composition × channel preset), names may follow the ADR, each with `company_id`, an RLS policy and the indexes the queries need; unique keys on (set, garment, view, hex) and (composition, preset) so job retries upsert, never duplicate. Your migration is generated **after** T-26-3's `ai_photos` migration (journal order). The RLS coverage test passes with no exception added.
2. **Analyze (a job, plan review item 4).** `photos.analyzeDesign` loads the design (tenant-scoped; another tenant's id → NOT_FOUND) and returns the cached analysis, or enqueues an analysis job on the `ai` queue (after commit) and returns `{status: "pending"}`; the job gets the palette from imaging and calls `analyzeDesignForPhotos(companyId, userId, …)` with no transaction open across the model call. The stored result carries **deterministic contrast warnings computed in code** (WCAG-style contrast between the palette's dominant opaque colors and each recommended or chosen blank; light art on a light blank and dark art on a dark blank warn, with the ratio). Cached per design until `refresh`.
3. **Estimate and create.** `estimate` returns compositions (distinct garment × view × color that the design can show: no back view without a back print file), images (compositions × channel presets), and credits (`PHOTO_TEMPLATE_CREDITS` per composition; channel derivatives are free). `createSet` refuses with `CREDITS_EXHAUSTED` when the balance is below the estimate, refuses more than 48 compositions with BAD_REQUEST, is idempotent on `idempotencyKey` (same key → same set, no second job), and only enqueues: no rendering in the request.
4. **Jobs (heavy work on the queue).** One render job per composition (plan review item 9), with a lower BullMQ `priority` than gang-sheet compose on the `render` queue; it renders each channel image of that composition through imaging at the real print size from `design_files.widthIn/heightIn` and the chosen hex, stores results under the company prefix, saves checks, and charges credits **once per composition**: `SELECT … FOR UPDATE` on the composition row, charge only when `charged_at IS NULL`, then set `charged_at` in the same transaction, ledger `ref = {type: "photo_composition", id}` (plan review item 5; T-26-3 adds a partial unique index as a backstop). A retried or duplicated job never charges twice: test it by running the job twice. Imaging down → the image is `failed` with a readable error, the set ends `ready` with failures counted or `failed` if nothing rendered; nothing charged for failed images.
5. **Approval.** `reviewImages` lets a person approve or reject rendered images; only `owner`, `admin`, `office`, `designer` (per contract permissions); a presser → FORBIDDEN. Only approved images can be zipped or attached; trying with an unapproved id → BAD_REQUEST naming the count.
6. **Zip.** `exportZip` enqueues a job that calls `/photo/zip` with approved images named `<channel>/<slot>-<garment>-<view>-<color>.jpg`, stores the key on the set, and `getSet` returns a presigned URL when ready. Running it twice for an unchanged approval set reuses the zip.
7. **Attach.** `attachToDraft` calls `attachPhotosToDraft` with the approved images' keys and their flags (phase A images: `aiGenerated=false`, `syntheticPerformer=false`); another tenant's draft → NOT_FOUND.
8. **Signed URLs.** `getSet` presigns only keys under the caller's company prefix (`isCompanyKey`), and `listSets` doesn't presign every image of every set (thumbnail of slot 1 only), so the web list doesn't fire dozens of URL requests (lesson 2026-10-01 P1).
9. Tests: service and job tests with a fake imaging client (your test double in your test file), tenancy test with two companies for every procedure, the double-charge test, the idempotent create test, and the QA acceptance file going green.

## Verification
- While building: `pnpm vitest run --reporter=dot src/modules/photos 2>&1 | tail -n 40`. Once at the end: `set -o pipefail; pnpm typecheck && pnpm lint && pnpm test > /tmp/t264.log 2>&1; echo $?; grep -nE 'FAIL|Error' /tmp/t264.log | head -n 30; tail -n 15 /tmp/t264.log` (Bash timeout 600000).
- Exercise for real on the dev DB (apply your migration with `pnpm db:migrate`; never `db:reset`): imaging from the repo on `:8142` (`uv run uvicorn app.main:app --port 8142`), API `PORT=3142 IMAGING_URL=http://localhost:8142 OPENAI_API_KEY= ANTHROPIC_API_KEY= pnpm dev:api`, and a worker with the same env. Sign in as `office@desertbloom.test`, analyze a design, create a set (2 garments × 2 colors × 2 views, channels amazon + etsy), wait for `ready`, approve 3 images, export a zip, attach to an AI draft; show the credit ledger rows (one per composition) and open 2 rendered images and the zip listing. Refused: `presser@` → FORBIDDEN; a design id from another company → NOT_FOUND.
- Record every PID you start; stop them at the end.

## Out of scope
- Shopify push and lifestyle scenes (wave 27). Web. Imaging code. Seed changes.

## Commit and report
- Commit only owned paths (grant files: stage only your line), schema and migration in the same commit with passing tests; message ending with the co-author line from your instructions. Don't push; only the tech lead pushes after the gate.
- Report: `invai-docs/waves/26/reports/T-26-4.md` (verify-and-report, at most 60 lines, PIDs); reply in at most 8 lines.
