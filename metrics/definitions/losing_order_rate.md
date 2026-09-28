# Metric: losing_order_rate

- **Label:** EN "Orders that lost money" / ES "Pedidos con pérdida"
- **Version:** 1 (2026-09-28)   **Owner (acts on it):** product-manager   **Defined by:** data-analyst
- **Spec:** `specs/business-analytics-v2.md`

## Meaning
Of the orders you sold, the share that cost more to make and ship than they brought in, before ads.

## Formula
- Numerator: orders with CM2 < 0 (profit lines + all non-voided refund events of that order, net of fee recovered).
- Denominator: orders placed in the window with at least one profit line.
- Window and time zone: `[from, to)` in the shop's time zone (`companies.timezone`).
- Includes reprint lines (a reprint is often why an order loses money).
- Unit: percent; also `loss_cents` (sum of negative CM2).
- Minimum sample: 30 orders.

## Source
| Table.column | Meaning |
|---|---|
| profit_lines.net_cents + ads_cost_cents | CM2 per line |
| refund_events | refunds per order |

## Marketplace comparison
None: this is InvAI's own number; no marketplace defines it.

## SQL
Path: `invai-docs/metrics/sql/losing_orders.sql` (moves to `invai-backend/scripts/analytics/` with B-49; see `metrics/definitions/README.md`).
Tested 2026-09-28 on the local dev DB `invai` (shared seed, read-only SELECT, sample workspaces excluded), window 2026-08-28 → 2026-09-29 unless stated. Result below is **SEED** data, not a business result.
- amazon 2/51 (3.9%, −$55.27), etsy 4/108 (3.7%, −$110.48), shopify 1/75 (1.3%), tiktok 1/38 (2.6%). Counts below 30 would show counts only.

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large, `shop_segment.md`) | Yes | Report per segment only when the cell has ≥ 3 shops; otherwise per shop slug |
| Channel | Yes | |
| Design, blank style, shipping service | Yes | the drill-down the web table shows |

## Target and alarm
- Target: under 2% of orders
- Alarm (goes into the weekly review): above 5% of orders, or loss_cents doubles week over week

## Caveats
- An order-level view: refunds attach to their order regardless of refund date, so this does not add up to the period P&L (by design).
- Estimated buckets make small losses uncertain; show `estimated` on every row.
- PII: the query reads no `buyer_pii`, buyer notes, addresses or personalization text; output is shop slug, channel, ids and numbers only.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
| 1 | 2026-09-28 | First definition | Analytics v2 audit (owner direction 2026-09-28) |
