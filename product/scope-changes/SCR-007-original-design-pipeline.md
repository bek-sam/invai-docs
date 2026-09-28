# SCR-007: Design risk gate, then original AI designs from a niche brief (reopens "AI design generation" in decision 0006)
Filed by: product-manager  Date: 2026-09-28  Type: add (reopens a cut)
Scope section affected: scope.md "MVP: out" (AI design generation); items 10, 11, 16

## Request
Two phases.
- **Phase 1, design risk gate (G-15).** Every new design (uploaded, purchased or generated) gets:
  - OCR text plus the existing trademark check;
  - a USPTO TSDR lookup;
  - a lawful web image-similarity check (Google Cloud Vision Web Detection or TinEye);
  - a perceptual hash against the shop's own catalog.
  The result is a risk score with reasons, using the B-46 thresholds: 60 or more blocks; 25–59 needs a recorded human review.
- **Phase 2, original designs (G-14):**
  1. A niche brief from market signals (item 16), the seasonal calendar and the shop's own sales. It is never built from another seller's image or listing.
  2. An image model generates 2–4 candidates. The prompt refuses brands, characters, celebrities, teams and living artists' styles.
  3. `invai-imaging` upscales to print size and removes the background.
  4. Every candidate passes the phase 1 gate, then gets a mockup and a listing draft.
  5. Batch approval by a human, with a daily cap per shop.
  6. Publish through channel APIs (Shopify now; Etsy after Commercial Access; Amazon, TikTok and Walmart after approval, as asynchronous jobs).

Designs are metered as AI credits.

## Why (new evidence since decision 0006)
Decision 0006 cut AI design generation for IP risk and Etsy's Creativity Standards. New since then (`research/16` §5.2):
- Etsy's Creativity Standards (2025-06-10) explicitly allow seller-prompted AI designs with disclosure ("Designed by").
- Priced, lawful similarity APIs exist: Vision Web Detection at $3.50 per 1,000; TinEye from $0.04 per search. Indemnified models exist: Vertex Imagen; OpenAI Copyright Shield, which excludes trademark claims.
- Competitors have made it table stakes: MyDesigns Dream and Scout, Printify's AI generator, Pythias AI mockups.
- The owner asked directly (2026-09-28) for fast trend-to-listing.

Pain: `research/03` #10 (listing time) and #2 (IP takedowns), which the gate addresses for all designs. Shops confirmed: 0 pilots.

**Explicitly excluded:** copying or imitating other sellers' designs, or collecting them in any way (§5.1: statutory damages up to $150,000 per work, Etsy repeat-infringer bans, inducement liability after *Cox v. Sony* 2026, and a breach of Etsy's API terms). This exclusion is permanent.

## Who it helps
Small and mid shops that design their own products (owner and designer roles).

## Cost and risk
- Effort:
  - Phase 1 is M (about 2 cards: an integrations adapter with mock, the gate in `modules/ai`, a web review panel).
  - Phase 2 is L (about 1 wave: an image-generation adapter with a deterministic mock, jobs, imaging upscale, background removal and hoodie mockup, an Ideas screen, batch approval, credits, evals).
- **Spend (owner):**
  - Similarity: about $0.004–0.04 per design.
  - Generation: about $0.06–0.20 per approved design, so about $30–40 a month for a shop making 200 designs.
  - New outside accounts: Google Cloud Vision or TinEye, and an image-model API.
- **Risk:**
  - IP remains: the gate lowers it but can't prove a design is clean.
  - Pure AI designs have no copyright protection (US Copyright Office Part 2; *Thaler*), and the UI must say so.
  - Listing-spam flags are a risk; the daily cap mitigates it.
  - Etsy and Amazon publishing wait on approvals.
- Fences carried over: no scraping; no competitor data; human approval before any publish; mocks stay in place until the owner approves each account.

## If we don't
Shops use MyDesigns or Printify for design and listing, with no check tied to their production. Our listing tool stays text-only while competitors generate art.

## Decision
Sent to owner (OI-17). The PM recommends:
- **Accept phase 1 now**, with a small spend cap.
- **Defer phase 2** until phase 1 is live and one pilot shop agrees to test it on Shopify.
Decided by: —  Date: —
