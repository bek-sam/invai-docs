# Review of T-26-2 (round 1)

- Reviewer: compliance-officer on Sonnet 5
- Author: imaging-engineer on Opus 5.5
- Verdict: approve

Scope of this review: marketplace-policy risk flag only (presets, checks, XMP, illustration flag). Code correctness, security (zip caps, company-prefix) and budgets are the reviewer/security-reviewer's territory.

## Evidence I re-ran / read
| Source | What I checked |
|---|---|
| `invai-imaging/app/photos.py` (`PRESETS`, `run_checks`, `background_is_white`, `fill_ratio`, `xmp_packet`, `encode`) | Preset numbers, check logic, XMP write path |
| `invai-imaging/README.md` listing-photos section | Documented presets, failure codes, XMP behavior match code |
| `invai-imaging/tests/test_photos.py` (grep) | `illustration_not_photo`, `background_not_white`/`fill_below_min`/`too_small`, `contains-synthetic-performer` XMP round-trip all have tests |
| `invai-docs/decisions/0022-listing-photos-design-lock.md`, `0023-listing-photos-pipeline.md` | Design-lock rule, disclosure-follows-source rule, who decides `xmp_subjects` (backend, not imaging) |
| `invai-docs/specs/listing-photos.md` §"Marketplace rules and their sources" | Spec already flags Amazon synthetic-performer and Etsy disclosure wording as third-party/unverified, assigns re-verification to me |
| `research/10-marketplace-engineering-rules.md` ~line 239 | `contains-synthetic-performer`, effective 2026-07-22, sourced `[3P]` (geekseller.com blog) |
| WebSearch (official pages 403/redirected — Etsy, Amazon Seller Central, Walmart seller portal all gate behind login/captcha, consistent with the known limitation) | Amazon main-image rules, Etsy photo count/AI disclosure, Shopify/TikTok/Walmart preset numbers — see findings below, all third-party aggregator sources `[3P]` since official pages weren't fetchable |

## Acceptance criteria (AC4, AC5 — the ones in my scope)
| # | Met? | Evidence |
|---|---|---|
| AC4 presets/checks | Yes | `PRESETS` dict and `run_checks` in `photos.py:54-63,276-292`; tested `tests/test_photos.py:206-224` |
| AC5 XMP | Yes | `xmp_packet`/`encode` in `photos.py:212-251`; round-trip test `tests/test_photos.py:233-238`; empty list writes no packet (code path confirmed) |

## Findings on marketplace rule accuracy

**Amazon main image (`amazon_main`: 2000×2000, white required, fill ≥0.85, longest ≥1600, photo required)**
- Pure white RGB 255/255/255, ≥85% fill, ≥1600px minimum (2000+ recommended): matches current third-party-aggregated guidance `[3P]`, consistent with what `research/10` calls "long-standing Amazon Image Requirements." Numbers in code match. **Correct, not blocking.**
- "Main image must be a professional photograph, not a drawing/illustration/graphic/mockup": confirmed by multiple third-party sources `[3P]` (official seller-central page is sign-in gated, not fetchable). `illustration_not_photo` on every `drawn` template for `amazon_main` only is the **right, conservative call** — it blocks the rule we'd otherwise violate by default. **Not blocking.**
- 8×8-block halo exclusion from the pure-white check: this excludes JPEG-ringing pixels right at the product edge from the exact-255 test, not the whole background. For a human reviewer or Amazon's own listing-quality tooling (which samples the field well away from the product edge), this is standard, defensible practice, not a loosening that would pass an actually-non-white image. It also grows the same way for PNG output, where there's no JPEG ringing to protect against — slightly more lenient than necessary there, but not a violation (PNG output still has to be literal 255 outside the grown mask, and the grown region is tiny relative to the frame). **Acceptable, not blocking.**
- **New finding, not yet in the card or spec**: third-party sources are specific that for **adult apparel**, Amazon requires the **main image to be on-model** (standing, no mannequin/dress form) rather than flat. Today every template this card ships is `drawn: bool = True` by default (`garments.py:313`), so `illustration_not_photo` already blocks *every* view (flat and on-model alike) from passing `amazon_main` — the on-model-vs-flat question never gets a chance to matter yet, so there is nothing to block here. **Non-blocking now; flag for wave 27**: once phase B produces real/AI-rendered (non-illustration) images, `amazon_main`'s checks need an apparel on-model requirement in addition to `photo_required`, or a flat real photo of adult clothing will pass today's checks even though Amazon would reject it. Recommend T-27-1/T-27-3 add this.

**Etsy (`etsy`: 2700×2025, ≥2000px longest, 4:3)**
- ≥2000px: matches current guidance. **Not blocking.**
- "Up to 20 images": I initially found conflicting third-party claims (some blogs still say 10). Etsy raised the per-listing limit from 10 to 20 in August 2025 per multiple sources, so the spec's "up to 20" is current, not stale. **Confirmed, not blocking** (the count cap itself isn't enforced in this card — that belongs to whichever module builds the photo set/attach flow).
- Etsy mockups of a seller's own printed/physical original design do not themselves require an AI disclosure (the disclosure is about the *item/design* being AI-made, filed under Etsy's Creativity Standards "Designed by a seller" category, disclosed in the listing description) — this matches the spec's framing and decision 0022's "disclosure follows the source" rule. This card writes no disclosure text at all (that's backend/AI, wave 27); it only provides the XMP mechanism. **Not blocking.**

**Shopify (`shopify`: 2048×2048, no white/fill requirement)**
- 2048×2048 is Shopify's own recommended (not mandated) size; Shopify has no enforced background-color rule for product images. Preset correctly carries no `white_required`/`min_fill`. **Correct, not blocking.**

**TikTok (`tiktok`: 1600×1600, ≥600px, no white required)**
- Minimum-pixel number is conservative versus guidance (600–1080px cited). **Not blocking.**
- Third-party sources disagree on strictness of a white background for the TikTok Shop main/cover image: some call it a "strict requirement... actively enforced," others simply "allowed/recommended." The official Partner Center page needs JavaScript and wasn't fetchable (expected, per `research/10`'s own note). The preset doesn't set `white_required`, consistent with the spec's "white allowed" framing. **Non-blocking, but flag as a real gap**: if TikTok in fact requires white for its cover image, a non-white `tiktok` composite would pass this card's checks and then fail on submission. Recommend `policy-change-watch` or a fresh check against `partner.tiktokshop.com` (logged in) before any shop submits a non-white TikTok cover image for real.

**Walmart (`walmart`: 2000×2000, white required, ≥1500px, no fill-ratio check)**
- White-required and size are consistent with third-party guidance (2000×2000, RGB 255 background). **Not blocking.**
- Some third-party sources also describe an ≥85% fill requirement for Walmart's main image, which this preset doesn't check (`min_fill: None`). The spec itself only commits Walmart to "square, ≥1500px, white main" — no fill ratio — so the card isn't violating its own spec, and the official Walmart seller portal page was captcha-gated and unverifiable today. **Non-blocking; recommend adding `min_fill=0.85` to the `walmart` preset once confirmed**, since it's a one-line change and cheap insurance if the rule is real.

## XMP `contains-synthetic-performer`
- Mechanism (write arbitrary `dc:subject` keywords into JPEG APP1/PNG iTXt) is generic and correct; imaging never decides *when* to request the tag — that's the caller's (backend's) job per decision 0023 point 3 ("decided from the requested scene kind... never from inspecting the output"). This card's own templates (including `on_model_white`, a "neutral grey illustration, not photoreal" per the README) never get this tag today, correctly, since nothing in phase A calls it with that subject. **Correct separation of concerns, not blocking.**
- The July 2026 effective date and exact keyword are still sourced `[3P]` (a trade blog), as the spec itself already states and assigns to me to re-verify before phase B ships to a real shop. I could not reach Amazon's own current policy page (sign-in redirect) to upgrade this past `[3P]`. **Non-blocking for this card** (no disclosure decision is made here); **carry forward to wave 27 (T-27-1/T-27-3)**: re-confirm the keyword and effective date against Amazon's own developer/seller policy page (not just the blog) before any real shop's photoreal AI person ships without it.

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (imaging-engineer's `invai-imaging/**`; I made no edits, read-only review)
- [x] Nothing outside scope
- [x] Tests exercise the behavior (illustration flag, background/fill/size failures, XMP round-trip)
- [x] Decisions recorded where needed (0022, 0023 already cover the design-lock and disclosure-follows-source rules this card depends on)

## Optional notes (not blocking)
1. Wave 27 follow-up: add an apparel on-model requirement to `amazon_main` checks once phase B can produce non-illustration images (today `illustration_not_photo` masks the gap).
2. Wave 27 follow-up: re-verify `contains-synthetic-performer` keyword/date against Amazon's own policy page, not only the third-party blog.
3. Recommend a `policy-change-watch` pass to confirm TikTok Shop's cover-image white-background strictness and Walmart's fill-ratio requirement against their authenticated seller portals (both were unreachable today — sign-in/CAPTCHA gated); add `min_fill` to the `walmart` preset if confirmed.
4. Etsy's 20-photo limit (raised from 10 in August 2025) is current; no action needed, noting it here since it's easy to find stale "10 photos" advice.
