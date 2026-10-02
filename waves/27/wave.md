# Wave 27: AI listing photos, phase B (generated lifestyle scenes with the design locked, Shopify image push)

- Dates: after wave 26's gate
- Goal (user outcome): a shop adds lifestyle scenes to a photo set; the scene and garment come from an image-generation provider (a deterministic mock by default), the shop's real design is composited by invai-imaging and checked for drift; AI images carry the right disclosures; approved images can be pushed to a Shopify product.
- Scope ref: `product/scope.md#listing-photos` (SCR-008, owner approval 2026-10-02). Decision 0022 (no model draws the design), ADR 0023.
- Fences: **real image generation stays off.** The OpenAI image provider runs only when `IMAGE_GEN_PROVIDER=openai` and a key exist; nobody on the team sets that flag. OI-25 asks the owner. Every test, review and gate runs on the mock with AI keys blanked. No real Shopify call (no Shopify keys exist; the mock adapter answers). At most 3 agents at once.
- Plan reviewed by: product-manager (approve) and architect (changes-required, 9 edits applied) together with wave 26, 2026-10-02 (`waves/26/reviews/plan-*-r1.md`)

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| [T-27-1](T-27-1-image-gen-provider.md) Image-generation provider: interface, deterministic mock (default), OpenAI GPT Image behind `IMAGE_GEN_PROVIDER=openai`, per-shop daily cap + platform spend cap before each call, scene prompt rules | ai-engineer | opus | reviewer (fable) + security-reviewer (opus, new outbound provider) | ai, outbound, payments (spend) | planned |
| [T-27-2](T-27-2-imaging-scene-lock.md) Imaging: scene base + edit mask, scene composite with displacement, two design-lock checks (region unchanged, SSIM vs source), XMP | imaging-engineer | opus | reviewer (fable) + security-reviewer (opus, files: untrusted model output) | files, marketplace-policy | planned |
| [T-27-3](T-27-3-backend-lifestyle-and-push.md) Backend photos: lifestyle jobs (base → provider → composite → lock check → reject on drift), disclosures, credits/caps, Shopify push job | backend-engineer (area: photos) | opus | reviewer (fable) + security-reviewer (opus) + compliance-officer (sonnet, disclosures and marketplace image rules) | tenancy, files, payments, marketplace-policy | planned |
| [T-27-4](T-27-4-shopify-image-push.md) Shopify adapter: push product images (mock + live GraphQL), idempotent | integrations-engineer | opus | reviewer (fable) + security-reviewer (opus, outbound to the shop's store) | outbound, idempotency | planned |
| [T-27-5](T-27-5-web-lifestyle-and-push.md) Web: lifestyle scene options, AI and drawn badges, disclosure notes, push to Shopify, cap messages | web-engineer | sonnet | reviewer (opus) | ui | planned |

## Order and slots
1. T-27-1, T-27-2, T-27-4 in parallel (no shared files). T-27-1 commits its stub (`getImageProvider`, `assertImageGenAllowed`) first.
2. T-27-3 after all three are committed. T-27-5 after T-27-3's jobs run on the dev DB.
3. Reviews as each card finishes; gate when all are approved.

## Agreed interfaces
- `getImageProvider(companyId) -> ImageProvider` and `ImageProvider.generateScene({ baseImage: Buffer, mask: Buffer, prompt: ScenePrompt, sizePx }) -> { image: Buffer, model, costCents, containsPerson }` in `invai-backend/src/ai/images/` (ai-engineer). Mock: deterministic from the prompt and base hash, never touches masked-off pixels, `costCents = 0`, model `mock-image`. A test hook `IMAGE_GEN_MOCK_DRIFT=1` (test env only, refused in production) makes the mock alter the print region so the drift path can be exercised.
- `assertImageGenAllowed(tx, companyId, count) -> void` (ai-engineer): per-shop daily image cap (`IMAGE_GEN_DAILY_CAP_PER_SHOP`, default 30), platform daily AI spend cap (`assertSpendAvailable` with the estimated cost), credits (`PHOTO_SCENE_CREDITS` each); and `recordImageGen(...)` to log cost and spend after each call.
- `buildScenePrompt(analysis, sceneKind, garment, blankName) -> ScenePrompt` (ai-engineer): refuses brands, logos, celebrities, real people's likeness, children, text in the scene; always asks to leave the garment's print area blank.
- Phase B lock approach (plan review item 8; OpenAI GPT Image masks are guidance only and output sizes are fixed at 1024², 1536×1024, 1024×1536): check 1 is "garment outline aligned" (register output to base, compare an edge map in a ring around the print box), the base's blank print-box pixels are restored before compositing, check 2 compares the printed region to the source design; the provider-size output is upscaled to the preset size (documented).
- Imaging (T-27-2): `POST /photo/scene-base {garment, view: on_model_white|lifestyle_base, blank_hex, size_px, out_key, mask_out_key}` → `{key, mask_key, print_box_px}`; `POST /photo/scene-composite {scene_key, base_key, print_box_px, design_key, design_width_in, design_height_in, placement, blank_hex, preset, out_key, xmp_subjects}` → `{key, checks: {passes, failures, region_unchanged_score, design_lock_score}}`. Thresholds live in imaging and are reported.
- Shopify (T-27-4): `ChannelAdapter.pushProductImages?(conn, { productGid: "gid://shopify/Product/<id>", images: [{url, alt, filename}], idempotencyKey }) -> { pushed: [{filename, mediaId}], skipped: [...] }`. The contract's `productRef = {listingId}` points at a row of the backend `listings` table (same company, same connection, channel shopify); T-27-3 maps `listings.channelListingId` to the gid (plan review item 7).

## Integration gate
- [ ] Fresh reset, migrate, seed, AI keys blanked, `IMAGE_GEN_PROVIDER` unset
- [ ] `run-golden-path` passes (API, browser, floor) plus the listing-photos specs
- [ ] Key screens looked at (lifestyle images with badges, push dialog, en/es, 390 px)
- [ ] Pushed to `main`

## Team metrics
| First-pass approvals | Canary caught? | Escaped defects | Reopened | Avg cycle time | Tokens per card |
|---|---|---|---|---|---|

## Log

## Retro
- What slipped:
- Lessons added:
