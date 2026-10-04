# Swap drawn shirts for photographed bases

InvAI's listing photos look nothing like top Etsy or Amazon listings because the shirt in every picture is drawn by code, not photographed. The fix is not a bigger AI budget. InvAI should build a **library of real photographic base images** (blank Comfort Colors 1717, Bella+Canvas 3001 and Gildan 5000 tees, hoodies and sweatshirts, shot flat, folded, on a standing model and in lifestyle settings, each made once), and then **paste each shop's exact design onto those photos with deterministic displacement-map compositing**. Displacement-map compositing means bending the flat design along the photo's folds and shading it with the photo's own light, without any AI model touching the design. That gives real-photo realism at about a tenth of a cent per image. It also keeps the design pixel-exact, which decision 0022 requires, and it passes Amazon's rule that the main image for adult apparel must be a real photo of a standing model. Generative AI still has a role, but a narrow one: making extra base photos once (models and lifestyle scenes), segmenting and mapping the folds of new bases, and optional per-design lifestyle scenes sold at a price that covers their cost. One master set of 10–12 images feeds all five marketplaces through cropping and slot rules, so a design × 5 colors × 5 channels costs about **$0.07–0.10** template-only and **$0.20–0.39** with two AI scenes. The fully generative route costs **$3.30–7.20** for the same job, and it breaks the design lock. On gang sheets InvAI is already ahead of the market (rectangle nesting at 86–91% film use, a scannable QR code under every transfer). The real gaps are file checks: thin lines and small text, size-aware placement presets, and an opt-in AI upscaler. Nearly all of that is plain code, not AI. Five owner decisions gate the plan, and the most important is amending 0022's "drawn by code, never stock art" wording so real photographs can serve as bases.

## Three structural causes make today's photos look drawn, not shot

The owner's complaint is accurate, and it comes from the system's design, not from a bug. InvAI has two image pipelines. The old `/mockup` endpoint draws a single flat tee from Bezier curves (smooth curves defined by control points) and pastes the design into a fixed chest box. The listing-photo pipeline from waves 26–27 (`invai-imaging/app/photos.py`, `garments.py`, `scenes.py`) is far more capable, but it shares the same root. In `garments.py:4-7`, every garment is "drawn by code from bezier paths, in inches". Folds are hand-placed strokes, and a single soft ellipse stands in for studio light. The "model" is a faceless grey mannequin built from polygons. A search of `invai-imaging` found **no photographic or 3D garment asset anywhere**. The contract's `PhotoImageSource` enum allows only `template` or `ai_scene`, so the system has no way to take in a camera photo of a garment.

Three causes stack on top of each other. **First**, the phase-A template garment is vector art with painted shading, so there is no fabric weave, no real drape and no camera optics (depth of field, sensor grain, lens falloff). That holds even for the "real" template photos, and OI-25 does not change it. **Second**, phase-B lifestyle scenes come by default from a deliberately crude mock generator: a two-color gradient, one light spot and two to four colored squares (`invai-backend/src/ai/images/mock.ts:28-82,198-206`). That is because OI-25, which would switch on OpenAI `gpt-image-2`, is still unanswered. **Third**, even with the real provider on, the design-lock step repaints the print band with the exact blank color and relights it (`scenes.py:629-636,750-828`). So the AI-drawn shirt gets a flat patch where the print sits, and the backlog already logs the side effects. **B-287** records that scene lighting turns a white tee beige and that hoodie drawstrings show through the print. **B-289** records that a "flat lay" request still shows a figure, because no flat-lay base exists.

This matters commercially. Mockup makers call wrong print placement "the first thing that gives an amateur mockup away" ([Spocket](https://www.spocket.co/blogs/t-shirt-design-size-and-placement-tips-for-printify)). The most-used blanks in best-selling Etsy mockups are **Comfort Colors 1717, Bella+Canvas 3001 and Gildan 5000**, usually shown folded or laid flat on a styled surface ([mockupmuse](https://mockupmuse.com/blogs/pod-growth-academy/best-tshirt-mockups-etsy)). Buyers compare InvAI output against real photographs of those exact shirts. InvAI's own code also flags a compliance problem: drawn templates fail Amazon's main-image "photo, not illustration" check (`photos.py:286-302`). So today a shop cannot produce a compliant Amazon main image at all.

## Real photographs as bases, exact designs composited on top

### Displacement compositing is cheap, exact and mostly already written

The technique pros have used for years in Photoshop mockups works like this. A grayscale **displacement map** pushes the flat design up or down so it follows the folds (50% gray leaves it in place). Then a **multiply** layer adds the fabric's shadows and a **screen** layer adds its highlights ([Nick Cassway](http://nickcassway.com/designblog/?p=2343)). The same effect runs without Photoshop, as in Fred Weinhaus's public ImageMagick "TSHIRT" script, which uses a lighting image and a displacement image ([fmwconcepts](http://www.fmwconcepts.com/imagemagick/tshirt/index.php)). Hosted mockup APIs sell exactly this, for example Dynamic Mockups at about **$0.051 per mockup credit** ([Dynamic Mockups](https://dynamicmockups.com/pricing/)). Vendors like Mockuplabs let a seller turn their own product photo into a "reusable custom mockup" for many designs ([Mockuplabs](https://www.mockuplabs.ai/mockup)).

The key point for InvAI is that **`photos.py` `compose()` already does every step except one**. It places the design at its true physical size, displaces it along a height map, shades it with multiply and screen, and previews the white underbase (the layer of white ink printed under colors on dark shirts). The missing step is that its maps come from Bezier drawings instead of from a photograph. Swapping the source of the base and its maps is a contained imaging change, not a rewrite. The per-image cost stays at CPU compute, roughly a tenth of a cent (an estimate, not measured). The design is never regenerated, so the existing SSIM drift check (structural similarity, a score of how alike two images look) stays trivially green.

Each base becomes a small bundle of files. The bundle holds the photo; a garment mask; a print-area mapping (four or more anchor points that tie real inches on the shirt to pixels, calibrated from the blank's published size chart); a displacement map and a shading map derived from the photo's own brightness inside the garment; a highlight map; and an **occlusion mask** for anything that sits in front of the print, such as hair, an arm or hoodie drawstrings. The occlusion mask is how B-287's drawstring bleed gets fixed. Bases are shot or generated for the top 6–8 colors of each blank. The long tail of colors is recolored from the nearest shot color with a calibrated lookup table, and a **deltaE check** (a standard measure of how different two colors look) rejects drift. That matters because the Comfort Colors community has publicly warned that mockup tools render 1717 colors wrong ([MyDesigns community](https://community.mydesigns.io/c/general-discussions/comfort-colors-mockup-colors-are-wrong-please-double-check-your-listings)).

### Where the bases come from: five options compared

| Option | Realism | Design fidelity | Marketplace fit | Cost | Fit with decisions |
|---|---|---|---|---|---|
| **A. Status quo: drawn vector templates** | Low; reads as illustration | Exact | Fails Amazon main (photo required); Walmart wants a real photograph ([Dresma](https://www.dresma.com/blog/walmart-picture-requirements-what-you-need-to-know)) | ~$0 | Fits 0022 as written |
| **B. Licensed stock mockup photos + compositing** | High, but generic: many sellers use the same stock | Exact | Real model can serve as Amazon main; no AI involved, so no Etsy AI disclosure | License fee unknown; the license must allow reuse by many tenants (sublicensing), which is often extra | **Conflicts with 0022 §3** ("never downloaded stock art") → owner decision |
| **C. Photoshoot of real blank garments (InvAI house library, optional per-shop shoot) + compositing** | Highest; true blank color and drape | Exact | Best for Amazon/Walmart main; Etsy mockup-template use; no AI disclosure | One-time, about **$500–2,000 for a half-day fashion shoot**, or $25–500 per image ([Photoroom report](https://www.photoroom.com/industry-trends/product-photography-cost-for-smbs)); needs model releases | Same 0022 §3 wording conflict (not "drawn by code") → owner decision |
| **D. AI-generated base photos made once, reused + compositing** | High, depending on the model; consistent synthetic models | Exact (design never sent to the model) | Etsy AI disclosure on every derived image; Amazon `contains-synthetic-performer` tag on photoreal people; risky as Walmart/Amazon main | $0.04–0.15 per base attempt, amortized over thousands of designs | **Fits 0022 §1 as written** (AI garments and people allowed); needs a real provider (OI-25) |
| **E. Per-design AI scene (today's phase B)** | Medium: AI scene, but the print band is repainted | Exact after the lock | Disclosure on every image | ~$0.10–0.11 per image on `gpt-image-2` medium (OI-25) | Fits 0022/0023 as built |
| **F. Virtual try-on or generative editing with the design as input** | High | **Not exact**: the model redraws the print | Disclosure required; text and logos can drift silently | $0.06–0.075 per try-on ([FASHN](https://help.fashn.ai/plans-and-pricing/api-pricing); [cloudprice/Vertex](https://cloudprice.net/models/google-virtual-try-on-1)) | **Violates 0022 §3** if the design is in the input → reject for design pixels |

The recommendation is a **C-first, D-second library**. C is a one-day house photoshoot of the top blanks in their top colors. It produces flat, folded, ghost, standing-model front and back, and close-up bases, and it supplies every **main image** (the first, search-result image), where real photos are required or safest. D adds AI-generated lifestyle and extra-model bases for secondary slots, made once at library-build time and tagged as AI so disclosure follows them into every image. Option B is a fallback only if a stock license explicitly allows multi-tenant SaaS use. That term is unverified, and the legal question goes to the compliance officer. Try-on (F) still has one legitimate job: fed a **blank** garment photo, with no design, it can dress synthetic models to create more D-type bases. FASHN says its model preserves "text, patterns, and fabric details" ([FASHN API](https://fashn.ai/products/api)), and Vertex AI Virtual Try-On reached general availability on January 23, 2026 ([Google Cloud](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/generate-virtual-try-on-images)). Self-hosting open try-on models is ruled out, because IDM-VTON and CatVTON are licensed CC BY-NC-SA, which bans commercial use ([Hugging Face discussion](https://huggingface.co/yisol/IDM-VTON/discussions/26)).

The library also changes phase B. Today it pays for a provider call per design and then flattens the AI garment. With bases, the provider is called **once per base, by InvAI, at library-build time**. Every design reuses that base, and the compositor keeps the base's own garment pixels, using maps derived from them, instead of repainting a flat band. That needs an amendment to **ADR 0023 §2** (the restore-blank-color step) by the architect. Per-design AI scenes (E) remain a paid extra for shops that want a unique scene.

### Disclosure follows the base's origin

Disclosure must be tracked **per image, from the base's provenance**, which is a new `photo_base.origin` field (`shop_shoot`, `house_shoot`, `licensed_stock`, `ai_generated`). That extends the rule 0022 §4 already set ("disclosure follows the source, not the design"). Etsy has required AI disclosure since July 9, 2026. According to secondary summaries, the rule covers AI-generated mockups and lifestyle scenes but exempts "mockup templates where a real product photo is placed into a lifestyle scene by the seller" ([ngini](https://ngini.com/en-us/blog/etsy-ai-disclosure-policy-2026-explained); [Rewarx](https://www.rewarx.com/blogs/etsy-ai-generated-product-images-disclosure)). Undisclosed listings are filtered from search or removed. Amazon has required, since July 2026, the XMP keyword `contains-synthetic-performer` on photoreal AI-generated people ([Forbes](https://www.forbes.com/sites/gabrielalinzainescu/2026/07/25/amazon-requires-sellers-to-label-ai-generated-people-in-listing-images/)). TikTok Shop requires a visible AI label on AI-generated or significantly altered product imagery and synthetic humans ([pixelmatch](https://pixelmatch.art/blog/policy/tiktok-shop-ai-generated-content-label-requirements/)). For personalized items, Etsy expects the first image to show a finished, customized item representative of what the buyer receives ([Listadum](https://www.listadum.com/blog/should-you-disclose-mockups-and-ai-images-in-your-etsy-listings)).

So real-photo bases keep main images disclosure-free, and AI bases cost a disclosure on every image they touch. Every one of these rules comes from secondary summaries. The compliance officer must confirm each against Etsy, Amazon and TikTok primary pages before launch. Backlog item B-282 already tracks re-verifying Amazon's keyword wording.

## One 12-image master set feeds five marketplaces

### The channel rules that shape the set

| Rule | Etsy | Amazon | TikTok Shop | Walmart | Shopify |
|---|---|---|---|---|---|
| Image cap | **10 per secondary sources; B-280/code allow 20 → verify** ([Outfy](https://www.outfy.com/blog/etsy-listing-photo-size-guide/)) | 7–9 by category, convention not a published cap ([Controla](https://www.controla.global/blog/amazon-listing-images-guide.html)) | 9 ([Rewarx](https://www.rewarx.com/blogs/tiktok-shop-4-9-images-listing-requirements)) | min 4, 6+ for content score ([Dresma](https://www.dresma.com/blog/walmart-picture-requirements-what-you-need-to-know)) | No platform cap (own store) |
| Main image | Free style; 4:3 or square, ≥2000 px short side | Pure white RGB 255, ≥85% fill, no text, **standing model for adult apparel** ([Sellhound](https://www.sellhound.com/learn/amazon-main-image-requirements); [CatalogX](https://catalogx.app/blog/amazon-apparel-photo-requirements-model)) | White background, 1:1, no text | Pure white, ≥85% fill, real professional photo, 2200 px recommended | Free |
| Aspect | 4:3 or 1:1 | 1:1, ≥1000 px, 2000+ for zoom | **1:1 mandatory**, 800+ px | Apparel additional images **3:4 portrait** ([PixelBatch](https://pixelbatch.io/blog/walmart-image-requirements-guide)) | Consistent per store |
| Video | 1 clip, 5–15 s, 1:1 or 4:5; listings with video reported "40% more likely" to sell ([veonib, citing Etsy](https://veonib.com/blogs/etsy-listing-video-best-practices-2026-en)) | Optional | 9:16, 9–60 s, product in first 3 s ([dev.to](https://dev.to/northba/tiktok-shop-video-specs-a-technical-reference-for-anyone-building-video-tools-hjk)) | Optional | Optional |

On the **Etsy cap conflict**, the image-pattern research found every 2025–2026 secondary source saying 10 images plus 1 video, and it argued the "20" figure should be dropped. InvAI's code uses one flat `MAX_PHOTO_IMAGES_PER_LISTING = 20` for every channel (`invai-contracts/src/schemas/photos.ts:224`), and backlog B-280 already flags that Amazon and TikTok are lower. Neither side has been checked against Etsy's own help page, which returned HTTP 403 to the researchers. The blueprint below is built to be **correct either way**. Slots 1–10 form a complete Etsy listing, and slots 11+ are optional extras used only if the compliance officer confirms a higher cap. The B-280 fix should make the maximum a per-channel table that the compliance officer owns, rather than a constant.

The evidence on image count supports this size. Several studies report gains flattening after about six images, and going from 4 to 7+ images on Amazon has been tied to a 32% conversion lift. That figure is one aggregator's unverified summary ([clippingpath](https://www.clippingpath.in/blog/how-many-product-images-does-a-listing-need/)), so it is a direction rather than a promise. No sourced, apparel-specific data exists on how much of the frame the design should fill, or on front-back-sleeve order. The rules below are therefore defaults to A/B test (compare two versions on real traffic), not proven optima. Two rules carry the most weight. **The design always sits at its true printed size on the garment** (the pipeline already enforces this), so how visible the design is follows honestly from the print size the buyer will receive. And **one image is a close-up** in which the print fills most of the frame, so buyers can judge print quality.

### The shared master set

Every image is rendered once on a large master canvas with the garment inside a central safe zone. Channel images are then **deterministic crops and pads** of the master: 1:1 for Amazon and TikTok, 3:4 for Walmart, 4:3 for Etsy. White-background images pad with pure white. Lifestyle bases are captured wide enough for all three crops, so no AI outpainting (extending an image with generated content) is needed, and no disclosure is triggered.

| ID | Image | Base origin | Garment side | Design visibility | When |
|---|---|---|---|---|---|
| M1 | Standing model, front, pure white | Real photo (shoot) | Front | Garment ≥85% of frame; print true-size | Always; one per color for variant mains |
| M2 | Styled flat-lay or folded hero (best-seller color, e.g., Pepper or Ivory) | Real photo | Front | Print centered, true-size | Always |
| M3 | Ghost or flat front on white | Real photo | Front | Garment fills frame | Always; one per color |
| M4 | Back view | Real photo | Back | True-size back print | Only if a back print exists |
| M5 | Print close-up on fabric | Crop of M2/M3 at high resolution | Front (or back) | Print fills most of frame | Always |
| M6 | Lifestyle on-model, scene 1 | AI base (disclosed) or shoot | Front | True-size | Always |
| M7 | Lifestyle scene 2 or styled flat-lay with props | AI base or shoot | Front | True-size | Always |
| M8 | Color grid: design on every offered color | Composite of M3s | Front | Small, uniform | When ≥3 colors |
| M9 | Size chart for the exact blank | Rendered from supplier spec data | — | No design | Always ([Printify](https://help.printify.com/hc/en-us/articles/4483630220433-Where-can-I-find-size-guides) recommends it as an image slot) |
| M10 | Blank, fabric and care facts | Rendered template, supplier facts only | — | No design | Always |
| M11 | "How to order" steps | Rendered template | — | Preview of personalization | Only if the listing has personalization fields |
| M12 | Sleeve or left-chest detail | Crop | Sleeve / chest | Fills frame | Only if that placement exists |
| V1 | Short video | Deterministic pan/carousel of M-images (no AI) first; AI clip only on request | — | — | Optional; needs scope approval |

### Slot-by-slot blueprint per marketplace

| Slot | Etsy (10, maybe 20) | Amazon (7–9) | TikTok Shop (≤9, 1:1) | Walmart (6+, main 1:1, rest 3:4) | Shopify |
|---|---|---|---|---|---|
| 1 | M2 styled hero (personalized: finished custom item) | **M1** standing model, white, no text | M1 or M3 on white | **M1** or M3 on white | M2 |
| 2 | M6 lifestyle | M4 back or M6 | M6 | M4 back or M6 | M6 |
| 3 | M5 close-up | M5 close-up | M5 | M5 | M5 |
| 4 | M8 color grid | M9 size chart | M8 grid without text labels | M6 / M7 | M4 / M7 |
| 5 | M4 back or M7 | M6 / M7 lifestyle | M4 or M7 | M9 size chart | M8 |
| 6 | M3 flat front | M10 fabric and care | M7 | M10 | M9 |
| 7 | M9 size chart | M3 flat front | M3 | M3 | M10 |
| 8 | M10 fabric and care | (M12 detail) | M9 if text is allowed on secondaries (unverified) | — | M11 |
| 9 | M11 how-to-order, else M12 | — | — | — | per-color M3 |
| 10 | M1 white standing | — | — | — | — |
| Video | V1, 5–15 s, 1:1 | optional | V1 9:16, strongly advised | optional | optional |
| Colors | Variations share the set; M8 shows all | **Each color is a child listing with its own M1 main** | Per-variant M3 | Per-variant M1/M3 | Per-variant M3 |

Two code gaps fall out of this table. The Walmart preset is square 2000×2000 with white required (`photos.py` PRESETS), so it needs a 3:4 secondary preset and white-only-on-slot-1 logic, as Amazon already has. And Amazon's comparison and benefit infographics are left out on purpose, because they invite unsupported claims. Text on TikTok secondary images is marked unverified.

## Gang sheets need better file checks, not smarter nesting

InvAI's production side is ahead of the public market, and the report should say so plainly. Rectangle nesting (packing designs as rectangles, with rotation) using `rectpack` MaxRects tries 27 strategy combinations per sheet. It reserves a label strip under every design and measures utilization by length, so a half-empty last sheet cannot inflate the number. The market claims about the same band: manual layouts at 70–75% film use and auto-nesting at 90–95% ([dtfpromo](https://dtfpromo.com/blogs/news/how-to-maximize-dtf-film-auto-nesting-vs-manual-arrangement)). InvAI streams sheets up to 22×240 inches at 300 DPI without holding them in memory. It prints a QR code under each transfer (order, item, size, color, reprint flag) and a sheet-header QR, with module sizes chosen for handheld scanners. The industry still matches transfers to orders with sticky notes and printed labels, sorted by order number ([dtfsheet](https://dtfsheet.com/blogs/blog/dtf-gang-sheet-layout-guide)). Batching also exists already: `production/sheets.ts` sorts candidates by ship-by date, cuts off at a due date and can put rush items first.

The real gaps are the ones a crop of DTF file-prep tools now charges for. **DTFWiz** flags transparent edges, low DPI, white backgrounds and stray pixels, and upscales 4× with Real-ESRGAN ([DTFWiz](https://dtfwiz.com/tools/dtf-dpi-calculator)). **Kolormatrix** flags lines thinner than about **0.02 inch** and text under about 7–9 pt ([Kolormatrix](https://kolormatrix.com/blogs/news/how-small-is-too-small-for-dtf-printing-text-lines-detail-guidelines)), and its "White Ink Checker" shows which details are too thin for white ink at the chosen print size ([Kolormatrix](https://kolormatrix.com/blogs/news/how-to-check-dtf-artwork-before-you-print)). InvAI's `qa.py` measures effective DPI and semi-transparent "haze" (`soft_alpha_ratio`, with a `clean_alpha` repair), but nothing measures stroke width or text height. No upscaler exists either; `render.py` only warns when a photo would be stretched.

| Gap | AI or deterministic | How | Priority |
|---|---|---|---|
| Thin-line and small-feature detection at print size | **Deterministic** | Distance transform on the alpha mask at the target DPI, which gives the thinnest stroke in inches; flag <0.02 in (error) and 0.02–0.03 in (warn); connected-component height for tiny text; highlight overlay for the shop | P1 |
| Size-aware placement presets | **Deterministic** | Rules table: left chest 3.5×2 in (max 4.5 wide), full front 11×11 (max 12 wide, 16 tall oversized), sleeve 2.5×1 (or 2.5×14 vertical) ([screenprinting.com](https://www.screenprinting.com/blogs/news/dtf-transfer-placement-guide)); the same presets drive mockup placement, so the photo matches what gets pressed | P1 |
| White-box background and wrong color space | **Deterministic** | Detect an opaque near-white border; convert to sRGB on ingest | P1 |
| Low-resolution rescue (upscaling) | **AI (a vision model, not an LLM)** | Real-ESRGAN-class 4× upscale, opt-in, with before/after shown and the original kept; API around $0.0047 per upscale ([modelslab](https://modelslab.com/real-esrgan)) or self-hosted | P2, needs an owner decision |
| Press-order grouping on the sheet | **Deterministic** | Cluster left-chest, sleeve and full-front pieces so cutting follows pressing order (dtfsheet) | P3 |
| Contour (true-shape) nesting | **Deterministic optimizer** | Offline evaluation of sparrow / jagua-rs ([GitHub](https://github.com/JeroenGar/sparrow); [arXiv 2508.08341](https://arxiv.org/pdf/2508.08341)) on real sheet history before any build | Spike only |
| Background removal on photo-like uploads | **AI (segmentation)** | Photoroom API at $0.02 per image ([Photoroom API](https://www.photoroom.com/api/pricing)) or self-hosted; only for uploads without transparency | P3 |

**Where AI is not needed**, the answer is most of this list. Nesting, QR labeling, DPI, haze, thin-line and text-size checks, placement presets, batching by ship-by date, channel crops, white-background and fill checks, size charts, color grids and XMP tags are all exact computations. An LLM would make them slower, costlier and less reliable. White-underbase choke (shrinking the white layer slightly so it doesn't peek out) and mirroring belong to the vendor's RIP software (the printer's layout and ink-control program) ([QuickTransfers](https://quicktransfers.com/blogs/dtf/mastering-white-underbase-techniques-in-dtf-printing)). InvAI should not duplicate them. Contour nesting is not proven for this art. Its "10–25% film saving" figure comes from sheet-metal and garment-cutting research and is marked unverified in InvAI's own `research/08`. A 2025 reinforcement-learning nester reported 11% better material use, but on sheet-metal data ([ACM](https://dl.acm.org/doi/abs/10.1007/s10845-025-02620-6)). Most DTF art is close to rectangular, and InvAI's label strip under each piece favors rectangles. The right move is a measurement spike: compute each design's alpha-area ÷ bounding-box ratio over real history, replay three months of sheets through sparrow, and build only if film saved is at least 5%. At $3–5 per square foot of film ([Bear Transfers](https://beartransfers.com/pages/gang-sheet-calculator)), a shop using 1,000 square feet a month would save about $150–250 a month at 5%. That is real money, but not before the evidence exists.

AI upscaling needs a flag of its own. It **invents pixels in the design**, which is the very thing 0022 forbids for listing photos. 0022 is scoped to photos, not print files, but the same principle applies. It should therefore be opt-in per file, show a side-by-side comparison, keep the original, and record the shop's approval. The owner should confirm that carve-out explicitly rather than have it inferred.

## A design × 5 colors × 5 channels costs cents, unless every image is generated

### Unit costs (list prices; check quarterly)

| Item | Price | Source / status |
|---|---|---|
| Deterministic composite or crop | ≈ $0.001 or less | Estimate (CPU only) |
| AI base or scene image | $0.048 FLUX.2 [pro]; ~$0.067 (1K) to $0.101 (2K) Gemini 3.1 Flash Image, batch 50% off; ~$0.10–0.11 `gpt-image-2` medium | [BFL](https://bfl.ai/pricing), [Google](https://ai.google.dev/gemini-api/docs/pricing), OI-25 |
| Virtual try-on | $0.06–0.075 | FASHN official; Vertex via a price mirror |
| Background removal | $0.02 | Photoroom official |
| Upscale | ~$0.0047 API, or self-hosted | Secondary |
| AI video | ~$0.10/s Veo 3 Fast without audio; $0.14/s Kling 3 on fal | [Google](https://developers.googleblog.com/veo-3-now-available-gemini-api/), [fal](https://fal.ai/pricing) |
| LLM text (copy for 5 channels, alt text, slot picks) | ≈ $0.02–0.05 per design (estimate) | **Unverified**: the notes quote "Sonnet 5.5 $2/$10", but the current models are Opus 5.5, Sonnet 5 and Haiku 4.5, so token prices must be re-read from Anthropic's page |

LLM tokens are a rounding error next to image generation. The cost question is almost entirely how many images an AI model draws. The worked numbers below assume $0.05–0.11 per accepted AI image, multiplied by **1.3** to cover the one regeneration ADR 0023 allows. That gives **$0.065–0.143 per kept AI image**.

### Per set, per design and per month

| Scenario | One set (1 design, 1 color, 10 images) | 1 design × 5 colors × 5 channels | Small shop (20 designs/mo) | Mid (100/mo) | Large (300/mo) |
|---|---|---|---|---|---|
| **Template-only** (photo-base library) | $0.03–0.06 | $0.07–0.10 | $1–2 | $6–9 | $18–27 |
| **Hybrid** (library + 2 per-design AI scenes) | $0.15–0.34 | $0.20–0.39 | $4–8 | $19–38 | $57–114 |
| **Fully generative** (every image drawn by AI) | $0.70–1.50 | $3.30–7.20 | $40–87 | $200–434 | $600–1,300 |

The monthly columns assume an average of 3 colors per design (the 5-color column shows the upper bound) and 5 channels. Shop sizes are illustrative and should be checked against pilot data. The structural lesson is that **channels are free** (they are crops of the master), **colors are nearly free** with a library (one extra composite per color), and only per-image AI generation multiplies cost. The one-time library is small next to that. About 5 garments × 8 views × 6 colors = 240 AI bases at 4 attempts each is roughly **$50–110**. A house photoshoot costs about $500–2,000 per half day. Both are paid once by InvAI and shared by every tenant, because no tenant data is involved. Human time to check the maps is the larger cost, and the AI-assisted map tooling in wave IMG1 exists to shrink it.

### Credits and gross margin

InvAI's plans include monthly AI credits: trial 100 ($0), starter 500 ($149), growth 2,000 ($349), pro 6,000 ($699), scale 20,000 (custom) (`billing/service.ts:43-90`). Photos cost 1 credit per template image and 10 per AI scene (`ai/models.ts:93-94`), and text routes cost 1 credit per 1,000 tokens. Under today's prices, a hybrid design in 3 colors uses about 32 credits, so a starter shop gets only about 15 designs a month before its text routes take anything. That pushes shops away from the cheapest, most realistic path. The credit-pack price is unset (it lives on a Stripe price). The table assumes **$0.02 per credit** as a working figure for the owner to decide.

| Item | Today | Proposed | Revenue at $0.02/credit | Raw cost | Gross margin |
|---|---|---|---|---|---|
| Low-res preview (any) | charged per image | **0 credits** | $0 | ~$0.001 | Loss-leader that encourages the cheap path |
| Approved library set, per color (≤12 images) | 1 per image (~12) | **3 per set** | $0.06 | ~$0.012 | ~80% |
| Per-design AI scene, approved (regeneration included) | 10 | **15** (or keep 10 on a ≤$0.05 model) | $0.30 | $0.065–0.143 | 52–78% |
| AI on-model / try-on base for one shop | — | 15 | $0.30 | $0.08–0.10 | ~67–73% |
| Opt-in print-file upscale | — | 2 | $0.04 | ~$0.005 | ~88% |
| AI video clip (8 s) | — | 150, only if scope approves | $3.00 | $0.80–1.12 | 63–73% |
| Text: 1 credit per 1k tokens | 1 | Keep; route by evals | $0.02 | $0.005 at Haiku-class output (unverified), up to ~$0.02 at the top model | **~0–75%: check in cost-review** |

At plan level the photo risk is small. A pro shop that spends all 6,000 credits on AI scenes gets 400 scenes, which cost at most about $57, or **8% of $699**. A starter shop maxing out on scenes costs about $4.80, or 3% of $149. The hidden risk is the text meter. If output-heavy routes run on the most expensive model, one credit's raw cost can approach its $0.02 resale value. The monthly `cost-review` should verify current Anthropic and OpenAI prices and move bulk routes to cheaper models through `model-upgrade` evals. The shop's side of the math is very favorable. A traditional shoot costs $25–500 per image (Photoroom). AI photo tools retail at $0.078–0.30 per image ([Pebblely](https://pebblely.com/pricing)) and $0.48–1.10 per photo ([Botika](https://botika.com/pricing)). So InvAI's $0.06 per color set and $0.30 per AI scene sit at or below the market, while keeping 50–80% margins.

The engineering rules that keep this cheap follow from the cost structure. Generate bases once and share them. Cache composites by (design, base, color). Render previews at low resolution and finals only after approval. Generate AI scenes **only when a listing is about to be published**. Use Gemini or Claude batch modes (50% off) for overnight bulk runs. Use a cheap model for drafts and a better one only for the kept image. Dedupe near-identical designs with a perceptual hash (a fingerprint of how an image looks). Self-host only after volume is proven. A RunPod RTX 4090 at $0.34–0.74 an hour ([RunPod](https://www.runpod.io/pricing)) beats APIs only if it stays busy. At pilot scale, an idle GPU erases the 15–100× unit saving.

## Agents pick and check; the pipeline renders deterministically

This plugs into the earlier roster without a new agent. The **Listing Agent** (orchestrator plus per-channel workers) gains an **Image Studio** tool set, but the image pipeline itself is a deterministic job chain on the render queue, at lower priority than gang-sheet compose. The agent's job is choosing and checking, never drawing. It reads the design analysis (the existing `photo_analysis` route, which already suggests colors, alt text and image order). It picks the lead color and library bases whose tags match the niche through a short, cached call on a cheap model. It assembles the per-channel slot plan from the rules table. It writes alt text, and it hands the set to the approval inbox. Disclosure flags, white-background and fill checks, slot caps and the trademark gate stay **rule-coded**, not model-decided. The **Order Intake Sentinel** gains the new print-file checks: holding an order whose art fails the thin-line or DPI check at its placement size is an *auto*-level action. The **Production Planner** keeps sheet builds at *notify*.

| Action | Autonomy level |
|---|---|
| Free previews, slot plans, alt text | auto |
| Render an approved library set (costs credits) | notify, within the shop's monthly photo budget |
| Per-design AI scene, try-on, video | approve, or notify under a per-tenant credit threshold once evals pass |
| AI upscale of a print file | approve, always (it changes design pixels) |
| Publish or push to any channel | approve, always (0022 §5, B-46 trademark gate) |
| Hold an order for unprintable art | auto (internal, reversible) |
| Build gang sheets | notify |

| Wave | Tasks (owning role) | Exit gate |
|---|---|---|
| **IMG0 Decide** | ADR amendment to 0022 §3 / 0023 §2 for photo bases and `origin` provenance (architect); OI items below (product-manager → escalate-to-owner); verify Etsy cap, Walmart 3:4, TikTok text rules, stock licensing terms (compliance-officer); cost model and credit prices (data-analyst) | Owner answers; per-channel caps table signed off |
| **IMG1 Photo-base library** | `photo_bases` asset model, map derivation (mask, displacement, shading, occlusion), recolor LUT + deltaE check, pyvips render (imaging-engineer); contract `PhotoImageSource` + `photo_base` and provenance (architect); library admin and calibration screen (web-engineer); base import, credits per set, preview at 0 credits (backend-engineer); acceptance tests incl. SSIM, deltaE, Amazon main checks (qa-engineer) | Amazon main passes `photo_required`; B-287 drawstring and B-289 flat-lay fixed; peak RSS within B-278 budget |
| **IMG2 Channel blueprint** | Per-channel slot rules, caps table (fixes B-280), crops/pads incl. Walmart 3:4 (imaging-engineer + backend-engineer); size-chart, care, how-to-order and color-grid renderers (imaging-engineer); per-image disclosure from provenance plus zip READMEs per channel (fixes B-290) (backend-engineer + compliance-officer review); attach and approval UI (web-engineer) | Golden-path E2E produces five valid channel sets from one design |
| **IMG3 Print-file prep** | Thin-line, small-text, white-box and sRGB checks with overlay (imaging-engineer); placement presets shared by mockups and sheets (architect + backend-engineer); Order Intake Sentinel hold rule (ai-engineer); opt-in upscaler behind a mock, if approved (imaging-engineer); contour-nesting measurement spike with sparrow (imaging-engineer) | Seeded thin-line and low-DPI art caught ≥95%; spike report with film-saving number |
| **IMG4 AI bases and agent** | Build AI and try-on base sets once at library time behind OI-25 (ai-engineer); Listing Agent Image Studio tools and evals (ai-engineer); cost-review of photo and text margins (data-analyst); security co-review of the new asset paths (security-reviewer) | Override rate <10% on slot plans; margin per credit ≥50% verified |

The owner needs to decide five things. Each comes with a safe default, so nothing is overridden silently.

| # | Decision | Recommendation | Default if unanswered |
|---|---|---|---|
| 1 | Amend **0022 §3** so real photographs (house shoot, shop's own shoot, licensed stock) can be bases, not only code-drawn templates | Yes: the design lock is unchanged, and only the garment source widens | Drawn templates only; Amazon main stays impossible |
| 2 | Fund a **house photoshoot** of the top blanks (about $500–2,000 per half day) vs. licensed stock vs. AI-only bases | Photoshoot for main images; AI bases for secondary lifestyle slots | AI-only bases with disclosure, once OI-25 is on |
| 3 | **OI-25**, reframed: use the real image provider to build the shared library once (about $50–110), and for paid per-design scenes | Option A (dev trial), then library build | Mock scenes |
| 4 | **Credit prices**: free previews, 3 per library set, 15 per AI scene, set the pack price (e.g., $0.02 per credit) | Yes | Today's 1 / 10 credits |
| 5 | **AI upscaling of print files** as an opt-in exception to the "models never alter design pixels" principle; **video** as a new scope item | Upscale: yes, opt-in with before/after. Video: deterministic carousel first; AI video only via an SCR | Neither built |

Decision 0006 is untouched: no model ever invents a design. Contour nesting needs no decision until the spike reports.

## Conclusion

The research reverses an easy assumption. "Real pictures" does not mean "more generative AI". The most realistic, compliant and cheapest listing photo is a real photograph of a real blank with the shop's exact design laid onto it by plain image math, and AI's best role is building and mapping the library once rather than redrawing every listing. That turns image cost from a per-listing variable into a one-time platform asset shared by every tenant, so InvAI can give shops near-free, approval-gated photo sets and charge credits only for the truly variable extras (per-design scenes, try-on, video, upscaling) at healthy margins. The same discipline applies to the gang-sheet side. InvAI's lead in nesting and traceability is already won with deterministic code, and the remaining wins are measurement problems (stroke width, text height, placement size), not intelligence problems. The open risks are factual rather than technical: Etsy's real image cap, Walmart's 3:4 rule, TikTok's text rule and the wording of stock licenses all rest on secondary sources. The compliance officer should confirm them before the blueprint ships.
