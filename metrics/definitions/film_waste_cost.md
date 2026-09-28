# Metric: film_waste_cost

- **Label:** EN "Wasted film" / ES "Film desperdiciado"
- **Version:** 1 (2026-09-28)   **Owner (acts on it):** product-manager   **Defined by:** data-analyst
- **Spec:** `specs/business-analytics-v2.md`

## Meaning
Money spent on DTF film that carried no design: the empty part of each gang sheet you sent to print.

## Formula
- film_waste_cents = Σ gang_sheets.cost_cents × (1 − utilization), sheets sent or later.
- film_use_pct = Σ(utilization × length_in) ÷ Σ length_in × 100 (starter `film_use`).
- Window and time zone: `[from, to)` in the shop's time zone (`companies.timezone`). By `gang_sheets.created_at`.
- Unit: cents; percent.
- Minimum sample: 10 sheets.

## Source
| Table.column | Meaning |
|---|---|
| gang_sheets.cost_cents, utilization, length_in, status | sheet cost and fill |

## Marketplace comparison
None: this is InvAI's own number; no marketplace defines it.

## SQL
Path: `invai-docs/metrics/sql/film_waste_cost.sql` (moves to `invai-backend/scripts/analytics/` with B-49; see `metrics/definitions/README.md`).
Tested 2026-09-28 on the local dev DB `invai` (shared seed, read-only SELECT, sample workspaces excluded), window 2026-08-28 → 2026-09-29 unless stated. Result below is **SEED** data, not a business result.
- 25 sheets, film $1,033.12, waste **$180.41**, film use 82.5%, 0 sheets without cost.

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large, `shop_segment.md`) | Yes | Report per segment only when the cell has ≥ 3 shops; otherwise per shop slug |
| Vendor | Yes | `gang_sheets.vendor_connection_id` |
| Batch trigger (rush vs scheduled) | Yes | rush batches waste more; that is a real trade-off |

## Target and alarm
- Target: film use ≥ 85% (v1-plan 86–91% on full sheets)
- Alarm (goes into the weekly review): film use below 80% two weeks running

## Caveats
- A batch's short last sheet counts (the shop pays for it).
- `cost_cents` is the vendor price the shop entered; wrong vendor pricing makes this wrong.
- Seed utilization is known to be low (B-111).
- PII: the query reads no `buyer_pii`, buyer notes, addresses or personalization text; output is shop slug, channel, ids and numbers only.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
| 1 | 2026-09-28 | First definition | Analytics v2 audit (owner direction 2026-09-28) |
