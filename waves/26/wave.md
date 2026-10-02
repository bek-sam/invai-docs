# Wave 26: AI listing photos, phase A (template photo sets from the shop's own design)

- Dates: 2026-10-02 →
- Goal (user outcome): an office or designer person picks one of the shop's designs, picks garments (tee, hoodie, crewneck, tank) and blank colors, sees an analysis (recommended colors, contrast warnings, alt text, image order), gets a per-marketplace photo set rendered from drawn templates with the real design at its real print size, approves images, then downloads a zip or attaches them to an AI listing draft.
- Scope ref: `product/scope.md#listing-photos` (item 18, SCR-008, owner approval in chat 2026-10-02: "implement these all"). Not SCR-007: no image model ever makes or edits the design itself (decision 0022).
- Phase B (generative lifestyle scenes, Shopify image push) is wave 27 (`waves/27/wave.md`). The contract card here carries the phase B shapes too, so wave 27 needs no contract change.
- Plan reviewed by: product-manager (2026-10-02, approve, `reviews/plan-product-manager-r1.md`), architect (2026-10-02, changes-required with 9 card edits, `reviews/plan-architect-r1.md`; all 9 applied to the cards by the tech lead the same day, the architect said it approves once applied, no further reading round)
- Fences: mocks stay the default for every outside service; no real image generation in this wave; no outbound call except the existing AI gateway (gates run with AI keys blanked); no new paid service; at most 3 agents at once (reviewers included); never two owners on one file.

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| [T-26-1](T-26-1-photos-contract.md) Contract: `photos` namespace, enums and shapes for phases A and B, permissions; ADR | architect | fable | reviewer (opus) + backend-foundation (sonnet) + web-engineer (sonnet, consumer) | contract | planned |
| [T-26-2](T-26-2-imaging-garment-templates.md) Imaging: garment template library (4 garments × 4 views), real-size composite on the real blank color, underbase preview, channel presets with automated checks, XMP keywords, palette, zip | imaging-engineer | opus | reviewer (fable) + security-reviewer (opus, files) + compliance-officer (sonnet, marketplace image rules) | files, marketplace-policy | planned |
| [T-26-3](T-26-3-ai-design-analysis.md) AI: design analysis route (vision), deterministic mock, eval set, credits kind for photos, `attachPhotosToDraft` | ai-engineer | opus | reviewer (fable) | ai | planned |
| [T-26-4](T-26-4-backend-photos-module.md) Backend: `photos` module, tables with RLS, idempotent render jobs, credits per image, approval, zip export, attach to draft | backend-engineer (area: photos) | opus | reviewer (fable) + backend-foundation (sonnet, migration) + security-reviewer (opus, tenancy/files) | tenancy, files, migration, payments (credits) | planned |
| [T-26-5](T-26-5-web-listing-photos.md) Web: Listing photos screen (en/es, light/dark, 390 px) | web-engineer | sonnet | reviewer (opus) + product-designer (sonnet, new screen) | ui | planned |

Acceptance tests first (operating system step 3): a qa-engineer (sonnet) run after T-26-1 commits writes `invai-backend/src/modules/photos/photos.acceptance.test.ts` and `invai-web/e2e/listing-photos.spec.ts` from the ACs of T-26-4 and T-26-5 (red until built). The card reviewers check them; the gate runs them.

## Order and slots (at most 3 agents)
1. Plan review: product-manager (also writes SCR-008, scope item 18, spec `specs/listing-photos.md`, decision 0022) and architect (design review), in parallel.
2. T-26-1 (architect) and T-26-2 (imaging) in parallel; T-26-2 has no contract dependency.
3. After T-26-1 commits: T-26-4 (backend) starts and its first commit is the stubbed `photos` router + mount line (backend typecheck green again); T-26-3 (ai) starts and its first commit is its stubs **plus the `ai_photos` migration** (the `image_disclosures` column and ledger index), which must precede T-26-4's `photos_sets` migration in the journal. With T-26-2 still running that is 3 agents; QA acceptance tests start when a slot frees.
4. T-26-4 exercises for real once T-26-2 is committed. T-26-5 (web) after T-26-4's router is callable on the dev DB.
5. Reviews as each card finishes. Gate when all are approved.

## Agreed interfaces (stubs committed first)
Names are fixed here; the architect may refine shapes in T-26-1, and the ADR is the reference.

**Imaging (provider: imaging-engineer, consumer: backend-engineer through `src/integrations/imaging/client.ts`).** All new routes use the existing shared-secret auth, storage keys checked against the company prefix like `/mockup`, and the existing pixel caps.
- `POST /photo/palette {design_key}` → `{colors: [{hex, share}], light_share, dark_share, transparent_share}` (share 0..1, top 6 colors, alpha-weighted).
- `GET /photo/templates` → `[{garment, view, print_areas: {front?: {w_in, h_in}, back?: {...}}, drawn: true}]`.
- `POST /photo/render {design_key, design_width_in, design_height_in, placement: front|back, garment, view, blank_hex, underbase_preview, preset, out_key, xmp_subjects: string[]}` → `{key, width_px, height_px, format, print_box_px: [x,y,w,h], checks: {passes, failures: string[], background_pure_white: bool|null, fill_ratio, longest_side_px}}`.
- `POST /photo/zip {items: [{key, name}], out_key}` → `{key, bytes}`.
- Wave 27 (T-27-2): `POST /photo/scene-base` and `POST /photo/scene-composite` (see `waves/27/wave.md`).

**Presets** (`preset` values; imaging owns the numbers, compliance-officer checks them): `amazon_main` (pure white RGB 255 background, product fill ≥ 85% of the frame, longest side ≥ 1600 px, JPEG sRGB), `amazon_alt`, `etsy` (≥ 2000 px, up to 20 images per listing), `shopify` (square 2048), `tiktok` (square, white allowed), `walmart` (square ≥ 1500, white main). Each render returns its checks; a failed check is shown, never hidden.

**AI (provider: ai-engineer, consumer: backend-engineer).**
- `analyzeDesignForPhotos(companyId, userId, { designId, previewKey, palette, designName, tags }) -> DesignPhotoAnalysis` (runs inside a job on the `ai` queue, no transaction across the model call; charges credits through the gateway; mock is deterministic from palette + name).
- `attachPhotosToDraft(tx, ctx, { draftId, imageKeys: string[], aiGenerated: boolean, syntheticPerformer: boolean }) -> ListingDraft` (appends to `listing_drafts.mockupKeys`, stores disclosures in the new `listing_drafts.image_disclosures` column; refuses another tenant's draft with NOT_FOUND).
- Credit kinds `photo_image`, `photo_scene` (contract `CREDIT_KINDS` + backend mirror); constants `PHOTO_TEMPLATE_CREDITS = 1` per rendered composition, `PHOTO_SCENE_CREDITS = 10` per AI scene image (wave 27). Owner may change them (OI-25).

**Backend module `photos` (provider: backend-engineer, consumer: web-engineer):** the oRPC procedures from T-26-1.

## Integration gate
- [ ] Fresh reset, migrate, seed (AI keys blanked: `OPENAI_API_KEY= ANTHROPIC_API_KEY= caffeinate -i pnpm gate ...`)
- [ ] `run-golden-path` passes (API, browser, floor) plus the new acceptance spec
- [ ] Key screens looked at by the tech lead (listing photos en/es, 390 px, dark)
- [ ] Pushed to `main` (commits: …)

## Team metrics
| First-pass approvals | Canary caught? | Escaped defects | Reopened | Avg cycle time | Tokens per card |
|---|---|---|---|---|---|

## Log
- 2026-10-02 Plan written by the tech lead from the owner's approved analysis. Next free numbered wave: 26 (24–25 paused, decision 0019). Repos clean and level with origin; Docker healthy; 36 GB free; ports 3000/5173/5174/8000 free.
- 2026-10-02 OI-25 filed (enable real image generation; default: sample generator). Backlog B-272 (wave 26), B-273 (wave 27). Plan review started: product-manager (sonnet; also SCR-008, scope item 18, spec, decision 0022) and architect (opus), 2 agents.
- 2026-10-02 PM approve (docs 38400fb: SCR-008, scope item 18, spec ready, decision 0022). Architect changes-required, 9 items applied to cards (docs 70fc7be review, 4a25b98 plan); optional notes to B-274..B-276. T-26-1 (architect, fable) and T-26-2 (imaging, opus) started.
- 2026-10-02 T-26-1 built: contracts 9026680 (0.12.0, 143 tests), docs bd33f4a (ADR 0023, report). Backend typecheck red only on the expected router mount and CREDIT_KINDS mirror. Gap: contracts README rows (outside `src/**`; give the architect a README grant in its round 2 or a follow-up). T-26-4 (backend, opus) and T-26-3 (ai, opus) started; with T-26-2 that is 3 agents. T-26-1 reviews wait for a slot.
- 2026-10-02 T-26-2 built: imaging f282280 (159 tests; render 0.1–0.4 s; RSS up to 700 MB over a full set, B-278). Tech lead looked at the 16-view contact sheet: folded view hides the lower part of a large print (B-277). Reviewer r1 (fable) approve. Security co-review (opus) started; compliance co-review when a slot frees. T-26-4 stub router 30618a0, T-26-3 stubs + ai_photos migration d7e7b6c.
- 2026-10-02 T-26-2 security r1 changes-required (S-50 Medium: `/photo/zip` no byte caps); round 2 (imaging, sonnet) fixes only S-50. T-26-3 built (backend d7e7b6c, 1a9631d, 6ad243c; 1549/1550, `ratelimit.test.ts` failed once under load, passes alone, B-280); reviewer r1 started. T-26-4 built (backend 30618a0, 5930d59, migration 0040; 1550/1550; real run: 16/16 rendered, 8 ledger rows, duplicate job charged nothing); reviewer r1 started. QA acceptance tests slipped behind the build for slot reasons: QA writes them before T-26-5 starts (deviation from step 3, recorded for the retro).
- 2026-10-02 T-26-2 r2 (imaging 9d66957, S-50 caps; 162 tests). T-26-3 reviewer r1 approve. T-26-4 reviewer r1 approve (mutation proof: removing the `charged_at` guard turns the run-twice test red); optional notes: attach accepts a draft of another design (queued as T-27-3 AC6 before that card starts), overdraw ≤ one set, analysis labelled `photo_image` (B-281). Running: QA acceptance tests, backend-foundation (T-26-1/3/4 co-reviews), security (T-26-2 r2 + T-26-4 r1). The guard refused a heredoc docs append that quoted a card id (B-268 family); docs edits go through Edit.
- 2026-10-02 QA acceptance tests: backend e32f9c5 (16/16 green on the built module), web a9a5dc6 (`e2e/listing-photos.spec.ts`, smoke route). backend-foundation approve on T-26-1, T-26-3, T-26-4. T-26-1 reviewer (opus) approve (README rows gap: follow-up). T-26-2 security r2 approve (S-50 fixed). T-26-4 security r1 changes-required (S-51 Medium: credits not reserved across open sets; marker test f86184b). T-26-4 round 2 (backend, opus) started with a one-word grant in `security.test.ts` (`it.fails` → `it`). T-26-5 (web, sonnet) building on the :3000 slot. Compliance co-review of T-26-2 started.
- 2026-10-02 T-26-2 compliance r1 approve (follow-ups B-282). T-26-1 web-engineer co-review approve. T-26-4 r2 built (backend 790986f, S-51: open commitments held, claim/charge refuse instead of going negative; 1574 tests). A coordinator relay reported 4 red tests from a mid-edit snapshot of r2; checked: the tree is clean and 790986f is committed with the suite green. Security r2 approve (S-51 fixed; extra concurrency test 47a54b3; new Low queued as T-27-3 AC8; `estimate.canAfford` queued as T-27-3 AC7). Test-code review of QA and security test commits started (reviewer, sonnet).
- 2026-10-02 Test-code review approve (`reviews/tests-reviewer-r1.md`). Flaky under load: market AC30 and ratelimit (B-283). T-26-5 built (web 66ab0cb; full web E2E 34 pass, the new spec failed on its own selectors); QA selector fix 760d6f4. T-26-5 reviewer r1 changes-required (4: analysis poll loop, zip keyed on count, signed-URL storms, raw English/390 px) and product-designer r1 changes-required (2: hidden credits reason, 2 columns at 390 px). Round 2 (web, sonnet) fixes those 6; the backend half of the poll loop (a failed analysis is re-enqueued on any call) is queued as T-27-3 AC9 rather than a third T-26-4 round, because the web fix stops the loop.

## Retro
- What slipped:
- Lessons added (links to `team/lessons.md`):
