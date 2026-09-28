# Metric: press_minutes_per_unit

- **Label:** EN "Press time per shirt" / ES "Tiempo de planchado por prenda"
- **Version:** 1 (2026-09-28)   **Owner (acts on it):** product-manager   **Defined by:** data-analyst
- **Spec:** `specs/business-analytics-v2.md`

## Meaning
How long one shirt really takes at the press, measured from the floor scans, so labor cost in profit stops being a guess.

## Formula
- Per station: gaps between consecutive successful press scans, kept when 0.1–10 minutes (longer = break or setup; shorter = double scan or synthetic row).
- Median and p75 minutes per unit; units per active hour = 60 × timed units ÷ Σ kept gaps.
- Window and time zone: `[from, to)` in the shop's time zone (`companies.timezone`). By `scans.scanned_at`.
- Unit: minutes (2 decimals).
- Minimum sample: 100 timed units per station.

## Source
| Table.column | Meaning |
|---|---|
| scans.action = 'press', ok, station_id, scanned_at | the timing |
| cost_settings.labor_minutes_per_item | the estimate it replaces |

## Marketplace comparison
None: this is InvAI's own number; no marketplace defines it.

## SQL
Path: `invai-docs/metrics/sql/press_minutes_per_unit.sql` (moves to `invai-backend/scripts/analytics/` with B-49; see `metrics/definitions/README.md`).
Tested 2026-09-28 on the local dev DB `invai` (shared seed, read-only SELECT, sample workspaces excluded), window 2026-08-28 → 2026-09-29 unless stated. Result below is **SEED** data, not a business result.
- 41 press scans on one station, all at identical timestamps → 0 timed units (the seed's scans are synthetic). The query correctly refuses to time them. Needs realistic scan times in the seed (T-A1).

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large, `shop_segment.md`) | Yes | Report per segment only when the cell has ≥ 3 shops; otherwise per shop slug |
| Station | Yes | |
| Garment class (tee vs hoodie) | Yes | via order_items → blank style |
| Person | Internal only | never shown per person in shop-facing analytics without the owner's decision (staff monitoring) |

## Target and alarm
- Target: measured median within 25% of the cost setting, then use the measured value
- Alarm (goes into the weekly review): measured differs from the setting by > 25% for 2 weeks: suggest updating the labor setting

## Caveats
- Press time only; pick, QC and pack have their own scans and can use the same method.
- Batch pressing (several units per press cycle) makes the gap per unit look shorter; that is real throughput.
- PII: the query reads no `buyer_pii`, buyer notes, addresses or personalization text; output is shop slug, channel, ids and numbers only.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
| 1 | 2026-09-28 | First definition | Analytics v2 audit (owner direction 2026-09-28) |
