# Metric: shipping_margin

- **Label:** EN "Shipping profit or loss" / ES "Ganancia o pérdida en envíos"
- **Version:** 1 (2026-09-28)   **Owner (acts on it):** product-manager   **Defined by:** data-analyst
- **Spec:** `specs/business-analytics-v2.md`

## Meaning
For orders you shipped with an InvAI label, what the buyer paid for shipping minus what the label cost you.

## Formula
- Per labeled order: `orders.shipping_cents − Σ(shipments.postage_cents + label_fee_cents)` over non-voided shipments.
- Total and per order; `free_shipping_orders` = orders with shipping charged = 0.
- Window and time zone: `[from, to)` in the shop's time zone (`companies.timezone`). By `shipments.labeled_at`.
- Excludes: orders shipped without an InvAI label (cost unknown); counted as `label_attach_rate`'s gap.
- Unit: cents.
- Minimum sample: 30 labeled orders per row; zone and weight cuts need the `dest_zone` and `weight_oz` columns (see Cuts).

## Source
| Table.column | Meaning |
|---|---|
| orders.shipping_cents | shipping charged to the buyer |
| shipments.postage_cents, label_fee_cents, labeled_at, voided_at, carrier, service, weight_oz | what the label cost |

## Marketplace comparison
None: this is InvAI's own number; no marketplace defines it.

## SQL
Path: `invai-docs/metrics/sql/shipping_margin.sql` (moves to `invai-backend/scripts/analytics/` with B-49; see `metrics/definitions/README.md`).
Tested 2026-09-28 on the local dev DB `invai` (shared seed, read-only SELECT, sample workspaces excluded), window 2026-08-28 → 2026-09-29 unless stated. Result below is **SEED** data, not a business result.
- etsy: 105 orders, charged $297.45, labels $767.47, **−$470.02** (−$4.48/order, 50 free-shipping). amazon: 51, charged $0, labels $381.59, −$381.59. shopify: 71, −$309.00. tiktok: 36, −$152.02. Total −$1,313 on 263 orders (SEED; mock postage).

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large, `shop_segment.md`) | Yes | Report per segment only when the cell has ≥ 3 shops; otherwise per shop slug |
| Channel | Yes | |
| Carrier / service | Yes | from shipments |
| Weight band | Yes | `shipments.weight_oz` |
| Destination zone | **Not yet** | needs `shipments.dest_zone` (card T-A3), computed from origin and destination ZIP3 at label time; no address is stored for analytics |

## Target and alarm
- Target: ≥ 0 per channel, or a conscious 'free shipping built into price' choice the shop records
- Alarm (goes into the weekly review): loss per order worsens by ≥ $0.50 over 4 weeks, or a USPS/UPS rate change date passes

## Caveats
- Amazon shipping credits may not be in `orders.shipping_cents` from the CSV import: verify the Amazon CSV mapping before showing Amazon (known gap, integrations-engineer).
- Free shipping is often priced into the item; the report must say 'free-shipping orders: the item price carries the shipping' and show CM per order next to it, never tell the shop to stop free shipping on this number alone.
- Mock carrier postage in the seed.
- PII: the query reads no `buyer_pii`, buyer notes, addresses or personalization text; output is shop slug, channel, ids and numbers only.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
| 1 | 2026-09-28 | First definition | Analytics v2 audit (owner direction 2026-09-28) |
