# Metric: blank_stock_health

- **Label:** EN "Blank stock health" / ES "Salud del inventario de prendas"
- **Version:** 1 (2026-09-28)   **Owner (acts on it):** product-manager   **Defined by:** data-analyst
- **Spec:** `specs/business-analytics-v2.md`

## Meaning
How fast your blank stock turns into sold shirts, and how much money sits in blanks that haven't moved.

## Formula
- consumed cost = Σ −qty × blank_variants.cost_cents over `consume` movements in the trailing N days (default 90).
- turns_per_year = consumed cost × 365/N ÷ on-hand value now.
- dead_stock_value = on-hand × cost for variants with on-hand > 0 and no consumption in the window.
- As of now (stock is a point in time).
- Unit: cents; turns with one decimal.
- Minimum sample: 90 days of InvAI history; a shorter history says 'too early'.

## Source
| Table.column | Meaning |
|---|---|
| inventory_movements.kind, qty, created_at | consumption |
| stock_levels.on_hand | stock now |
| blank_variants.cost_cents | valuation |

## Marketplace comparison
None: this is InvAI's own number; no marketplace defines it.

## SQL
Path: `invai-docs/metrics/sql/blank_stock_health.sql` (moves to `invai-backend/scripts/analytics/` with B-49; see `metrics/definitions/README.md`).
Tested 2026-09-28 on the local dev DB `invai` (shared seed, read-only SELECT, sample workspaces excluded), window 2026-08-28 → 2026-09-29 unless stated. Result below is **SEED** data, not a business result.
- 2,281 units on hand ($11,758.89), consumed $2,216.99 in 90 days (the seed holds ~30 days), turns 0.8/yr (understated for that reason), **19 dead variants worth $2,232.74**.

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large, `shop_segment.md`) | Yes | Report per segment only when the cell has ≥ 3 shops; otherwise per shop slug |
| Blank style / color / size | Yes | |
| Location | Yes | `stock_levels.location_id` |
| Supplier | Yes | `blank_variants.supplier` |

## Target and alarm
- Target: turns ≥ 6 per year; dead stock under 10% of stock value
- Alarm (goes into the weekly review): dead stock above 15% of stock value

## Caveats
- Valued at the current blank cost, not at what was paid (PO line cost is better once POs exist).
- A variant bought for an upcoming season looks dead until the season: the report shows the reorder date.
- PII: the query reads no `buyer_pii`, buyer notes, addresses or personalization text; output is shop slug, channel, ids and numbers only.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
| 1 | 2026-09-28 | First definition | Analytics v2 audit (owner direction 2026-09-28) |
