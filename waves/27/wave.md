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
- 2026-10-03 Wave 26 gate passed and pushed (`waves/26/wave.md`). The same tech lead runs wave 27 because the owner's task asked one tech lead to run both waves; a deviation from "fresh tech lead per wave" (decision 0018), recorded here. Cards unchanged since the plan review except queued ACs on T-27-3 (AC6–AC9, from wave 26 reviews). T-27-1 (ai, opus), T-27-2 (imaging, opus), T-27-4 (integrations, opus) start in parallel; ports 31xx/81xx per card; gate slot free.
- 2026-10-03 T-27-4 built (backend 3f4deae; `productUpdate` media, API 2026-07, dedupe by filename/alt; `write_products` added; 1588 tests). OI-26 filed (keep `write_products` when the Shopify app is registered). Reviewer r1 (fable) started; security co-review when a slot frees.
- 2026-10-03 T-27-4 reviewer r1 changes-required: media still processing is matched by alt text, but every image of a set shares one alt, so several new photos collapse into one "already pushed" (proven by probe). Round 2 (integrations, opus) adds a per-image marker. Security co-review after round 2.
- 2026-10-03 T-27-4 r2 (backend 31fb391: per-image `[img <8 hex>]` tag at the end of the alt text; 81 channel tests). Reviewer r2 approve (probe re-run). Non-blocking: shoppers' screen readers hear the tag (B-286). Security co-review started.
- 2026-10-03 T-27-1 built (backend 83ca734 stubs, 927ad35, cfd35ea; 163 ai tests, scene-prompt evals 14/14 mock; full suite only red on T-27-4 tests committed mid-run, 18/18 alone). Model `gpt-image-2` medium, about $0.10–0.11/image (checked 2026-10-03): OI-25's cost estimate updated (was $0.02–0.06). Reviewer r1 (fable) started. T-27-3 notes from the builder: job lock longer than the 120 s image timeout, pass held credits, use `err.retryable`.
- 2026-10-03 T-27-4 security r1 changes-required: S-52 (Medium) a 5xx retry re-sends the media mutation without re-reading media, so a gateway error after Shopify saved the photos doubles them on the live product (marker test 2075e12). The integrations-engineer fixes only S-52 for the security reviewer's round 2 (that reviewer's second round, within the 2-round limit; the primary reviewer already approved r2). Grant: the one-word `it.fails` → `it` in `shopify/security.test.ts`.

## Retro
- What slipped:
- Lessons added:
