# 0022: AI listing photos — the design's pixels are never generated or edited by a model

- Status: accepted (2026-10-02)
- Type: owner

## Context
- The owner approved "AI listing photos" in chat on 2026-10-02, quote: **"implement these all"** — both phases described by the tech lead's plan (`waves/26/wave.md`, `waves/27/wave.md`) and filed as `product/scope-changes/SCR-008-listing-photos.md`.
- This is a different feature from SCR-007 ("original AI designs from a niche brief"), which is still open and undecided under `owner-inbox.md` OI-17, and which would reopen decision 0006's cut of "AI design generation" (an image model **inventing** new artwork). SCR-008 does not reopen 0006: it only photographs a design the shop has **already uploaded**. Nothing here changes 0006's or SCR-007's status.
- The team's plan already assumes this split (`T-26-1` interfaces, `T-26-2` acceptance criterion 1 "drawn by code… no downloaded stock images"), but it needed an explicit, numbered rule before the imaging and AI cards build against it, because the two phases hand design bytes to different places: phase A composites a known design file onto a drawn template (no model involved); phase B hands a *blank, maskable* base image to an image-generation provider and composites the design afterward.
- Evidence for the feature itself: `research/16-growth-opportunities.md` §2 ranks "mockup creation" as the #1 feature gap against 5 competitors; 0 pilots have asked (no pilot is live). See SCR-008 for the full evidence and segment analysis.

## Decision
1. **AI-generated scenes, garments and people for listing photos are in scope** (SCR-008, items 18 in `scope.md`): an image-generation provider (deterministic mock by default; OpenAI GPT Image only when the owner sets `IMAGE_GEN_PROVIDER=openai`, OI-25) may draw a lifestyle scene, a garment and a photoreal or illustrated person around the shop's design.
2. **AI generation of design artwork itself stays cut.** Decision 0006's "AI design generation" cut is unchanged, and SCR-007 (an image model inventing new designs from a niche brief) remains open and undecided under OI-17. This decision does not touch either.
3. **The design's pixels are only ever composited by `invai-imaging`, deterministically, never drawn or altered by any image model.** Concretely:
   - Phase A: the shop's real design file is placed at its real print size on a drawn garment template (built by code in `invai-imaging`, never downloaded stock art) at the real blank hex. No AI call touches the design.
   - Phase B: an image-generation provider is given only a blank, masked base image (garment/scene, no design) and returns a scene; `invai-imaging` then composites the shop's real design onto that scene inside the masked print area. Two design-lock checks (print-region-unchanged, SSIM against the source design) run on every phase-B composite; a failed check rejects the image before the shop ever sees it.
4. **Disclosure follows the source, not the design:** a drawn template is not AI and carries no AI disclosure; an AI-generated scene gets Etsy's AI-use disclosure on the listing, and any photoreal AI person gets the XMP `contains-synthetic-performer` keyword (Amazon rule, `research/10` ~line 239). The design itself is never described as AI-made, because it never was.
5. **Approval gate:** no image (template or AI scene) leaves InvAI — zip download, attach to a draft, or Shopify push — before a person with photos-manage permission approves it.

## Consequences
- Easier: imaging and AI engineers build against one unambiguous rule instead of guessing where the line sits per card; compliance review (Etsy/Amazon disclosure wording) is scoped to phase B and templates marked "illustration, not photo" for Amazon's main-image rule, not to the design-sourcing question.
- Harder: phase B needs a real drift-detection step (two checks, with thresholds imaging must justify and report) instead of trusting the provider's output, which is strictly more build and review work than "just generate the whole photo."
- Enforcement: ADR `0023-listing-photos-pipeline.md` (architect, T-26-1) is the technical reference for the contract shapes; `T-26-2`'s acceptance criteria require templates drawn by code; `T-27-1`/`T-27-2`'s acceptance criteria require the image-gen provider never to receive the design and require the two design-lock checks before any phase-B image can be approved. security-reviewer co-reviews both imaging cards (files: untrusted model output) and the phase-B backend card.
- Links: `product/scope-changes/SCR-008-listing-photos.md`, `specs/listing-photos.md`, `owner-inbox.md` OI-25 (real image generation off by default), `waves/26/wave.md`, `waves/27/wave.md`. Decided by the owner (in chat, 2026-10-02); recorded by product-manager.
