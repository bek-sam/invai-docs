# Metric: late_rate

- **Label:** EN "Late shipments" / ES "Envíos tarde"
- **Version:** 1 (2026-09-28)   **Owner (acts on it):** customer-success   **Defined by:** data-analyst
- **Spec:** `specs/business-analytics-v2.md`

## Meaning
Of the orders you shipped, the share that shipped after their ship-by time, and what those late orders have in common.

## Formula
- Numerator: orders with `shipped_at > ship_by`.
- Denominator: orders shipped in the window (cancelled excluded).
- Window and time zone: `[from, to)` in the shop's time zone (`companies.timezone`). By `shipped_at`.
- Driver cuts: channel, personalized, rush, multi-unit order, any unit blocked > 24 h in `needs_mapping`/`needs_artwork` (from `order_item_transitions`). Planned: vendor sheet turnaround over `vendor_connections.turnaround_days`, blank stockout wait.
- Unit: percent.
- Minimum sample: 30 shipped orders per cut value; below, counts only.

## Source
| Table.column | Meaning |
|---|---|
| orders.shipped_at, ship_by, channel, has_personalization, is_rush, item_count, status | the facts |
| order_item_transitions | blocked time per item |

## Marketplace comparison
Amazon late shipment rate < 4%; Etsy Star Seller 95% on-time dispatch with tracking; TikTok late dispatch rate enforced above 10%; Walmart on-time delivery ≥ 90% (research 10 §2, §7).

## SQL
Path: `invai-docs/metrics/sql/late_rate_drivers.sql` (moves to `invai-backend/scripts/analytics/` with B-49; see `metrics/definitions/README.md`).
Tested 2026-09-28 on the local dev DB `invai` (shared seed, read-only SELECT, sample workspaces excluded), window 2026-08-28 → 2026-09-29 unless stated. Result below is **SEED** data, not a business result.
- 263 shipped, **0 late** in every cut (the current shared seed has no late shipped orders; 43 overdue open orders exist). Driver analysis can't be validated on this seed: card T-A1 adds late history.

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large, `shop_segment.md`) | Yes | Report per segment only when the cell has ≥ 3 shops; otherwise per shop slug |
| Channel | Yes | compare with each marketplace's own rule below |
| Driver | Yes | the point of this metric |

## Target and alarm
- Target: under 4% overall and under each channel's limit
- Alarm (goes into the weekly review): above 3% on Amazon or TikTok, or Etsy on-time below 96% (1 point of headroom before the limits)

## Caveats
- InvAI's `ship_by` is the marketplace's dispatch deadline from import; Amazon counts late from ship confirmation, Walmart from the carrier's first scan (research 10 §2, §7). InvAI's shipped_at is the label/tracking push time, so it can read better than Walmart's number.
- Driver cuts are associations, not causes; the report says 'late orders were more often X', never 'X caused it'.
- PII: the query reads no `buyer_pii`, buyer notes, addresses or personalization text; output is shop slug, channel, ids and numbers only.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
| 1 | 2026-09-28 | First definition | Analytics v2 audit (owner direction 2026-09-28) |
