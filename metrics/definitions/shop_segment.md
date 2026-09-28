# Metric: shop_segment

- **Label:** EN "Shop size" / ES "Tamaño de la tienda"
- **Version:** 1 (2026-09-28)   **Owner (acts on it):** product-manager   **Defined by:** data-analyst
- **Spec:** `specs/business-analytics-v2.md`

## Meaning
How big a shop is, by the orders it gets per day, so every other number can be compared among shops of the same size.

## Formula
- Numerator: orders placed in the 28 shop-days before the as-of date (cancelled included: they still cost work).
- Denominator: 28.
- Segment: small < 100 orders/day, mid 100–999, large ≥ 1,000 (`product/scope.md` Segments).
- Excludes: sample workspaces and deleted companies (`realCompanySql()`).
- Unit: orders/day, one decimal.
- Minimum sample: a shop live < 28 days is labelled `new` and not segmented.

## Source
| Table.column | Meaning |
|---|---|
| orders.placed_at | when the order was placed |
| companies.timezone, demo_owner_user_id, settings.demoRetiredAt, deleted_at | shop day and real-shop filter |

## Marketplace comparison
None: this is InvAI's own number; no marketplace defines it.

## SQL
Path: `invai-docs/metrics/sql/shop_segment.sql` (moves to `invai-backend/scripts/analytics/` with B-49; see `metrics/definitions/README.md`).
Tested 2026-09-28 on the local dev DB `invai` (shared seed, read-only SELECT, sample workspaces excluded), window 2026-08-28 → 2026-09-29 unless stated. Result below is **SEED** data, not a business result.
- desert-bloom-tees: 331 orders in 28 days, 11.8/day → **small** (the demo seed is a small-volume shop; the pilots target mid).

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large, `shop_segment.md`) | Yes | Report per segment only when the cell has ≥ 3 shops; otherwise per shop slug |
| Channel | No | Segment is per shop |

## Target and alarm
- Target: none (descriptive)
- Alarm (goes into the weekly review): a shop changes segment two weeks running: tell customer-success (onboarding level may change)

## Caveats
- Staff count and locations are part of the scope definition but are not in the data; volume is the proxy.
- Seasonal shops can swing segment in Q4; use the 28-day window, never a single day.
- PII: the query reads no `buyer_pii`, buyer notes, addresses or personalization text; output is shop slug, channel, ids and numbers only.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
| 1 | 2026-09-28 | First definition | Analytics v2 audit (owner direction 2026-09-28) |
