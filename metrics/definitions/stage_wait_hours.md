# Metric: stage_wait_hours

- **Label:** EN "Where work waits" / ES "Dónde se detiene el trabajo"
- **Version:** 1 (2026-09-28)   **Owner (acts on it):** product-manager   **Defined by:** data-analyst
- **Spec:** `specs/business-analytics-v2.md`

## Meaning
For each production step, how long shirts sit before moving on, so the slowest step (the bottleneck) is visible.

## Formula
- For each item state entered in the window: hours from entering to the next transition (still waiting: to now, counted as `still_waiting`).
- Median and p90 per state; the bottleneck is the critical-path state with the largest median.
- Window and time zone: `[from, to)` in the shop's time zone (`companies.timezone`). By transition `created_at`.
- Unit: hours, one decimal.
- Minimum sample: 30 entries per state.

## Source
| Table.column | Meaning |
|---|---|
| order_item_transitions.order_item_id, to_state, created_at | state history |

## Marketplace comparison
None: this is InvAI's own number; no marketplace defines it.

## SQL
Path: `invai-docs/metrics/sql/stage_wait_hours.sql` (moves to `invai-backend/scripts/analytics/` with B-49; see `metrics/definitions/README.md`).
Tested 2026-09-28 on the local dev DB `invai` (shared seed, read-only SELECT, sample workspaces excluded), window 2026-08-28 → 2026-09-29 unless stated. Result below is **SEED** data, not a business result.
- needs_mapping 12 (all still waiting, median 28.9 h); ready/on_sheet/transfer_in/pressed/packed ~550–690 entries each, median 5.0 h, p90 101–244 h. The flat 5.0 h medians are seed artefacts (T-A1).

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large, `shop_segment.md`) | Yes | Report per segment only when the cell has ≥ 3 shops; otherwise per shop slug |
| State | Yes | |
| Vendor (on_sheet, transfer_in) | Yes | via transfers → gang_sheets.vendor_connection_id |

## Target and alarm
- Target: none until pilots give a baseline
- Alarm (goes into the weekly review): any critical-path median doubles week over week with ≥ 30 entries

## Caveats
- Waiting includes nights and weekends (calendar hours); a working-hours version needs shift hours per shop (`companies.settings.shiftEndHour` only has the end).
- PII: the query reads no `buyer_pii`, buyer notes, addresses or personalization text; output is shop slug, channel, ids and numbers only.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
| 1 | 2026-09-28 | First definition | Analytics v2 audit (owner direction 2026-09-28) |
