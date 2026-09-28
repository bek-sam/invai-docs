# Metric: action_adoption_rate

- **Label:** EN "Actions taken" / ES "Acciones tomadas"
- **Version:** 1 (2026-09-28)   **Owner (acts on it):** product-manager   **Defined by:** data-analyst
- **Spec:** `specs/business-analytics-v2.md`

## Meaning
Of the ranked actions InvAI showed a shop, the share someone clicked or marked useful: whether the analytics change what shops do.

## Formula
- Numerator: action insights with ≥ 1 click (`digest_clicks`) — and separately with an up vote.
- Denominator: action insights in ready digests whose week ended in the window.
- Later (T-A12): the same for the Actions panel on Today, and 'acted within 7 days' where the action is observable (label bought, listing drafted, PO created).
- Unit: percent.
- Minimum sample: 30 actions shown.

## Source
| Table.column | Meaning |
|---|---|
| digests.status, week_end | digest |
| digest_insights.section, detector | actions |
| digest_clicks, digest_feedback.vote | response |

## Marketplace comparison
None: this is InvAI's own number; no marketplace defines it.

## SQL
Path: `invai-docs/metrics/sql/action_adoption.sql` (moves to `invai-backend/scripts/analytics/` with B-49; see `metrics/definitions/README.md`).
Tested 2026-09-28 on the local dev DB `invai` (shared seed, read-only SELECT, sample workspaces excluded), window 2026-08-28 → 2026-09-29 unless stated. Result below is **SEED** data, not a business result.
- D6: 1 shown, 1 clicked; D7: 2 shown, 0 clicked (local test data).

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large, `shop_segment.md`) | Yes | Report per segment only when the cell has ≥ 3 shops; otherwise per shop slug |
| Detector | Yes | shows which analysis is worth keeping |
| Role | Yes | owner vs office |

## Target and alarm
- Target: ≥ 30% of actions clicked
- Alarm (goes into the weekly review): a detector below 10% for 4 weeks with ≥ 30 shown: PM reviews it

## Caveats
- A click is intent, not the action done.
- PII: the query reads no `buyer_pii`, buyer notes, addresses or personalization text; output is shop slug, channel, ids and numbers only.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
| 1 | 2026-09-28 | First definition | Analytics v2 audit (owner direction 2026-09-28) |
