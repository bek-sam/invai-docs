# Metric: design_lifecycle_stage

- **Label:** EN "Design stage" / ES "Etapa del diseño"
- **Version:** 1 (2026-09-28)   **Owner (acts on it):** product-manager   **Defined by:** data-analyst
- **Spec:** `specs/business-analytics-v2.md`

## Meaning
Where each design is in its life: new, growing, steady, declining or dead (listed but not selling), so you know what to push and what to retire.

## Formula
- Units = non-reprint, non-cancelled order items with the design (one item = one unit), last 365 days.
- u4 = units in the last 28 days; p4 = the 28 days before.
- Stage, first match: dead (active listing, no sale in 60 days) → new (first sale < 8 weeks ago) → growing (u4 ≥ 3 and u4 ≥ 1.25 × p4) → declining (p4 ≥ 3 and u4 ≤ 0.75 × p4) → steady (a sale in 60 days) → inactive.
- As of a date, shop time zone.
- Unit: category; counts of designs and units per stage.
- Minimum sample: the 3-unit floors above (same as `MIN_UNITS` in analyst-queries).

## Source
| Table.column | Meaning |
|---|---|
| order_items.design_id, is_reprint, state | units |
| orders.placed_at | timing |
| listings.state, design_id | listed designs |

## Marketplace comparison
None: this is InvAI's own number; no marketplace defines it.

## SQL
Path: `invai-docs/metrics/sql/design_lifecycle.sql` (moves to `invai-backend/scripts/analytics/` with B-49; see `metrics/definitions/README.md`).
Tested 2026-09-28 on the local dev DB `invai` (shared seed, read-only SELECT, sample workspaces excluded), window 2026-08-28 → 2026-09-29 unless stated. Result below is **SEED** data, not a business result.
- 40 designs, all **new** (612 units in 4 weeks): the seed has only ~30 days of history, so no design can be anything else. B-130 (18 months of history) is needed to test the other stages.

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large, `shop_segment.md`) | Yes | Report per segment only when the cell has ≥ 3 shops; otherwise per shop slug |
| Channel | Yes | a design can be growing on TikTok and dead on Etsy |
| Niche | Yes | `market_design_niches` |

## Target and alarm
- Target: dead listed designs under 20% of active listings
- Alarm (goes into the weekly review): dead designs above 30% of active listings (suggest a cleanup)

## Caveats
- The market module's statistical trend (`signals.ts`, OLS on 26 weeks) is the better trend for long histories; this rule is the simple one for the digest and for shops with < 13 weeks. When both exist, the market trend wins and the stage says so.
- 'Never sold' cannot be dated: listings have no created date; such designs count as dead only after the shop has 60 days of history in InvAI.
- PII: the query reads no `buyer_pii`, buyer notes, addresses or personalization text; output is shop slug, channel, ids and numbers only.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
| 1 | 2026-09-28 | First definition | Analytics v2 audit (owner direction 2026-09-28) |
