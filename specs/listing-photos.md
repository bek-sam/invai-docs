# Spec: AI listing photos

- Scope ref: `product/scope.md#listing-photos` (item 18)
- Decision: `decisions/0022-listing-photos-design-lock.md` (design pixels only ever composited by invai-imaging); owner approval in chat, 2026-10-02, quote "implement these all"; `product/scope-changes/SCR-008-listing-photos.md`
- Not SCR-007 (`scope-changes/SCR-007-original-design-pipeline.md`, still open under `owner-inbox.md` OI-17): that request is about an image model **inventing new artwork** from a niche brief. This feature only **photographs a design the shop has already uploaded**. The two don't overlap and this spec doesn't reopen decision 0006.
- Research: `research/16-growth-opportunities.md` §2 and §5.2; `research/10-marketplace-engineering-rules.md` §4–5 (channel image rules); `research/02-competitors.md`
- Depends on: existing design catalog (`catalog` module), AI listing drafts (`ai.listings.*`, scope item 10), AI gateway and credits
- Status: ready (2026-10-02). Wave 26 (phase A), wave 27 (phase B). Task cards: `waves/26/T-26-{1..5}.md`, `waves/27/T-27-{1..5}.md`.

## Problem and evidence
Shops need photos of their shirt before they can list it anywhere, and today InvAI gives them one flat, tinted tee mockup (`invai-imaging/app/mockups.py`) — no hoodie, no back view, no on-model shot, nothing sized or checked for a specific marketplace. Shops either skip proper photos (hurting conversion) or make them outside InvAI, which breaks the "orders in, listing out" promise at exactly the step buyers see first.

Evidence, stated honestly:
- `research/16-growth-opportunities.md` §2, "Features competitors have that we lack" ranks **"Mockup creation (5 products). We have flat tee mockups only"** as gap #1 of 10 (line ~147), ahead of invoicing, proof-approval portals and QuickBooks sync. The same research file's design-pipeline section (§5.2, lines ~420–440) already assumes a "mockups" step between design approval and listing draft.
- Competitors with mockup or AI-photo features: Pythias (AI mockups, claimed), MyDesigns (AI listings and mockups), Taivo/Printavo (Mockup Creator), YoPrint (Mockup Creator) — `research/02-competitors.md`, `research/16` §2.
- **0 pilots have asked for this** — no pilot is live yet. This is an owner-initiated bet on a visible, sourced competitive gap, not a pilot-confirmed pain, and the spec is honest about that (same standard as `specs/weekly-digest.md`).
- The owner approved building it, in chat, 2026-10-02, quote: "implement these all."

## Users
- **owner, admin, office, designer**: can analyze a design, choose garments/colors/channels, generate a photo set, approve or reject images, download a zip, attach to an AI listing draft, and (phase B) push approved images to a connected Shopify store. Same permission tier as managing AI listing drafts today.
- **presser, packer, receiver, vendor**: no access (refused `FORBIDDEN`; no nav entry). They don't manage listings.

## Segments
- **Small** (1–3 people, self-serve): the main beneficiary — today they either skip photos or pay a freelancer. Works with no outside approval: everything in phase A, and phase B's mock scenes, run with no marketplace or provider keys.
- **Mid** (pilot target): wants photo sets across 3–5 marketplaces at once; the per-channel presets and the zip-by-channel naming exist for this.
- **Large**: same tool; multi-location/brand variety is handled by running the flow per design, same as any shop. No segment-specific cut.

## In scope
### Phase A (wave 26)
1. **Design analysis** (AI, vision): recommended blank colors with reasons, deterministic contrast warnings (computed in code from the palette, not the model, per `T-26-4` AC2), detected text, style/niche description, alt text per channel, and a suggested image order per channel.
2. **Drawn garment templates**: tee, hoodie, crewneck, tank; views front flat, folded, back, on-model-on-white. Templates are drawn by code in `invai-imaging` (no stock photography, no uncleared fonts).
3. **Real-size, real-color composite**: the shop's design file is placed on the template at its true print size (inches) and the template is filled with the exact blank hex the shop picked; a white-underbase preview shows what the print looks like on a dark blank.
4. **Channel presets with automated, visible checks**: Amazon main (pure white background, product fill ≥ 85%, longest side ≥ 1600 px), Amazon alt, Etsy (≥ 2000 px, up to 20 images per listing), Shopify (square 2048), TikTok (square, white allowed), Walmart (square, ≥ 1500 px, white main). A failed check is shown to the shop in plain words, never hidden.
5. **Disclosures on drawn templates**: an on-model-on-white template is an illustration, not a photo — it carries no AI disclosure (it isn't AI), but is flagged `illustration_not_photo` against Amazon's main-image rule (which wants an actual photograph).
6. **Credits**: charged once per rendered composition (garment × view × color), not per channel derivative.
7. **Approval**: a person must approve an image before it can be downloaded or attached anywhere.
8. **Zip download**, grouped by channel; **attach approved images to an AI listing draft** (scope item 10).
9. Web screen, English and Spanish.

### Phase B (wave 27)
10. **Image-generation provider**, gated: a deterministic mock by default; OpenAI GPT Image only when the owner sets `IMAGE_GEN_PROVIDER=openai` (`owner-inbox.md` OI-25). Per-shop daily image cap and a platform daily AI-spend cap, checked before every call.
11. **Lifestyle scenes**: the provider draws a scene and garment from a *blank, masked* base (no design bytes sent to the provider); `invai-imaging` composites the shop's real design into the masked print area afterward.
12. **Design-lock drift checks**: two checks per phase-B composite (print-region-unchanged, SSIM against the source design); a failed check rejects the image before the shop sees it as usable.
13. **Disclosures on AI scenes**: Etsy AI-use disclosure on the listing when any AI-generated image is attached; XMP `contains-synthetic-performer` on any photoreal AI-generated person.
14. **Shopify image push**: approved images can be pushed to a connected Shopify product (mock adapter locally; live GraphQL when Shopify keys exist). Every other channel stays zip-download until that channel's adapter and approval exist (scope fence; see `decisions/0006-v1-cuts.md` and item 18's fences).

## Out of scope
- Any image model drawing, redrawing or editing the shop's design pixels, in either phase (decision 0022). This is the hard line between this feature and SCR-007.
- AI-invented designs from a niche brief (SCR-007, still open under OI-17).
- Real OpenAI image calls before the owner answers OI-25; every review, test and gate runs on the mock.
- API image push to Etsy, Amazon, TikTok or Walmart (they stay zip-download until each channel's own API adapter and marketplace approval land — see scope items 2 and "MVP: out").
- Video, GIFs or A+ content modules.
- Any change to the existing flat-tee `/mockup` endpoint's current behavior (it keeps working unchanged).
- Automatic listing or price changes from a photo set (approval and attach are explicit, person-driven actions, consistent with the market-signals/digest fence "no automatic listing changes").

## Flow
### Phase A
1. Shop opens **Listing photos** (nav, next to AI listings) or clicks through from a design's detail page (design preselected).
2. **Step 1 — pick a design** from the shop's own uploaded designs (searchable, thumbnails).
3. **Step 2 — analysis**: InvAI shows style/audience, detected text, recommended blank colors with reasons, and plain-language contrast warnings ("Light art on a light shirt is hard to see. Try Black or Navy."). A mock (sample) analysis is labelled as sample.
4. **Step 3 — choose**: garments, blank colors (shop's own colors plus recommended ones), views, channels. A live estimate ("N photos, M credits") updates as choices change; generate is disabled with a reason when credits are short.
5. Generate enqueues render jobs; **step 4 — results** show a grid grouped by channel and slot, each with its check result in plain words, updating as renders finish.
6. Shop **approves** images (one by one or "approve all passing"), or **rejects**.
7. Shop **downloads a zip** (by channel) and/or **attaches approved images to an AI listing draft**.

### Phase B (adds to step 3/4)
8. Shop optionally adds **lifestyle scenes** (a count and, optionally, scene kinds) alongside or instead of templates.
9. Each lifestyle image: provider draws a blank, masked scene → `invai-imaging` composites the real design into the print area → two design-lock checks run → pass: image appears for review, marked "AI scene" with its disclosure note; fail: image is marked failed/rejected automatically and never shown as usable (the shop can retry).
10. Approved images can additionally be **pushed to Shopify** (pick the connection and product); other channels still use the zip.

## Marketplace rules and their sources
Checks and disclosures in this spec are built to the following, each cited; several 2026 policy specifics for Amazon/Etsy image rules are sourced from third-party trade blogs rather than the platforms' own pages (`research/10-marketplace-engineering-rules.md` §4, ~line 239, flags this directly), so compliance-officer re-verifies exact wording against each platform's current, official help pages before anything ships to a real shop:
- **Amazon main image, pure white background / fill ratio / minimum pixels**: long-standing Amazon Image Requirements (seller central help), reflected in `research/10` §4. `contains-synthetic-performer` XMP keyword on photoreal AI-generated people, effective 2026-07-22, sourced from a third-party blog (`research/10` ~line 239, `[3P]`) — compliance-officer to confirm against Amazon's own current policy page before this ships beyond mocks.
- **Etsy AI-use disclosure**: Etsy's Creativity Standards (2025-06-10) allow seller-prompted AI content with disclosure; `research/16` §5.2 cites Etsy's own creativity page as the source for "seller-prompted AI art with disclosure" being allowed. **Etsy's own help content says mockups of a seller's own printed original design are fine** and does not itself require an AI disclosure for a photographic mockup of a physical, human-made product — the disclosure obligation here is specifically about *generated* scene/image content (phase B), not about photographing a design the shop made (phase A). This distinction is load-bearing for this spec and should be re-checked by compliance-officer against Etsy's current seller policy page before phase B disclosures ship to a real shop.
- **Etsy image count and minimum size**: up to 20 images per listing, ≥ 2000 px recommended — Etsy seller help (image requirements).
- **Shopify, TikTok, Walmart presets**: platform-stated image guidelines (square formats, minimum pixel sizes); exact current numbers to be reconfirmed by compliance-officer at review (`listing-compliance-check`) since this spec's numbers come from the tech lead's wave plan, not a fresh pull.

## Credits
- `PHOTO_TEMPLATE_CREDITS = 1` per rendered composition (garment × view × color); channel derivatives of the same composition are free.
- `PHOTO_SCENE_CREDITS = 10` per AI-generated lifestyle image (phase B).
- These are starting values the owner may change (`owner-inbox.md` OI-25). Pricing of credits themselves is not this spec's call (`pricing-experiment` territory if it ever needs testing); this spec only fixes the *behavior* (charge once per composition, in the same transaction that marks it rendered, never twice on retry).

## Acceptance criteria (Given/When/Then)
These are written to be consistent with the already-written task cards (`waves/26/T-26-*.md`, `waves/27/T-27-*.md`); where a card's AC is more specific (exact thresholds, exact file shapes), the card's wording governs and this spec states the user-observable behavior it must produce.

1. **Happy path, phase A.** Given an office user signed in to a seed shop with an uploaded design, when they pick the design, choose 2 garments × 2 colors × 2 views for Amazon and Etsy, and generate, then a photo set is created, images render with real-size design placement on the exact blank hex, each image shows its channel check result, and credits are charged once per composition.
2. **Analysis contrast warning.** Given a design whose dominant color is light, when the shop picks a light blank color, then the UI shows a plain-language contrast warning with the WCAG-style ratio computed in code (not claimed by the model).
3. **Approval gate.** Given rendered images in a set, when the shop tries to download a zip or attach to a draft before approving any image, then InvAI refuses with a message naming how many images still need approval; after approving, the same actions succeed only for the approved images.
4. **Credits exhausted.** Given a shop whose AI credit balance is below the estimate for the chosen compositions, when they try to generate, then `createSet` is refused with `CREDITS_EXHAUSTED` and the UI shows the shortfall before any job runs.
5. **Unapproved can't leave.** Given a mix of approved and rejected images in a set, when the shop exports a zip or attaches to a draft, then only approved images are included; the response/UI names the excluded count and reason.
6. **Design larger than the print area.** Given a design file whose print-size dimensions exceed a garment's print area, when it is composited, then the image is still produced (scaled down to fit, never scaled up to overflow) and its checks report `design_larger_than_print_area` so the shop sees it, not a silent clip.
7. **Missing back print file.** Given a design with no back print file, when the shop selects "back" as a view, then that composition is not offered (not silently produced as a wrong image) and the estimate excludes it.
8. **Dark blank underbase preview.** Given a blank color under the documented darkness threshold, when `underbase_preview` is requested, then semi-transparent design pixels render against white underbase instead of the raw blank color; a light blank with the same flag changes nothing.
9. **Marketplace/provider outage (imaging down).** Given invai-imaging is unreachable when a render job runs, when the job executes, then the affected image is marked `failed` with a readable reason, the set still reaches `ready` counting the failures (or `failed` if nothing rendered), and nothing is charged for failed images.
10. **Idempotent create.** Given a `createSet` call with an `idempotencyKey` already used for that shop, when it is called again with the same key, then the same set is returned and no second render job is enqueued.
11. **Retried render job doesn't double-charge.** Given a render job that is retried (crash or redelivery) after already charging credits for a composition, when it runs again, then the ledger shows exactly one charge for that composition (tested by running the job twice).
12. **Cancel/irrelevant states.** Given a design is deleted or archived after a photo set references it, when the shop reopens that set, then previously rendered images and their approvals remain visible and usable (zip/attach still work for already-rendered, approved images); no new renders can be started from a deleted design.
13. **Tenant isolation.** Given a design id, draft id or set id belonging to another company, when any `photos.*` procedure is called with it, then the response is `NOT_FOUND` (never a silent empty result or another tenant's data).
14. **Permission refusal.** Given a user with the `presser` role, when they call any `photos.*` procedure or open the Listing photos screen, then they are refused (`FORBIDDEN` / no nav entry / no-access page).
15. **Phase B: drift rejected.** Given a lifestyle render where the test-only drift hook (`IMAGE_GEN_MOCK_DRIFT=1`, non-production only) alters the print region, when the design-lock checks run, then the image is rejected before it can be approved, with a reason the shop can see ("design didn't match, try again"), and no credits beyond the attempted charge are lost twice on retry.
16. **Phase B: caps.** Given a shop at its daily AI-image cap (`IMAGE_GEN_DAILY_CAP_PER_SHOP`), when they request another lifestyle image, then the request is refused with a plain message naming the cap and when it resets; template images (phase A) are unaffected by this cap.
17. **Phase B: provider off by default.** Given `IMAGE_GEN_PROVIDER` is unset (the default, and the state of every test and gate run), when a lifestyle image is requested, then the deterministic mock runs — cost $0, clearly labelled as a sample scene — and no outbound call is made.
18. **Phase B: disclosures stick.** Given a draft that received an AI-generated image (disclosure set), when template (non-AI) images are attached to the same draft afterward, then the AI disclosure is not cleared.
19. **Phase B: Shopify push, idempotent.** Given an approved image already pushed to a Shopify product, when the same push is retried with the same idempotency key, then no duplicate image is created on the product.
20. **Scale.** Given a set of 48 compositions (the maximum `createSet` allows) for a mid-size shop, when it renders, then the set completes without timing out the request (rendering is job-based, never in the request) and the list screen doesn't fire a presigned-URL request per image (only the lead thumbnail per set).

## Success metrics
- **Adoption**: share of shops with at least one design that generate a photo set within 14 days of first use, target ≥ 30% of active shops once pilots are live (baseline: 0, feature doesn't exist yet). Needs a `define-metric` pass once pilots run; not yet a tested SQL query.
- **Approval-to-use**: share of rendered images that get approved (vs rejected), as a proxy for template/analysis quality; no target set yet — first few shops set the baseline.
- **Check pass rate**: share of Amazon-main renders that pass `background_pure_white` and `fill_ratio ≥ 0.85` on the first try, tracked to catch a bad template before a shop notices.
These are proposed, not yet defined per `define-metric` (no pilot data exists to baseline against); data-analyst picks this up at its normal trigger (first live pilot).

## Dependencies and outside approvals
- No outside marketplace approval is required for phase A or the mock-based phase B (everything runs on existing CSV/mock infrastructure plus the zip/attach flows already in scope).
- Phase B's real OpenAI calls need the owner to set `IMAGE_GEN_PROVIDER=openai` and hold a key (`owner-inbox.md` OI-25); until then the mock is the only path and that's by design, not a blocker.
- Phase B's live Shopify image push needs a live Shopify connection with write scope, already covered by the existing Shopify API adapter (scope item 2); no new approval beyond what that adapter already has.

## Open questions
- Exact current pixel/format rules for Shopify, TikTok and Walmart image presets: who answers — compliance-officer, via `listing-compliance-check`, before wave 26's gate.
- Whether Etsy's disclosure applies per-listing or per-image when a draft mixes template and AI-scene images: who answers — compliance-officer, confirmed against Etsy's current seller policy page (not the third-party source this spec relies on today).
- Final credit prices (1 / 10) — these are starting values; who answers — the owner, if a future pricing signal suggests they're off (not blocking this wave).
- Whether a future wave should let a shop choose its own scene style library (beyond the kinds the AI suggests) — who answers — product-manager, after the first few shops use phase B.

## Review log
- 2026-10-02: drafted by product-manager, written against the tech lead's already-authored cards (`waves/26`, `waves/27`) so acceptance criteria are consistent with what's being built, not a separate ask. product-designer, qa-engineer and customer-success reviews: pending (to be logged by the tech lead as wave 26 proceeds, per the operating system's review order; this spec is handed off `ready` so the wave is not blocked on the review round, and any blocking finding comes back as a card note, not a wave-stopping gate).
