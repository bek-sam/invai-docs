# InvAI: AI and imaging vendor research and cost model (prices checked 2026-09-23)

**How to read this**
- **[V]** means I read the price on the vendor page today (source URL given).
- **[U]** means the number is unverified. It comes from memory, an estimate, or a page that didn't show prices (dynamic or behind sales). Confirm these before committing.
- WebSearch was capped (200 of 200 calls), so everything here comes from WebFetch or curl on official pages.
- **Shop counts are my assumption.** You didn't give any. I used Pilot = 10 shops, Growth = 100, Scale = 500. That works out to about 150–160 designs per shop per month in every scenario, which is consistent.
- **Things that have changed recently:**
  - OpenAI's current image models are `gpt-image-2.5-sunburst/flare` and `gpt-image-2`.
  - Google has Nano Banana 2 / Pro (Gemini 3.x image) and lists an Imagen 5 SKU.
  - Ideogram's API docs now mention Ideogram 4.0, but I couldn't get a price for it [U].
  - Recraft has V4 / V4.1.

---

## 1. LLM listing copy (Claude)
**Assumptions**
- Each generation uses 3,000 input tokens (image included) and 800 output tokens.
- With caching, a 2,000-token shared prefix is read from cache at 10% of the input price. Only 1,000 tokens are billed at full price.
- Effective input with caching = 2,000×0.1 + 1,000 = **1,200 token-equivalents**.
- I ignored the cache-write premium (1.25× input on the first write). It's small when the hit rate is high.
- Batch gives 50% off both input and output.
- For Opus 5 on low effort, I assumed the 800 output tokens already include any thinking.

**Per-generation cost**

| Model | No optimisation | Cache only | Batch only | Batch + cache |
|---|---|---|---|---|
| Opus 5 ($5/$25) | 3k×5/1M + 0.8k×25/1M = 0.015+0.020 = **$0.0350** | 1.2k×5/1M + 0.020 = **$0.0260** | **$0.0175** | **$0.0130** |
| Sonnet 5 ($2/$10) | 0.006+0.008 = **$0.0140** | 0.0024+0.008 = **$0.0104** | **$0.0070** | **$0.0052** |
| Haiku 4.5 ($1/$5) | 0.003+0.004 = **$0.0070** | 0.0012+0.004 = **$0.0052** | **$0.0035** | **$0.0026** |

**Monthly cost (volume × per-generation cost; 3k / 30k / 150k generations)**

| Model / mode | Pilot | Growth | Scale |
|---|---|---|---|
| Opus 5, no optimisation | $105 | $1,050 | $5,250 |
| Opus 5, batch + cache | $39 | $390 | $1,950 |
| Sonnet 5, no optimisation | $42 | $420 | $2,100 |
| Sonnet 5, cache only | $31.2 | $312 | $1,560 |
| **Sonnet 5, batch + cache** | **$15.6** | **$156** | **$780** |
| Haiku 4.5, no optimisation | $21 | $210 | $1,050 |
| Haiku 4.5, batch + cache | $7.8 | $78 | $390 |

- **Pick:** Sonnet 5 with batch + cache for bulk channel copy. Use real-time Sonnet only for single interactive requests.
- **Runner-up:** Haiku 4.5 with batch + cache for cheap per-channel variants of a Sonnet "master" listing.
- Opus 5 costs 2.5× Sonnet. It isn't justified for templated copy.

## 2. Business assistant chats
**Assumptions**
- Each chat uses 20,000 input and 1,500 output tokens.
- With caching, I assumed 80% of input (system prompt, tools, earlier turns) is read from cache.
- Effective input with caching = 4,000 + 16,000×0.1 = **5,600 token-equivalents**.
- I ignored cache writes; they add roughly 5–15% [U]. Batch doesn't apply because chats are interactive.

**Per-chat cost**

| Model | Uncached | Cached |
|---|---|---|
| Opus 5 | 20k×5/1M + 1.5k×25/1M = 0.10+0.0375 = $0.1375 | 5.6k×5/1M + 0.0375 = $0.0655 |
| Sonnet 5 | 0.04+0.015 = $0.055 | 0.0112+0.015 = $0.0262 |
| Haiku 4.5 | 0.02+0.0075 = $0.0275 | 0.0056+0.0075 = $0.0131 |

**Monthly cost (1k / 10k / 50k chats)**

| Model / mode | Pilot | Growth | Scale |
|---|---|---|---|
| Opus 5, uncached | $137.5 | $1,375 | $6,875 |
| Opus 5, cached | $65.5 | $655 | $3,275 |
| Sonnet 5, uncached | $55 | $550 | $2,750 |
| **Sonnet 5, cached** | **$26.2** | **$262** | **$1,310** |
| Haiku 4.5, cached | $13.1 | $131 | $655 |

- **Pick:** Sonnet 5 with caching. Tool-use reliability matters in business chats.
- **Runner-up:** Haiku 4.5 as a router for simple lookups, escalating to Sonnet.

## 3. AI t-shirt design generation (1,500 / 15,000 / 80,000 images)
Monthly cost = volume × unit price. Some options in the table have no transparency; those designs also need the background-removal step (section 5).

| Option | Unit price (source) | Text, transparency, license notes | Pilot | Growth | Scale | Fit /10 |
|---|---|---|---|---|---|---|
| **Ideogram 3.0 Transparent** via fal: Turbo / Balanced / Quality | $0.03 / $0.06 / $0.09 [V] https://fal.ai/models/fal-ai/ideogram/v3/generate-transparent | Best-in-class typography, plus **native transparent PNG**. Output about 1.5k px max, so it needs upscaling. Commercial use allowed. No IP indemnity [U]. Same prices on Replicate [V] https://replicate.com/ideogram-ai/ideogram-v3-turbo. Ideogram 4.0 exists; price [U]. | Turbo $45; Balanced $90; Quality $135 | $450 / $900 / $1,350 | $2,400 / $4,800 / $7,200 | **9** |
| Recraft V3 / V4 raster; V4.1 Standard; V4.1 Flash | $0.04; $0.035; $0.007 [V] https://www.recraft.ai/docs/api-reference/pricing | Strong long-text rendering. Styles and brand consistency. | V4 raster $60 | $600 | $3,200 | 8 |
| **Recraft vector (SVG)**: V3 / V4 Standard; V4.1 Pro Vector | $0.08; $0.30 [V] | Native SVG output, so resolution-independent and ideal for DTF text and flat designs. Vectorize endpoint is $0.01 [V]. | $120 | $1,200 | $6,400 | 8 (for the vector niche) |
| GPT Image 1.5, medium / high, 1024×1536 | $0.05 / $0.20 [V] https://developers.openai.com/api/docs/guides/image-generation | Excellent instruction-following and text. `background:"transparent"` is supported on GPT Image 2.5 [V] and was supported on 1.5 [U for 2 and 1.5]. OpenAI business terms include output IP indemnity (Copyright Shield) [U; check terms]. | Medium $75; high $300 | $750 / $3,000 | $4,000 / $16,000 | 8 |
| GPT Image 2, low / medium / high, 1024² | $0.006 / $0.053 / $0.211 [V] (same page) | Newer model. Transparency support [U]. | Medium $79.5 | $795 | $4,240 | 7 |
| GPT Image 2.5 (sunburst / flare) | Priced by tokens: $30/1M image output [V]. Calculator shows "low" = 196 tokens ≈ $0.0059. Medium and high [U] (the calculator is JS-only). | Current flagship. Transparency supported up to 3840 px per edge [V]. | ~$9 at low | ~$88 at low | ~$470 at low | 7 (price unclear) |
| GPT Image 1 Mini, medium 1024×1536 | $0.015 [V] | Cheap drafts. Weaker text. | $22.5 | $225 | $1,200 | 6 |
| Imagen 4 Fast / 4 / 4 Ultra (Vertex) | $0.02 / $0.04 / $0.06 [V] https://cloud.google.com/vertex-ai/generative-ai/pricing | Good text on 4 and Ultra. **No transparency.** Google Cloud generative-AI indemnity covers Imagen on Vertex [U; check terms]. | Imagen 4 $60 | $600 | $3,200 | 7 |
| Nano Banana (Gemini 2.5 Flash Image); batch | $0.039; $0.0195 [V] https://ai.google.dev/gemini-api/docs/pricing | Great for editing. **No true alpha** (fakes a checkerboard background). | $58.5 (batch $29) | $585 | $3,120 | 6 |
| Nano Banana 2 (Gemini 3.1 Flash Image) at 1K; Nano Banana Pro at 1–2K | $0.067; $0.134 (batch 50% off) [V] | Very strong typography; fal says "character-validated". No alpha. | $100.5; $201 | $1,005; $2,010 | $5,360; $10,720 | 7 |
| FLUX.2 [pro] via fal (1 MP) | $0.03 first MP + $0.015 per extra MP [V] https://fal.ai/models/fal-ai/flux-2-pro | Good. Text is decent, not the best. No alpha. | $45 | $450 | $2,400 | 6 |
| Seedream 4.5 via fal | $0.04 [V] https://fal.ai/models/fal-ai/bytedance/seedream/v4.5/text-to-image | Native 4 MP output. Commercial use "under partner agreement". No alpha. | $60 | $600 | $3,200 | 6 |
| Qwen-Image via fal (Apache-2.0 weights) | $0.02/MP [V] https://fal.ai/pricing | Strong text for an open model. Could be self-hosted later on an H100 for about $0.015 per image [U]. No alpha. | $30 | $300 | $1,600 | 6 |

- **Pick:** Ideogram 3.0 Transparent.
  - Use Turbo for drafts and Balanced for finals. I costed a blend of 60% Turbo and 40% Balanced: 0.6×0.03 + 0.4×0.06 = **$0.042 per image**, giving **$63 / $630 / $3,360** per month.
  - Route text-only or flat designs to Recraft vector ($0.08), or vectorize finals ($0.01).
- **Runner-up:** GPT Image 1.5 or 2.5 medium. It has transparency and OpenAI's indemnity, but costs about 1.2–1.3× more per image.

## 4. Upscaling to 300 DPI (e.g. 4500×5400 = 24.3 MP; 1,000 / 8,000 / 40,000 images)

| Option | Unit price | Notes | Pilot | Growth | Scale | Fit |
|---|---|---|---|---|---|---|
| **Real-ESRGAN (BSD-3) self-hosted on Modal T4** | T4 at $0.000164/s [V] https://modal.com/pricing. At about 8 s per 4× tiled upscale: ≈ $0.0013, rounded up to **$0.002** for cold starts [U runtime] | Keeps flat and line art crisp (use the anime/illustration weights for graphics). Supports RGBA by upscaling alpha separately. Modal Starter includes $30/month free compute. | $2 | $16 | $80 | **9** |
| fal ESRGAN | $0.00111 per compute-second [V] https://fal.ai/models/fal-ai/esrgan. At about 4 s ≈ $0.0044 [U] | Hosted, no ops. | $4.4 | $35 | $178 | 8 |
| Replicate Real-ESRGAN | T4 at $0.000225/s [V] https://replicate.com/pricing | Model card recommends input ≤ 1440p. | ≈$2–3 | ≈$20 | ≈$100 [U] | 7 |
| Recraft Crisp Upscale | $0.004 [V] | Output-size cap [U]. Confirm it can reach 24 MP. | $4 | $32 | $160 | 7 |
| Topaz via fal | $0.08 up to 24 MP; **$0.16 up to 48 MP** [V] https://fal.ai/models/fal-ai/topaz/upscale/image | Best for photographic art. 4500×5400 is 24.3 MP, which **falls in the $0.16 tier**. Staying under 24 MP means about 4,470×5,364. | $80 / $160 | $640 / $1,280 | $3,200 / $6,400 | 6 |
| Imagen 4 Upscale | $0.06 [V] | Maximum output is 4K, **not enough for 5400 px**. | $60 | $480 | $2,400 | 3 |
| Clarity Upscaler via fal | $0.03/MP × 24.3 = $0.73 [V] https://fal.ai/models/fal-ai/clarity-upscaler | Generative. **Hallucinates text.** | $730 | $5,832 | $29,160 | 2 |
| Recraft Creative Upscale | $0.25 [V] | Generative. | $250 | $2,000 | $10,000 | 3 |

- **Pick:** self-hosted Real-ESRGAN, with the vector route for typography.
- **Runner-up:** fal ESRGAN for zero ops; Topaz as a premium option for photo art.

## 5. Background removal (1,000 / 8,000 / 40,000 images)

| Option | Unit price | Notes | Pilot | Growth | Scale | Fit |
|---|---|---|---|---|---|---|
| **BiRefNet (MIT)** self-hosted, or via Replicate | Replicate: ≈$0.0017 per run on A100, ~2 s [V] https://replicate.com/men1scus/birefnet. Modal T4: ≈$0.0005 [U] | Top open-source matting. Use BiRefNet-HR for print-sized images. For DTF, threshold/defringe the alpha: DTF needs hard edges and no halos. | $1.7 | $13.6 | $68 | **9** |
| fal BiRefNet v2 | Per compute-second [V]; ≈$0.002 per image [U] | Hosted. | ≈$2 | ≈$16 | ≈$80 | 8 |
| rembg (MIT) on CPU | ≈$0.0001 [U] | Lower quality on fine detail. Good as a fallback. | <$1 | ≈$1 | ≈$4 | 6 |
| Recraft Remove Background | $0.01 [V] | Hosted. | $10 | $80 | $400 | 7 |
| Bria RMBG 2.0 via fal | $0.018 [V] https://fal.ai/models/fal-ai/bria/background/remove | Trained on licensed data; Bria offers indemnity [U]. Output capped at 1024². Self-hosting the weights is CC BY-NC [U]. | $18 | $144 | $720 | 6 |
| Photoroom API (Basic) | $0.02 [V] https://www.photoroom.com/api/pricing | Hosted. | $20 | $160 | $800 | 6 |
| remove.bg | ≈$0.10–0.23 [U]; the page is dynamic | Expensive. | ≈$180 | ≈$1,440 | ≈$7,200 | 3 |

- **Pick:** BiRefNet self-hosted in the same Modal app as the upscaler.
- **Runner-up:** Recraft ($0.01), or Bria if indemnity matters.
- Most generated designs won't need this step if they come from Ideogram's transparent endpoint.

## 6. Mockups (5,000 / 50,000 / 250,000 renders)

| Option | Unit price | Notes | Pilot | Growth | Scale | Fit |
|---|---|---|---|---|---|---|
| **Self-built compositor** (Sharp/libvips or Pillow: displacement map, multiply blend, colour-tint masks) | CPU $0.0000131 per core-second [V] (Modal). At about 0.5 core-s per render: 5k → $0.03, 50k → $0.33, 250k → $1.64, plus a similar memory cost | Deterministic and exact to the design. One-time cost for blank photos/PSDs ≈ $500–3,000 [U]. Budget with storage/CDN: ≈$5 / $15 / $50 [U]. | $5 | $15 | $50 | **9** |
| Dynamic Mockups API | Pro: $0.051/credit, 1 credit per API render, about 300 credits/month [V] https://dynamicmockups.com/pricing/. Enterprise from 5k+/month: custom [U; I assumed $0.02 and $0.01] | Fastest to ship. Large template library. | $255 | ≈$1,000 [U] | ≈$2,500 [U] | 7 (pilot) |
| Printful Mockup Generator API | Free, rate-limited [V] https://developers.printful.com/docs/ | Printful catalog products only, so it doesn't fit shops printing on their own DTF blanks. | $0 | $0 | $0 | 4 |
| Generative mockups (Nano Banana / FLUX Kontext edit) | ≈$0.04 [V] | Distorts the design. Not accurate enough for listings. | $200 | $2,000 | $10,000 | 2 |

- **Pick:** self-built compositor.
- **Runner-up:** Dynamic Mockups during the pilot, while the compositor is being built.

## 7. OCR for trademark screening (1,500 / 15,000 / 80,000 images)

| Option | Unit price | Notes | Pilot | Growth | Scale | Fit |
|---|---|---|---|---|---|---|
| **Claude extracts text inside the listing-copy call** | About +100 output tokens × $5/1M (Sonnet batch output price) = $0.0005 | The design image is already in that call. VLMs handle distressed or stylised fonts far better than classic OCR. | $0.75 | $7.5 | $40 | **9** |
| Standalone Claude call (Haiku 4.5) | About 1.9k input + 150 output: 0.0019 + 0.00075 = $0.00265 (batch $0.0013) | Same VLM advantage, separate call. | $3.98 | $39.75 | $212 | 7 |
| PaddleOCR (Apache-2.0) / Tesseract self-hosted on CPU | About 2 core-s ≈ $0.00003–0.0001 [U] | Weak on stylised text. Useful as a second signal. | ≈$0.5 | ≈$3 | ≈$10 | 6 |
| Google Cloud Vision TEXT_DETECTION | First 1k/month free, then $1.50/1k [V] https://cloud.google.com/vision/pricing | Pilot: (1,500−1,000)×0.0015 = $0.75. Growth: 14k × 0.0015 = $21. Scale: 79k × 0.0015. | $0.75 | $21 | $118.5 | 7 |
| AWS Textract DetectDocumentText | $0.0015/page [V] https://aws.amazon.com/textract/pricing/ | Built for documents, not artwork. | $2.25 | $22.5 | $120 | 5 |
| AWS Rekognition DetectText | $0.001 [V] https://aws.amazon.com/rekognition/pricing/ | Caps at about 100 words [U]. | $1.5 | $15 | $80 | 5 |

- **Pick:** Claude-in-the-listing-call plus PaddleOCR. Budgeted at $1.25 / $10.5 / $50.
- **Runner-up:** Google Vision.

## 8. LLM observability, evals and prompt management

**Units per month (my estimate)**
- Unit assumptions: 3 per listing, 8 per chat, 2 per image, OCR, or background-removal job.
- Pilot: 9k + 8k + 10k ≈ **27k units**
- Growth: 90k + 80k + 92k ≈ **262k units**
- Scale: 450k + 400k + 480k ≈ **1.33M units**

**Langfuse Core cost arithmetic** (100k units included, $8/100k up to 1M, $7/100k above)
- Growth: $29 + 162k × $8/100k = **$41.96**
- Scale: $29 + (900k × $8/100k = $72) + (330k × $7/100k = $23.1) = **$124.10**

| Option | Pricing | Pilot | Growth | Scale | Fit |
|---|---|---|---|---|---|
| **Langfuse Cloud Core** | $29/month with 100k units; overage $8/100k, then $7/100k above 1M [V] https://langfuse.com/pricing. Pro is $199 (SOC2/HIPAA, 3-year retention). Self-hosting is MIT-licensed, infra ≈ $50–150/month [U]. | $29 | $41.96 | $124.10 (Pro $294) | **9** |
| Helicone | Free tier 10k requests. Pro $79 plus usage, Team $799 [V] https://www.helicone.ai/pricing. Overage rates [U]. | $79 | ≈$100+ [U] | ≈$200+ [U] | 7 |
| Braintrust | Starter free. Pro $249 with 5 GB, then $3/GB; 50k scores, then $1.50/1k [V] https://www.braintrust.dev/pricing | Evals-first. | $0–249 | $249+ | $249+ | 7 (evals) |

- **Pick:** Langfuse. It covers traces, prompt management and evals, and you can self-host later.
- **Runner-up:** Braintrust, if evals become the priority.

## 9. Gang-sheet nesting libraries (licenses from memory [U]; compute cost negligible)
- **rectpack** (Apache-2.0, Python, MaxRects/Skyline): bounding-box packing with rotation. **Pick for v1.** Fine for 22"-wide DTF rolls.
- **SVGnest / Deepnest** (MIT, JS): irregular no-fit-polygon nesting with a genetic algorithm. Slow, but runs in the browser.
- **jagua-rs / sparrow** (Rust; MPL-2.0 / MIT [U]): state-of-the-art irregular strip packing. **Runner-up for v2.** Irregular nesting typically saves about 10–25% film [U].
- **libnest2d** (LGPL-3.0, C++): used by PrusaSlicer. Link it dynamically.
- **potpack** (ISC, JS): trivial packing for previews only.

## 10. Trademark data (checks = 1.5k / 15k / 80k)

| Option | Pricing | Notes | Fit |
|---|---|---|---|
| **USPTO Open Data Portal bulk trademark XML, plus the TSDR API** | Free, API key required, about 60 requests/min [U; from memory] https://data.uspto.gov | Build a local Postgres FTS or OpenSearch index of live US marks for a phonetic/fuzzy first pass. Infra ≈ $20 / $40 / $80 [U]. US only. | **9** |
| Signa API | Free: 100 searches. Starter $99 (2k searches). Growth $399 (10k). Scale $999 (50k). Yearly billing, 10 credits per search, overage $10 / $5 / $2.50 per 1k credits [V] https://signa.so/pricing | Covers multiple registries (EUIPO/WIPO). If every check hit Signa: $99 / (399 + 50k credits × $5/1k = $649) / (999 + 300k credits × $2.50/1k = $1,749). | 8 |
| Markify / Trademarkia API | Contact sales [U] | Pricing not public. | 5 |

**Pick:** local USPTO index for every check. Send only the ~10% flagged hits to Signa: 150 / 1.5k / 8k searches, which fits Starter $99 / Starter $99 / Growth $399. Total with the index: **$119 / $139 / $479**. This covers trademarks only; copyrighted characters are not screened.

## 11. Keyword and trend data
- **DataForSEO** [V] https://dataforseo.com/pricing/keywords-data/google-ads
  - Google Ads search volume: $0.06 per task of up to 1,000 keywords (standard queue), or $0.09 live. That's $60 per 1M keywords.
  - $50 minimum deposit.
  - Amazon and Trends endpoint prices [U].
- **Keywords Everywhere API** [V] https://keywordseverywhere.com/credits.html
  - $80 for 200k credits ($0.40/1k), down to $0.16/1k at 50M credits.
  - Covers Google, Amazon, eBay and YouTube.
- **Google Trends API:** alpha, application-only, pricing not stated [V] https://developers.google.com/search/apis/trends. Don't depend on it.
- **eRank / Everbee:** no public API found [U].
- **Pick:** DataForSEO, with a keyword cache shared across tenants. Budget **$50 / $75 / $250** [U, estimate].
- **Runner-up:** Keywords Everywhere.

## 12. Demand forecasting
- **statsforecast** (Apache-2.0). **Pick.**
  - AutoETS, AutoARIMA, Croston/TSB for sparse per-size/colour sales.
  - Handles millions of series in minutes of CPU. Budget ≈ $1 / $5 / $20 [U].
- **Prophet** (MIT). **Runner-up**, for shop-level totals with holiday effects.
  - Slow per series and poor on intermittent demand.

---

## Summary: recommended picks (monthly USD)
Shops assumed: 10 / 100 / 500.

| Category | Pick | Pilot | Growth | Scale |
|---|---|---|---|---|
| Design generation | Ideogram 3 Transparent, 60% Turbo / 40% Balanced ($0.042) | 63.00 | 630.00 | 3,360.00 |
| Upscaling | Real-ESRGAN on Modal ($0.002 [U]) | 2.00 | 16.00 | 80.00 |
| Background removal | BiRefNet ($0.0017) | 1.70 | 13.60 | 68.00 |
| Mockups | Self-built compositor [U] | 5.00 | 15.00 | 50.00 |
| Listing copy | Sonnet 5, batch + cache | 15.60 | 156.00 | 780.00 |
| Assistant chats | Sonnet 5, cached | 26.20 | 262.00 | 1,310.00 |
| OCR | Claude-in-call + PaddleOCR | 1.25 | 10.50 | 50.00 |
| **AI + imaging subtotal** | | **114.75** | **1,103.10** | **5,698.00** |
| Observability | Langfuse Core | 29.00 | 41.96 | 124.10 |
| Trademark | USPTO index + Signa on flagged hits | 119.00 | 139.00 | 479.00 |
| Keywords | DataForSEO [U] | 50.00 | 75.00 | 250.00 |
| Forecasting | statsforecast compute [U] | 1.00 | 5.00 | 20.00 |
| **Total** | | **313.75** | **1,364.06** | **6,571.10** |
| **Cost per shop** | total ÷ 10 / 100 / 500 | **$31.38** | **$13.64** | **$13.14** |
| AI + imaging only, per shop | | $11.48 | $11.03 | $11.40 |

**What drives the cost**
- Design generation is about 51–59% of the Growth and Scale totals. Every $0.01 change in unit price moves Scale by $800.
- **All Turbo** ($0.03): Scale design falls to $2,400, saving $960.
- **Opus 5 instead of Sonnet 5** for copy (batch + cache) and chats (cached): Growth rises by +$234 + $393 = +$627, and Scale by +$1,170 + $1,965 = +$3,135.
- Modal's $30 monthly credit covers all Pilot GPU work.

**Risks to verify**
1. Ideogram 4.0 and GPT Image 2.5 per-image prices.
2. Terms that affect liability for shops:
   - IP indemnity: OpenAI and Google offer it; Ideogram, Recraft and fal don't appear to. Check current terms.
   - Seedream's "partner agreement" terms on fal.
   - Bria RMBG-2.0 weights are licensed non-commercial.
3. Recraft crisp-upscale output cap.
4. Dynamic Mockups enterprise rate.
5. USPTO rate limits.
6. The mockup and upscale runtimes are estimates. Benchmark them on Modal before relying on them.

