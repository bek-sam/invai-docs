# Metric: stockout_exposure

- **Label:** EN "Sold but waiting on blanks" / ES "Vendido pero esperando prendas"
- **Version:** 1 (2026-09-28)   **Owner (acts on it):** customer-success   **Defined by:** data-analyst
- **Spec:** `specs/business-analytics-v2.md`

## Meaning
Units you already sold that can't be pressed because their blank is out of stock, and how much revenue and how soon they are due.

## Formula
- Open items in `ready`, `needs_artwork`, `on_sheet`, `transfer_in` whose blank variant has Σ stock_levels.available ≤ 0.
- Output: units, distinct blanks, revenue at risk (Σ unit_price_cents), earliest ship-by.
- Point in time (now).
- Unit: count and cents.
- Minimum sample: none (each unit matters).

## Source
| Table.column | Meaning |
|---|---|
| order_items.state, blank_variant_id, unit_price_cents, ship_by | open units |
| stock_levels.available | stock |

## Marketplace comparison
None: this is InvAI's own number; no marketplace defines it.

## SQL
Path: `invai-docs/metrics/sql/stockout_exposure.sql` (moves to `invai-backend/scripts/analytics/` with B-49; see `metrics/definitions/README.md`).
Tested 2026-09-28 on the local dev DB `invai` (shared seed, read-only SELECT, sample workspaces excluded), window 2026-08-28 → 2026-09-29 unless stated. Result below is **SEED** data, not a business result.
- 0 units waiting on a blank (no blank has available ≤ 0 in the seed).

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large, `shop_segment.md`) | Yes | Report per segment only when the cell has ≥ 3 shops; otherwise per shop slug |
| Blank | Yes | |
| Ship-by day | Yes | |

## Target and alarm
- Target: 0 units
- Alarm (goes into the weekly review): any unit with ship-by within 48 hours

## Caveats
- `on_sheet` and `transfer_in` items usually have their blank reserved; available ≤ 0 there can mean an over-reservation, not a shortage.
- Lost sales from listings that were paused for low stock can't be seen (no demand data); this is only sold units.
- PII: the query reads no `buyer_pii`, buyer notes, addresses or personalization text; output is shop slug, channel, ids and numbers only.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
| 1 | 2026-09-28 | First definition | Analytics v2 audit (owner direction 2026-09-28) |
