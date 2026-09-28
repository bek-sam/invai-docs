# Metric: break_even

- **Label:** EN "Break-even orders" / ES "Pedidos para cubrir costos fijos"
- **Version:** 1 (2026-09-28)   **Owner (acts on it):** product-manager   **Defined by:** data-analyst
- **Spec:** `specs/business-analytics-v2.md`

## Meaning
How many orders a month you need to cover your fixed costs (rent, salaries, software), and whether this month's pace gets there.

## Formula
- break_even_orders = ceil(fixed monthly costs ÷ CM3 per order over the trailing window).
- pace = orders in the window × 30 ÷ window days; operating profit pace = CM3 × 30 ÷ days − fixed.
- Fixed monthly costs: a new shop setting (`cost_settings.fixed_monthly_cents`, card T-A2); none today.
- Unit: orders/month; cents.
- Minimum sample: 30 orders in the window.

## Source
| Table.column | Meaning |
|---|---|
| profit_lines.net_cents, order_id | CM3 per order |
| cost_settings.fixed_monthly_cents (new) | fixed costs |

## Marketplace comparison
None: this is InvAI's own number; no marketplace defines it.

## SQL
Path: `invai-docs/metrics/sql/break_even.sql` (moves to `invai-backend/scripts/analytics/` with B-49; see `metrics/definitions/README.md`).
Tested 2026-09-28 on the local dev DB `invai` (shared seed, read-only SELECT, sample workspaces excluded), window 2026-08-28 → 2026-09-29 unless stated. Result below is **SEED** data, not a business result.
- With a test value of $2,500 fixed: CM3 $14.61/order → 172 orders/month to break even; pace 255/month → operating profit pace +$1,224.60.

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large, `shop_segment.md`) | Yes | Report per segment only when the cell has ≥ 3 shops; otherwise per shop slug |
| Month | Yes | |

## Target and alarm
- Target: pace ≥ 1.2 × break-even
- Alarm (goes into the weekly review): pace below break-even two weeks running

## Caveats
- Labor is inside CM (per unit); fixed costs must not include per-unit labor again. The settings screen must say so.
- A run-rate, not a forecast.
- PII: the query reads no `buyer_pii`, buyer notes, addresses or personalization text; output is shop slug, channel, ids and numbers only.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
| 1 | 2026-09-28 | First definition | Analytics v2 audit (owner direction 2026-09-28) |
