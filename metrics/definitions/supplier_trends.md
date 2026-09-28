# Metric: supplier_trends

- **Label:** EN "Blank prices and supplier lead time" / ES "Precio de prendas y tiempo de entrega del proveedor"
- **Version:** 1 (2026-09-28)   **Owner (acts on it):** product-manager   **Defined by:** data-analyst
- **Spec:** `specs/business-analytics-v2.md`

## Meaning
Whether what you pay per blank is going up, and how many days each supplier really takes to deliver.

## Formula
- avg unit cost = Σ qty × unit_cost_cents ÷ Σ qty on PO lines, by supplier × style × month of submission.
- lead time = median days from `submitted_at` to `received_at`, fully received POs.
- Unit: cents (one decimal); days.
- Minimum sample: 3 POs per supplier per month for lead time.

## Source
| Table.column | Meaning |
|---|---|
| purchase_orders.supplier, status, submitted_at, received_at | PO timing |
| purchase_order_lines.qty, unit_cost_cents | price paid |
| blank_variants.style_code | grouping |

## Marketplace comparison
None: this is InvAI's own number; no marketplace defines it.

## SQL
Path: `invai-docs/metrics/sql/supplier_trends.sql` (moves to `invai-backend/scripts/analytics/` with B-49; see `metrics/definitions/README.md`).
Tested 2026-09-28 on the local dev DB `invai` (shared seed, read-only SELECT, sample workspaces excluded), window 2026-08-28 → 2026-09-29 unless stated. Result below is **SEED** data, not a business result.
- 0 rows: the seed has no purchase orders. The query parses and runs; needs seeded POs (T-A1).

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large, `shop_segment.md`) | Yes | Report per segment only when the cell has ≥ 3 shops; otherwise per shop slug |
| Supplier / style | Yes | |

## Target and alarm
- Target: none
- Alarm (goes into the weekly review): unit cost up ≥ 5% vs 3 months ago on a style with ≥ 100 units/month (show margin impact per design)

## Caveats
- `inventory_settings.lead_time_days` is what reorder uses; when measured lead time differs by > 3 days, suggest updating it.
- Bella+Canvas moving to SanMar (research 03 §7) will show here as a supplier switch.
- PII: the query reads no `buyer_pii`, buyer notes, addresses or personalization text; output is shop slug, channel, ids and numbers only.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
| 1 | 2026-09-28 | First definition | Analytics v2 audit (owner direction 2026-09-28) |
