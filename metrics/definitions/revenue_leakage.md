# Metric: revenue_leakage

- **Label:** EN "Where your sales money goes" / ES "A dónde se va el dinero de tus ventas"
- **Version:** 1 (2026-09-28)   **Owner (acts on it):** product-manager   **Defined by:** data-analyst
- **Spec:** `specs/business-analytics-v2.md`

## Meaning
Of your gross sales, how much leaves before it becomes contribution: discounts, marketplace fees, refunds, shipping loss and reprints.

## Formula
- Components (cents): discounts (`orders.discount_cents`); fees (`profit_lines.channel_fees_cents` − `refund_events.fee_recovered_cents`); refunds (`refund_events.amount_cents`); shipping loss (Σ max(label − shipping charged, 0) per labeled order); reprint cost (`reprint_cost.md`).
- leakage_pct = Σ components ÷ gross sales (subtotal + shipping charged) × 100.
- Window and time zone: `[from, to)` in the shop's time zone (`companies.timezone`). Orders by placed_at, refunds by refunded_at, reprints by requested_at.
- Only orders that have profit lines count; the rest are reported as `orders_without_profit_line`.
- Unit: cents and percent.
- Minimum sample: 30 orders per channel.

## Source
| Table.column | Meaning |
|---|---|
| orders.subtotal_cents, shipping_cents, discount_cents | gross and discounts |
| profit_lines.channel_fees_cents | fees |
| refund_events | refunds, fee claw-back |
| shipments | label cost |
| reprints, profit_lines | reprint cost |

## Marketplace comparison
None: this is InvAI's own number; no marketplace defines it.

## SQL
Path: `invai-docs/metrics/sql/revenue_leakage.sql` (moves to `invai-backend/scripts/analytics/` with B-49; see `metrics/definitions/README.md`).
Tested 2026-09-28 on the local dev DB `invai` (shared seed, read-only SELECT, sample workspaces excluded), window 2026-08-28 → 2026-09-29 unless stated. Result below is **SEED** data, not a business result.
| Channel | Orders (+ without line) | Fees | Refunds | Ship loss | Reprints | Leakage % |
|---|---|---|---|---|---|---|
| amazon | 51 (+18) | $471.06 | $0 | $381.59 | $24.60 | 30.8 |
| etsy | 106 (+38) | $566.95 | $0 | $477.24 | $55.30 | 21.0 |
| shopify | 71 (+38) | $138.85 | $169.20 | $309.51 | $9.56 | 16.9 |
| tiktok | 36 (+11) | $106.63 | $0 | $152.20 | $6.48 | 15.9 |
105 non-cancelled orders in the window have no profit line yet (not mapped or not recomputed): the report must show that count.

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large, `shop_segment.md`) | Yes | Report per segment only when the cell has ≥ 3 shops; otherwise per shop slug |
| Channel | Yes | fee schedules differ per channel (`finance/fees.ts`) |
| Component | Yes | each one is its own row |

## Target and alarm
- Target: PM to set per channel after pilot weeks (fees are mostly fixed; shipping and reprints are controllable)
- Alarm (goes into the weekly review): any controllable component (shipping loss, reprints, refunds) up ≥ 2 points of gross

## Caveats
- Etsy Offsite Ads fees (12–15%) and TikTok refund commission claw-back are only right if the CSV/API import carries them; today fee tables are estimates when the channel doesn't report actual fees.
- Fees of orders without a profit line are missing: never compare leakage % between periods with different `orders_without_profit_line` shares.
- PII: the query reads no `buyer_pii`, buyer notes, addresses or personalization text; output is shop slug, channel, ids and numbers only.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
| 1 | 2026-09-28 | First definition | Analytics v2 audit (owner direction 2026-09-28) |
