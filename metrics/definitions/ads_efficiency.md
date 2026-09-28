# Metric: ads_efficiency

- **Label:** EN "Ads: blended and break-even ROAS" / ES "Anuncios: ROAS combinado y de equilibrio"
- **Version:** 1 (2026-09-28)   **Owner (acts on it):** product-manager   **Defined by:** data-analyst
- **Spec:** `specs/business-analytics-v2.md`

## Meaning
How much revenue each ad dollar comes with overall (MER), and the ROAS each channel needs just to break even at today's margins.

## Formula
- MER = total revenue ÷ total ad spend (all channels).
- Channel ROAS = channel revenue ÷ channel ad spend (same as `get_ad_performance`).
- Break-even ROAS = revenue ÷ CM2 (= 1 ÷ CM2 ratio). ROAS below it means ads cost more than the contribution they come with.
- Window and time zone: `[from, to)` in the shop's time zone (`companies.timezone`). Revenue from profit lines by placed_at; spend from `ad_spend.day`.
- Unit: ratio, two decimals.
- Minimum sample: $100 spend and 30 orders per channel.

## Source
| Table.column | Meaning |
|---|---|
| ad_spend.amount_cents, day, channel | spend |
| profit_lines.revenue_cents, net_cents, ads_cost_cents | revenue, CM2 |

## Marketplace comparison
None: this is InvAI's own number; no marketplace defines it.

## SQL
Path: `invai-docs/metrics/sql/ads_efficiency.sql` (moves to `invai-backend/scripts/analytics/` with B-49; see `metrics/definitions/README.md`).
Tested 2026-09-28 on the local dev DB `invai` (shared seed, read-only SELECT, sample workspaces excluded), window 2026-08-28 → 2026-09-29 unless stated. Result below is **SEED** data, not a business result.
- MER 5.70 on $2,480.54 spend; break-even 2.38. Shopify ROAS 3.13 vs break-even 2.01; Etsy 5.98 vs 2.51; TikTok 7.08 vs 2.58; Amazon no spend.

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large, `shop_segment.md`) | Yes | Report per segment only when the cell has ≥ 3 shops; otherwise per shop slug |
| Channel | Yes | |
| Campaign | Spend only | the data has no campaign revenue (attribution is by channel) |

## Target and alarm
- Target: every channel's ROAS ≥ 1.3 × break-even
- Alarm (goes into the weekly review): a channel's ROAS below break-even with ≥ $100 spend (digest D4 extension)

## Caveats
- **Attribution is by channel, not by ad**: channel revenue includes organic sales, so ROAS overstates the ad's effect. Say so every time (existing D4 note).
- This file's `cm3_cents` subtracts spend by day (cash view); the Profit page allocates spend to orders. Both are labelled.
- Etsy forbids connecting Etsy data to ad platforms: spend comes in, nothing goes out.
- PII: the query reads no `buyer_pii`, buyer notes, addresses or personalization text; output is shop slug, channel, ids and numbers only.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
| 1 | 2026-09-28 | First definition | Analytics v2 audit (owner direction 2026-09-28) |
