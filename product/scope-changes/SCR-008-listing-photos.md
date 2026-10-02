# SCR-008: AI listing photos (template photo sets, then generated lifestyle scenes)
Filed by: product-manager  Date: 2026-10-02  Type: add
Scope section affected: scope.md#mvp-in (new item 18); items 9 (vendor portal design files), 10 (AI listing drafts)

## Request
A shop picks one of its **own uploaded designs**, garment types (tee, hoodie, crewneck, tank) and blank colors, and InvAI produces a per-marketplace listing photo set:
- **Phase A (wave 26):** AI design analysis (recommended blank colors, contrast warnings, alt text, per-channel image order); drawn garment templates (4 garments × front flat, folded, back, on-model-on-white); the shop's real design composited at its real print size on the real blank hex, with a white-underbase preview; channel presets (Amazon, Etsy, Shopify, TikTok, Walmart) with automated checks shown to the shop; XMP `contains-synthetic-performer` on any photoreal AI person; Etsy's AI-use disclosure when a generated image is used; credits per image; shop approval before any image leaves InvAI; zip download; attach to an AI listing draft.
- **Phase B (wave 27):** an image-generation provider (deterministic mock by default; OpenAI GPT Image only when the owner sets `IMAGE_GEN_PROVIDER=openai`, behind a per-shop daily cap and a platform spend cap) draws the scene and garment around the design; design-lock drift checks reject any output where the design itself was touched; approved images can push to a Shopify product.

## Why (evidence)
- `research/16-growth-opportunities.md` §2, "Features competitors have that we lack": **"Mockup creation (5 products). We have flat tee mockups only"** is ranked #1 of 10 feature gaps (line ~147). The same file's design-pipeline section (§5.2, ~line 420-440) already assumes a mockup step feeding listing drafts.
- Competitors: Pythias (claims AI mockups), MyDesigns (AI listings and mockups), Printavo/Taivo (Mockup Creator), YoPrint (Mockup Creator) — `research/02-competitors.md` and `research/16` §2. We currently have one flat-tee tint mockup (`invai-imaging/app/mockups.py`), nothing per-garment, per-view or per-channel.
- Pilots and tickets: **0 shops have asked.** No pilot is live yet (same honesty standard as SCR-002's digest). This is an owner-initiated bet on a visible competitive gap, not a pilot-confirmed pain.
- The owner approved it directly in chat, 2026-10-02, quote: **"implement these all."**

## Who it helps
Small and mid shops that list their own designs (owner, designer, office roles) on Etsy, Amazon, Shopify, TikTok and Walmart — every segment that currently hand-makes or buys mockups elsewhere. Large shops get the same tool; no segment-specific cut.

## Cost and risk
- Effort: 2 waves, 10 cards (`waves/26/wave.md`, `waves/27/wave.md`): a new contract namespace, a new imaging template library and compositor, a new AI vision route, a new backend module with tables and jobs, two web screens, an image-generation provider, and a Shopify image-push adapter.
- New paid service, gated: OpenAI GPT Image, off by default (OI-25, owner decides when to turn it on; estimated $0.02–0.06/image).
- Risk, controlled by design: the design itself must never be drawn, redrawn or altered by an image model — only `invai-imaging` composites the shop's real design pixels, deterministically, onto AI- or template-made scenes (decision 0022). Marketplace-policy risk (Amazon synthetic-performer tag, Etsy AI disclosure) is covered by the contract's ADR 0023 and compliance-officer co-review on both imaging cards and the phase B backend card.
- No new tenant-cost line beyond existing AI credits (template images 1 credit, AI scene images 10 credits — owner may change, OI-25) and the capped, off-by-default OpenAI spend.

## If we don't
Shops keep making or buying listing mockups outside InvAI, which is exactly the "mockup creation" gap `research/16` ranks first among features we lack; the design-to-listing flow stays broken where it matters most for conversion (the photos buyers see first).

## Decision
**Accepted (owner, in chat, 2026-10-02, quote "implement these all").** Distinct from SCR-007 ("original AI designs from a niche brief", still open under OI-17): SCR-007 is about an image model **inventing new artwork**; this feature only **photographs the shop's own already-uploaded design** — no model ever draws or edits the design pixels (decision 0022, separate from and not reopening decision 0006's "AI design generation" cut). Scope: `product/scope.md#listing-photos` (item 18). Spec: `specs/listing-photos.md`. Decision record: `decisions/0022-listing-photos-design-lock.md`. Real image generation stays off by default; OI-25 is open for the owner to turn it on.
Decided by: owner (in chat, 2026-10-02)  Date: 2026-10-02
