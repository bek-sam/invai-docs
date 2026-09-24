---
name: experiment-readout
description: Read out an InvAI experiment (pricing offer, onboarding change, feature rollout to some pilots, before/after on a shop) against its pre-registered hypothesis, metric and threshold, with honest small-sample statistics and a keep/change/drop recommendation. Use when an experiment's end date arrives, stops early, or someone asks "did it work?".
---

# Experiment readout

Every experiment ends with a written answer to the question it was set up to ask, judged against the threshold
chosen before it ran, and honest about how little 2–10 shops can prove.

## When to use
- A `pricing-experiment` reaches its readout date or its stop rule.
- A feature or onboarding change was rolled out to some pilots and not others, or to all pilots with a
  before/after.
- The growth-marketer's page or email test ends (after public launch).
- Someone claims a change "worked" and the claim is about to be repeated to the owner or a shop.

## Steps
1. **Load the plan.** Read the pre-registered file: `invai-docs/product/pricing/<slug>.md`, a spec's "Success
   metrics" in `invai-docs/specs/`, or the growth plan in `invai-docs/growth/`. Copy the hypothesis, the
   metric (it must be in `invai-docs/metrics/definitions/`), the threshold, the stop rule and the guardrail.
   **No plan means no readout.** Write a "retrospective look" instead, and label it so.
2. **Check the setup held:** dates, which shops or users were in each group, anything that changed mid-test (a
   wave shipped, a mock switched to a real provider, an outage in `invai-docs/ops/`, Q4 or a TikTok spike, a
   shop's staff change). List every one of these as a confounder.
3. **Pull the data** with the metric's defined SQL, for exactly the pre-registered window and groups. Save the
   query and date in the readout.
4. **Pick the analysis for the sample size** (see `stats.md`):
   - 1–10 shops or accepted offers: report each unit's result and counts ("2 of 3 pilots accepted"). No
     percentages without counts, and no p-values.
   - Before/after on one shop: compare the same weekdays, with enough weeks to cover the weekly cycle, and
     show the 4-week trend before the change.
   - 100+ independent units (trials, sessions, orders within a shop for a floor change): a two-proportion or
     difference-in-means estimate with a 95% interval, and state the unit of analysis. Orders from one shop
     are not independent shops.
5. **Judge against the threshold, not against hope:** met, not met, or inconclusive (the interval or the count
   can't tell). Check the guardrail separately. A met target with a broken guardrail is not a win.
6. **Add what people said** (owner call notes, objections word for word, tickets), marked as qualitative,
   never counted as the result.
7. **Recommend** keep, change (say what), drop, or run longer (only if the plan allows it; don't move
   goalposts), with the one or two reasons that matter.
8. **Write** `invai-docs/metrics/experiments/<slug>.md` from `template.md` and link it from the plan file.
9. **Hand off:** the PM decides and records it with `record-decision` (type: product). Pricing and anything
   shop-facing go to the owner via `escalate-to-owner`. Lessons about how the test was run go to `log-lesson`.

## Rules
- MUST judge against the pre-registered metric, threshold and window. Changing them after seeing data turns
  the readout into exploration, and it must say so.
- MUST report counts with every rate, and intervals when using statistics.
- MUST list confounders and data caveats (seed, estimated, mock) before the conclusion.
- MUST treat stated willingness to pay as qualitative. Accepted offers and plan choices are the result.
- MUST NOT cherry-pick shops, days or segments. Every excluded unit is listed with the reason.
- MUST NOT include buyer data or shop names. Use slugs.

## Done when
- The readout file has plan recap, setup check and confounders, data with counts, the analysis, a verdict
  (met, not met, inconclusive), guardrail result, qualitative notes and a recommendation.
- The plan file links to it; the PM has it; owner-level decisions are in the inbox.

## References
- `template.md`, `stats.md` (this folder)
- `.claude/skills/pricing-experiment/methods.md` (why stated WTP overestimates)
- `invai-docs/metrics/definitions/`
- Related playbooks: `pricing-experiment`, `define-metric`, `weekly-metrics-review`, `record-decision`
