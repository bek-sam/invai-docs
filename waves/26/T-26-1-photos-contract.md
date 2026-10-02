# T-26-1: Contract for listing photos (phases A and B)

| Field | Value |
|---|---|
| Wave | 26 |
| Scope ref | `product/scope.md#listing-photos` (SCR-008) |
| Spec | `specs/listing-photos.md` |
| Owner | architect |
| Reviewer | reviewer (opus, a different model from the author) |
| Co-reviewers | backend-foundation (sonnet), web-engineer (sonnet, consumer) |
| Risk flags | contract |
| Model | fable |

## Read first
- `.claude/agents/architect.md`, playbook `add-contract-procedure`; `invai-docs/waves/26/wave.md` "Agreed interfaces" and `waves/27/wave.md` (phase B needs).
- `invai-contracts/src/contract/{_base,ai,catalog,channels,files}.ts`, `src/roles.ts` (or wherever permissions live), decisions 0017 (listing attributes), 0021 (OpenAI provider), 0022 (this feature's fence, written by the PM).
- Existing shapes to reuse: listing draft (`ai.listings.*`, its `mockupKeys`), design ids (`catalog`), channel connections (`channels`).

## Owned paths (edit)
- `invai-contracts/src/**` (new `src/contract/photos.ts`, its registration, permissions, tests)
- `invai-docs/decisions/0023-listing-photos-pipeline.md` + its index row in `invai-docs/decisions/README.md`

## Read-only paths
- Every code repo except `invai-contracts`.

## Depends on
- Spec `specs/listing-photos.md` and decision 0022 (product-manager, plan-review step). If missing when you start, design from this card and `wave.md`, and note it.

## Interfaces promised
A `photos` router (names fixed; shapes yours):
- `photos.analyzeDesign {designId}` → `DesignPhotoAnalysis` (cached per design; `refresh` flag optional). Decide whether it runs in the request (like `ai.listings.create`) or as a job with polling; record why in the ADR.
- `photos.estimate {designId, garments, colors, views, channels, lifestyle?}` → `{compositions, images, credits}` (no side effects).
- `photos.createSet {designId, garments[], colors[{name, hex}], views[], channels[], lifestyle?: {count, sceneIds?}, idempotencyKey}` → `PhotoSet` (enqueues; idempotent on the key).
- `photos.listSets {designId?, cursor?}`, `photos.getSet {id}` → set with images (signed URLs), status, credits charged, zip state.
- `photos.reviewImages {setId, approve: id[], reject: id[]}` (a person approves; only approved images can leave InvAI).
- `photos.exportZip {setId, channel?}` → enqueues; set shows `zip: {status, url?}`.
- `photos.attachToDraft {setId, draftId, imageIds[]}` → listing draft summary (approved images only).
- `photos.pushToShopify {setId, connectionId, productRef, imageIds[], idempotencyKey}` → push status (built in wave 27). Decide how `productRef` is chosen (an existing channel listing mapping vs a typed product id) after reading `channels`.
- Enums: `GarmentType` (tee, hoodie, crewneck, tank), `PhotoView` (front_flat, folded, back, on_model_white, lifestyle), `PhotoChannel` (amazon, etsy, shopify, tiktok, walmart), `PhotoImageSource` (template, ai_scene), image and set statuses, check failure codes (background_not_white, fill_below_min, too_small, design_drift, region_changed …).
- Image shape includes: `aiGenerated`, `containsSyntheticPerson`, `drawnTemplate` (true for drawn people/garments, so the UI and Amazon checks can say "illustration, not a photo"), `checks`, `altText`, `slot`, `creditsCharged`, `designLockScore` (nullable, phase B).
- Listing draft gains image disclosure fields (for example `imageDisclosures: {aiGenerated, syntheticPerformer}`), optional so older clients keep working.
- `photos.analyzeDesign` returns the cached analysis or enqueues and returns `{status: "pending"}` (plan review item 4: analysis runs as a job, never holding a transaction across a model call); the web polls.
- `photos.pushTargets {designId, connectionId?}` (GET, read permission) → the shop's Shopify listings from the backend `listings` table, this design's first; `pushToShopify`'s `productRef = {listingId: Id}` (plan review item 7).
- Append `photo_image` (and `photo_scene` for wave 27) to the end of `CREDIT_KINDS` in `src/schemas/ai.ts` (~line 233) so the credits ledger output validates (plan review item 3).
- Reuse `CREDIT_ERRORS` / `SPEND_CAP_ERRORS` (`contract/ai.ts` ~22-40) and add one `IMAGE_DAILY_CAP_REACHED`; derive `PhotoChannel` from `CHANNELS` (`states.ts` ~174).
- In the ADR, list each procedure's HTTP method and rate bucket (`ai` for analyzeDesign, createSet, pushToShopify).
- Permissions: read and manage permissions for photos, granted to the roles that can manage AI listings today (owner, admin, office, designer); refused for presser, packer, receiver and vendor.

## Acceptance criteria
1. Given the new `photos.ts`, when consumers import `@invai/contracts`, then every procedure above exists with Zod v4 input/output schemas, a permission, and typed errors (`NOT_FOUND`, `CREDITS_EXHAUSTED`, `CONFLICT`, `BAD_REQUEST`, a cap error for phase B daily image caps).
2. Every change is additive: no existing procedure, field or enum value is removed or renamed; new fields on existing outputs are optional. Grep all consumer repos (backend, web, floor) for exhaustive switches, `Record<Enum, …>` maps and copied key lists over any enum you widen, and list each hit in your report (lesson 2026-10-01 A2).
3. Money is never in this contract; credits are integers; sizes are inches (numbers, never rounded); colors are `#rrggbb`.
4. ADR 0023 records: the design-lock rule (design pixels only ever composited by invai-imaging; no image model receives a request to draw or alter the design), the two-check drift rule for phase B (generated output must leave the print region unchanged; final composite compared to the source design, threshold set by imaging), disclosure rules (Etsy AI flag when any AI-generated image is used; XMP `contains-synthetic-performer` on every AI-generated image with a photoreal person; drawn templates are not AI and carry no AI disclosure), approval before any image leaves InvAI, credits per image, and that analysis/render/zip/push run on the queue. Also: bulk-upload CSVs carry no image URLs (keys aren't public), so images leave InvAI only by zip or Shopify push; image disclosures live in their own draft column (`image_disclosures`), not in `content`; the phase B approach from plan review item 8 (garment outline aligned check, base print box restored before compositing, design-lock SSIM; provider sizes upscaled to presets); retention for raw scenes and zips.
5. `pnpm typecheck && pnpm lint && pnpm test` in `invai-contracts` pass; contract tests cover each new schema's happy path and one rejection (bad hex, unknown garment, empty garments).

## Verification
- `cd invai-contracts && pnpm typecheck && pnpm lint && pnpm test 2>&1 | tail -n 40`
- `pnpm typecheck` in `invai-backend` and `invai-web` against the new contracts (their `node_modules/@invai/contracts` already links to `../../../invai-contracts`; don't re-link). Report each consumer's result; red consumer typecheck from an exhaustive map is a finding to list, not to fix.

## Out of scope
- Backend, web and imaging code. Phase B provider choice details (ai-engineer, T-27-1).

## Commit and report
- Commit only `invai-contracts/src/**` and your ADR + index row, message ending with the co-author line from your instructions. Don't push; only the tech lead pushes after the gate.
- Report: `invai-docs/waves/26/reports/T-26-1.md` (verify-and-report format, at most 60 lines); reply to the tech lead in at most 8 lines.
