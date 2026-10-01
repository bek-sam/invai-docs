# Metric: profit_bridge

- **Label:** EN "Why profit changed" / ES "Por qué cambió la ganancia"
- **Version:** 1 (2026-09-28)   **Owner (acts on it):** product-manager   **Defined by:** data-analyst
- **Spec:** `specs/business-analytics-v2.md`

## Meaning
Splits the change in net profit between two periods into 'sold more or fewer' (volume) and 'each sale earned more or less' (rate), and names the designs that moved it most.

## Formula
- Per design d: volume_d = (u1 − u0) × cm0/u0; rate_d = (cm1 − cm0) − volume_d; a design with no units in one period puts all of its change in volume.
- Σ volume + Σ rate = total change exactly (no residual).
- u = units (a reprinted/re-pressed unit still counts as a sale unit, decision 0020); cm = Σ profit_lines.net_cents (CM3) in the period.
- Windows: base [bfrom, bto) and current [from, to), shop time zone, same length recommended.
- Unit: cents.
- Minimum sample: 20 orders in each period; else 'not enough orders to explain'.

## Source
| Table.column | Meaning |
|---|---|
| profit_lines.design_id, net_cents, placed_at | per-design CM |

## Marketplace comparison
None: this is InvAI's own number; no marketplace defines it.

## SQL
Path: `invai-docs/metrics/sql/profit_bridge.sql` (moves to `invai-backend/scripts/analytics/` with B-49; see `metrics/definitions/README.md`).
Tested 2026-09-28 on the local dev DB `invai` (shared seed, read-only SELECT, sample workspaces excluded), window 2026-08-28 → 2026-09-29 unless stated. Result below is **SEED** data, not a business result.
- Week 2026-09-14 vs 2026-09-07: CM3 $1,076.07 → $1,125.61 (+$49.54) = volume −$19.27 + rate +$68.81. Top mover: one design +$78.31 (volume +$55.20, rate +$23.11). Sum checked by hand: −1,927 + 6,881 = 4,954.

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large, `shop_segment.md`) | Yes | Report per segment only when the cell has ≥ 3 shops; otherwise per shop slug |
| Channel | Yes | same method by channel |
| Cost line | Yes | the rate part splits by bucket (fees, blank, label, ads…) using the same per-unit deltas |

## Target and alarm
- Target: none (explanatory)
- Alarm (goes into the weekly review): none; feeds digest D2 and the assistant's 'why' answer

## Caveats
- Refund events (dated by refund) are not in the design bridge; they are shown as their own line in the total.
- Rows where u1 = 0 but cm1 ≠ 0 are cancel reversals or reprint costs of earlier sales; they go to volume.
- PII: the query reads no `buyer_pii`, buyer notes, addresses or personalization text; output is shop slug, channel, ids and numbers only.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
| 1 | 2026-09-28 | First definition | Analytics v2 audit (owner direction 2026-09-28) |
