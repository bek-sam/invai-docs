# Pricing experiment: <title>

- **Slug:** <slug>   **Status:** draft | approved by owner | running | read out
- **Owner-inbox id:** <id>   **Readout by:** data-analyst on YYYY-MM-DD

## Hypothesis
<Segment> shops will <behavior> for <offer> because <value>, shown by <metric> ≥ <threshold>.

## Variable (one)
| | Today (source) | Test |
|---|---|---|
| e.g. Growth price | $349 (`PLAN_CATALOG`) | $299 |

## Segment and shops
Segment, number of shops, how they were chosen (customer-folder slugs, never real names).

## Method
From `methods.md`, and why it fits this sample size.

## Money (from a scratch copy of `calc/cost_model.py`)
| Shop size | Monthly bill today (plan + labels) | Monthly bill in test | Our gross margin |
|---|---|---|---|
| 100/day | | | |
| 300/day | | | |
| 1,000/day | | | |

## Success metric, threshold, stop rule, guardrail
- Metric:
- Success if:
- Stop early if:
- Guardrail (must not get worse):

## Drafts for the owner
Links to `send-owner-draft` items (offer email, interview script).

## Result (filled after the readout)
Link to `invai-docs/metrics/experiments/<slug>.md`. Decision: keep / change / drop, and the decision record id.
