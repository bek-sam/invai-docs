# T-27-3: Backend photos: lifestyle scene jobs with design lock, disclosures, caps, Shopify push job

| Field | Value |
|---|---|
| Wave | 27 |
| Scope ref | `product/scope.md#listing-photos` (SCR-008, phase B) |
| Spec | `specs/listing-photos.md` |
| Owner | backend-engineer (area: photos) |
| Reviewer | reviewer (fable) |
| Co-reviewers | security-reviewer (opus, tenancy/files/outbound); compliance-officer (sonnet, disclosures and image rules end to end); backend-foundation (sonnet) only if a migration is generated |
| Risk flags | tenancy, files, payments (credits/spend), marketplace-policy |
| Model | opus |

## Read first
- Your wave 26 card and code (`src/modules/photos/**`); ADR 0023; `waves/27/wave.md` "Agreed interfaces"; T-27-1 (`src/ai/images/**`), T-27-2 routes, T-27-4 `pushProductImages`.

## Owned paths (edit)
- `invai-backend/src/modules/photos/**` (not the QA acceptance file), `src/db/schema/photos.ts` + migration if needed (`pnpm db:generate --name photos_lifestyle`)
- Grant: `src/integrations/imaging/client.ts`, additive `photoSceneBase`, `photoSceneComposite` only

## Read-only paths
- `src/ai/**`, `src/modules/ai/**`, `src/integrations/channels/**`, everything else.

## Acceptance criteria
1. `createSet` with `lifestyle: {count}` (and `estimate`) includes scene images: `PHOTO_SCENE_CREDITS` each; refused up front with the cap error, `CREDITS_EXHAUSTED` or the platform cap error from `assertImageGenAllowed` before anything is enqueued.
2. A lifestyle job per scene image: scene base (imaging) → `getImageProvider().generateScene` (scene prompt from `buildScenePrompt`) → store the raw scene under the company prefix → `scene-composite` → on success save the image with `source=ai_scene`, `aiGenerated=true`, `containsSyntheticPerson` from the provider, `designLockScore`; XMP `contains-synthetic-performer` requested whenever a person is present. On `design_drift` or `region_changed`, regenerate once; a second drift marks the image `failed` with that reason, and the shop is not charged for it (spend for the provider call is still recorded). Retried jobs never call the provider twice for an image that already has a stored scene (idempotent on the image id) and never charge twice. Scene charge guard as in wave 26: lock the scene image row, charge when `charged_at IS NULL`, ref `{type: "photo_scene", id}`.
3. Disclosures: attaching a set with any approved AI image calls `attachPhotosToDraft` with `aiGenerated=true` (Etsy AI disclosure) and `syntheticPerformer` when any attached image has a person. The zip includes a `README.txt` per channel listing which files are AI-generated and which carry the synthetic-performer tag (en + es).
4. `photos.pushTargets` (now live): the shop's Shopify `listings` rows (tolerated foreign-table read of `src/db/schema/channels.ts` `listings`, with a doc comment), this design's first. `pushToShopify` (now live): `productRef.listingId` must be a listing of the same company, the same `connectionId` and channel shopify, mapped to `gid://shopify/Product/<channelListingId>`; approved images only; presigned URLs must outlive Shopify's async fetch (say the expiry); the connection must be a Shopify connection of the same company (another company's → NOT_FOUND); enqueues a job calling `pushProductImages` with presigned URLs, alt text and an idempotency key per (set, product, image); a retried job pushes nothing twice; result per image stored and returned by `getSet`. Audit row per push.
5. With the mock provider and mock Shopify (the defaults), the whole flow runs end to end on the dev DB; with `IMAGE_GEN_MOCK_DRIFT=1` in tests the drift path is shown.
6. Tests: drift → regenerate once → fail without charge; idempotent retry (provider called once); caps refuse before enqueue; push idempotency; tenancy for push and lifestyle.

## Verification
- `pnpm vitest run --reporter=dot src/modules/photos 2>&1 | tail -n 40`, then the full backend suite once with pipefail and a log (Bash timeout 600000).
- Dev DB exercise as in T-26-4 (API `:3142`, imaging `:8142`, worker, keys blanked, `IMAGE_GEN_PROVIDER` unset): add 2 lifestyle images to a set, approve, attach to a draft (show the disclosures), push to the seeded mock Shopify connection twice (second push skips), zip README. Refused: presser → FORBIDDEN. Record PIDs; stop them.

## Out of scope
- Web, provider internals, imaging internals, the Shopify adapter.

## Commit and report
- Commit own paths (grant: your functions only), co-author line; don't push. Report `invai-docs/waves/27/reports/T-27-3.md` (≤ 60 lines); reply ≤ 8 lines.
