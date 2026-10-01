# Metric: size_mix_gap

- **Label:** EN "Size mix vs stock" / ES "Tallas vendidas vs inventario"
- **Version:** 1 (2026-09-28)   **Owner (acts on it):** product-manager   **Defined by:** data-analyst
- **Spec:** `specs/business-analytics-v2.md`

## Meaning
For each blank style and color, whether your stock is spread across sizes the way your sales are.

## Formula
- sales share = size's units ÷ style×color units sold in the trailing N days (default 90).
- stock share = size's on-hand ÷ style×color on-hand now.
- gap_pts = stock share − sales share, percentage points (+ over-stocked, − under-stocked).
- Unit: points, one decimal.
- Minimum sample: 30 units sold per style×color.

## Source
| Table.column | Meaning |
|---|---|
| order_items.blank_variant_id, state | units sold (a reprinted unit still counts, decision 0020) |
| stock_levels.on_hand | stock |
| blank_variants.style_code, color, size | grouping |

## Marketplace comparison
None: this is InvAI's own number; no marketplace defines it.

## SQL
Path: `invai-docs/metrics/sql/size_mix_gap.sql` (moves to `invai-backend/scripts/analytics/` with B-49; see `metrics/definitions/README.md`).
Tested 2026-09-28 on the local dev DB `invai` (shared seed, read-only SELECT, sample workspaces excluded), window 2026-08-28 → 2026-09-29 unless stated. Result below is **SEED** data, not a business result.
- G64000 Sand: L is 34.6% of sales but 5.5% of stock (−29.2 pts, 27 sold vs 9 on hand); 2XL +11.7 pts. G64000 Navy: 2XL +15.0, XL −11.0.

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large, `shop_segment.md`) | Yes | Report per segment only when the cell has ≥ 3 shops; otherwise per shop slug |
| Style / color | Yes | |
| Channel | Yes | size curves differ by channel |

## Target and alarm
- Target: |gap| ≤ 10 points for every size with ≥ 30 units
- Alarm (goes into the weekly review): a size with gap ≤ −15 points and under 14 days of cover

## Caveats
- Uses the trailing curve only (no forecast; decision 0006). Q4 or a viral design can shift the curve; the reorder screen already uses velocity.
- Feeds reorder quantity split by size as a *suggestion*; nothing orders automatically.
- PII: the query reads no `buyer_pii`, buyer notes, addresses or personalization text; output is shop slug, channel, ids and numbers only.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
| 1 | 2026-09-28 | First definition | Analytics v2 audit (owner direction 2026-09-28) |
