# Review of T-6-4 (round 2) — compliance-officer co-review

- Reviewer: compliance-officer on Sonnet 5
- Author: ai-engineer on Opus
- Verdict: **approve**

Round 1 blocked on: Shopify CSV columns not matching Shopify's current product-CSV format (no
real per-variant option values, so the importer couldn't tell variants apart). Fix: backend
`937ef89`. Static/test evidence shared with `T-6-4-reviewer-r2.md`, not re-run here.

## Re-check: does the Shopify CSV now match Shopify's current product-CSV format?

| Check | Result | Evidence |
|---|---|---|
| One `Handle` per product, shared listing fields only on the first row | pass, unchanged | `Title`/`Body (HTML)`/`Vendor`/`Tags`/`Published`/`Image Src` still only set on `isFirstOfHandle`. |
| Every variant row carries its own option value(s) | **pass — this is the fix** | `Option1 Name: "Color"` / `Option1 Value: <real color>` and `Option2 Name: "Size"` / `Option2 Value: <real size>` are now set on **every** row, including continuation rows, sourced from `blank_variants.color`/`.size` (display names, not codes) via `variantRowsForDraft`. This matches Shopify's own bulk-export shape: option-name columns repeat on every row of a Handle; only the non-variant listing fields are first-row-only. |
| Variants under one Handle are distinguishable / no duplicate combinations | pass | New test asserts `Set of "Handle|Option1 Value|Option2 Value"` has size equal to row count (no collisions); production code also defensively dedupes on `color\0size` per handle and skips a would-be collision rather than emit it. |
| Real SKU per variant, no placeholder | pass, unchanged from r1 | `Variant SKU` still comes from `blank_variants.sku`; `variantRowsForDraft` still throws if nothing resolves. |
| AI disclosure still in the description | pass, unchanged | `description()` helper untouched by this commit. |

**Verdict on the specific r1/r1-compliance finding: resolved.** A shop exporting a 6-color × 6-size
Shopify draft now gets 36 rows that Shopify's importer can actually tell apart by Color/Size, with
real SKUs, under one Handle — the failure scenario from round 1 (upload collapses to one variant
or errors on duplicate combos) no longer applies.

## Standing, non-blocking finding (carried from round 1, still unresolved)
Etsy's `production_partner: "DTF transfer printer"` fixed-text column is unchanged by `937ef89`
(this commit only touches the Shopify branch and `variantRowsForDraft`). This remains the
already-logged M-23 gap: Etsy requires the structured `production_partner_ids` field, not
description/CSV text, and this text is wrong for a shop that prints in-house. Not this card's
scope (AC2 asked for real SKUs + the Shopify branch only) and not a regression — re-flagging only
so it isn't lost; recommend its own card.

## Checks
- [x] Shopify CSV columns now match the current marketplace upload format (this round's ask).
- [x] AI disclosure intact (unchanged by this commit; re-verified).
- [x] Real SKUs, no placeholders (unchanged from round 1's approval on this point).
- [x] No test weakened in the fix commit (scan against `937ef89`'s own parent: no hits).

No blocking findings this round.
