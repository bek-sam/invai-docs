# SCR-003: Design license record with unit-cap counter and checks
Filed by: product-manager  Date: 2026-09-28  Type: add
Scope section affected: scope.md#mvp-in items 3 (SKU mapper and design data), 8 (profit per design), 11 (trademark check)

## Request
Each design gets a license record: source (own, commissioned, Creative Fabrica, Design Bundles, Creative Market, Etsy seller, AI model, other), seller or URL, license type, unit cap or unlimited, subscription-bound with an end date, whether as-is use is allowed, allowed channels, and a proof file (receipt or license PDF). A job counts units sold per design across all channels from order items (one item = one unit). The system warns at 80% of the cap. At 100% of the cap, when a subscription-bound license has ended, or when a channel isn't allowed, adding the design to a new gang sheet is blocked; an owner can override, and the override is logged. The trademark check (text and OCR) runs on every uploaded or purchased design, not only on AI listings. Badges appear in Catalog, a validator warning in the listing flow, and a digest detector for designs near their cap.

## Why (evidence)
- Owner, 2026-09-28: most shops buy ready-made designs (PNG and SVG downloads) and print them.
- `research/16-growth-opportunities.md` §5.3. License terms really cap use: Creative Market Commercial allows 5,000 units and Extended 250,000; Creative Fabrica subscription downloads can be sold only while subscribed; Design Bundles forbids as-is print-on-demand use without edits and a paid add-on; Etsy license sellers often cap at about 500 items and disclaim IP liability. A bought license doesn't protect the shop if the file itself infringes, and Etsy's 2025 Creativity Standards can remove as-is purchased graphics even with a valid license.
- `research/03-pain-points.md` pain #2 (IP takedowns, account suspensions; frequency 5, severity 5).
- Shops confirmed: 0 pilots (none live). Evidence is desk research plus the owner's own view of the market.

## Who it helps
All segments. Owner, office and designer roles. Floor roles see only the block message at sheet build.

## Cost and risk
- Effort: S–M, about 2 cards (contracts and backend: license table, counter job, sheet-build guard, validator; web: Catalog and Listings).
- No new service or spend. One new tenant table with RLS; proof files go through the existing files module.
- Risk: a block at sheet build could hold up production if data is wrong. Mitigations: warn-only mode for the first 2 weeks, and the owner override.
- Public claims about "license compliance" need a compliance-officer review.

## If we don't
Shops keep printing past caps, or after a subscription ends, without knowing it, and list as-is purchased graphics on Etsy. That leads to takedowns and suspensions, which also end their InvAI subscription.

## Decision
Sent to owner (OI-17), together with SCR-004 to SCR-007. The PM recommends **accept**.
Reason: small, no spend, lowers IP risk; the owner asked for this area.  Decided by: —  Date: —
