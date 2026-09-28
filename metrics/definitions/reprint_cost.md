# Metric: reprint_cost

- **Label:** EN "Reprint cost" / ES "Costo de reimpresiones"
- **Version:** 1 (2026-09-28)   **Owner (acts on it):** product-manager   **Defined by:** data-analyst
- **Spec:** `specs/business-analytics-v2.md`

## Meaning
What reprints cost you in extra transfers and ruined blanks, by reason.

## Formula
- Per reprint: transfer cost of the item ÷ (1 + reprints of that item) + blank cost when `blank_consumed`.
- Same rule as `fulfillmentHealth` (`invai-backend/src/modules/ai/analyst-queries.ts`).
- Rate: reprints ÷ distinct items that reached `pressed` in the window (starter `reprint_rate`).
- Window and time zone: `[from, to)` in the shop's time zone (`companies.timezone`). By `reprints.requested_at`; cancelled reprints excluded.
- Unit: cents; rate in percent.
- Minimum sample: 30 items pressed.

## Source
| Table.column | Meaning |
|---|---|
| reprints.reason, blank_consumed, status, requested_at, station_id | reprint facts |
| profit_lines.transfer_cost_cents, blank_cost_cents | cost base |
| order_item_transitions.to_state = 'pressed' | denominator |

## Marketplace comparison
None: this is InvAI's own number; no marketplace defines it.

## SQL
Path: `invai-docs/metrics/sql/reprint_cost.sql` (moves to `invai-backend/scripts/analytics/` with B-49; see `metrics/definitions/README.md`).
Tested 2026-09-28 on the local dev DB `invai` (shared seed, read-only SELECT, sample workspaces excluded), window 2026-08-28 → 2026-09-29 unless stated. Result below is **SEED** data, not a business result.
- peel: 17 reprints of 540 items pressed (3.1%), $95.94. One reason only in the seed.

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large, `shop_segment.md`) | Yes | Report per segment only when the cell has ≥ 3 shops; otherwise per shop slug |
| Reason | Yes | `REPRINT_REASONS` |
| Station / presser | Yes | `reprints.station_id`; presser only in aggregate, never a named person in a shop-facing report (training, not blame) |
| Design / vendor (via gang sheet) | Yes | a vendor with high 'peel' or 'misprint' is a supplier-quality signal |

## Target and alarm
- Target: under 2% of items pressed
- Alarm (goes into the weekly review): rate up ≥ 1 point week over week with ≥ 100 items pressed, or one reason > 50% of reprints (digest D6 already alerts on spikes)

## Caveats
- Labor for the reprint and the late-shipment risk are not in the cost.
- An estimate: the transfer share assumes equal cost per print.
- PII: the query reads no `buyer_pii`, buyer notes, addresses or personalization text; output is shop slug, channel, ids and numbers only.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
| 1 | 2026-09-28 | First definition | Analytics v2 audit (owner direction 2026-09-28) |
