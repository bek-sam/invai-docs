# Metric: contribution_margin

- **Label:** EN "Contribution margin" / ES "Margen de contribución"
- **Version:** 1 (2026-09-28)   **Owner (acts on it):** product-manager   **Defined by:** data-analyst
- **Spec:** `specs/business-analytics-v2.md`

## Meaning
What each order, design, SKU or channel leaves in the shop's pocket after the costs that come with every sale, shown in three steps: after product costs (CM1), after fulfilment (CM2), after ads (CM3, the Profit page's Net).

## Formula
- CM1 = revenue − channel fees (after fees recovered on refunds) − blank − transfer.
- CM2 = CM1 − label − packaging − labor − refunds (cancel reversals on the line + dated refund events).
- CM3 = CM2 − ads (allocated by `cost_settings.ads_allocation`) = Profit page Net.
- Revenue = subtotal − discount + shipping charged (`recomputeProfit`, `finance/service.ts:481`).
- Window and time zone: `[from, to)` in the shop's time zone (`companies.timezone`). Profit lines by `placed_at`; refund events by `refunded_at` (same rule as `getProfit`).
- Excludes: nothing beyond what `profit_lines` excludes; orders without a profit line are reported as `incomplete`, never silently dropped.
- Unit: cents; `cm*_pct` = CM ÷ revenue as a percent (6.5).
- Minimum sample: 30 units per row for a percent; below, cents and counts only.

## Source
| Table.column | Meaning |
|---|---|
| profit_lines.* cost buckets, revenue_cents, net_cents, placed_at | per-unit profit ladder |
| refund_events.amount_cents, fee_recovered_cents, refunded_at, voided_at | refunds in their own period |

## Marketplace comparison
None: this is InvAI's own number; no marketplace defines it.

## SQL
Path: `invai-docs/metrics/sql/contribution_margin.sql` (moves to `invai-backend/scripts/analytics/` with B-49; see `metrics/definitions/README.md`).
Tested 2026-09-28 on the local dev DB `invai` (shared seed, read-only SELECT, sample workspaces excluded), window 2026-08-28 → 2026-09-29 unless stated. Result below is **SEED** data, not a business result.
| Channel | Orders | CM1 | CM2 | CM3 | CM3 % |
|---|---|---|---|---|---|
| etsy | 108 | $3,319.09 | $2,121.50 | $1,351.87 | 25.4 |
| shopify | 75 | $3,062.81 | $1,878.88 | $868.82 | 21.1 |
| amazon | 51 | $1,564.29 | $1,038.25 | $1,038.25 | 37.5 |
| tiktok | 38 | $1,255.26 | $744.97 | $544.77 | 28.4 |
Spot check: CM2 − CM3 equals allocated ads per channel (Amazon has no ad spend, so CM2 = CM3).

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large, `shop_segment.md`) | Yes | Report per segment only when the cell has ≥ 3 shops; otherwise per shop slug |
| Channel | Yes | |
| Design / blank style / SKU (blank variant) | Yes | swap the group key; 'unmapped' kept as its own row |
| Order | Yes | feeds `losing_order_rate` |

## Target and alarm
- Target: CM3 % ≥ 20 per channel (PM to confirm with pilots)
- Alarm (goes into the weekly review): CM3 % drops ≥ 3 points week over week with ≥ 20 orders (same as digest D3)

## Caveats
- Blank, transfer, label and ads can be **estimates** (`profit_lines.estimated`); show the estimated share next to every CM.
- Labor is `cost_settings.labor_minutes_per_item` (an estimate) until `press_minutes_per_unit` replaces it.
- Seed labels are bought on the mock carrier: postage is not real money.
- PII: the query reads no `buyer_pii`, buyer notes, addresses or personalization text; output is shop slug, channel, ids and numbers only.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
| 1 | 2026-09-28 | First definition | Analytics v2 audit (owner direction 2026-09-28) |
