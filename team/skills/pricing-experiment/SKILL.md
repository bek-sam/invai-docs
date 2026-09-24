---
name: pricing-experiment
description: Design an InvAI pricing or packaging test (plan price, order caps, per-label fee, AI credits, trial) with a hypothesis, segment, offer, method sized to pilot numbers, success metric and readout plan, for the owner to approve and run. Use when testing willingness to pay, plan fit or label fees.
---

# Pricing experiment

Every pricing change is tested as a written, pre-registered experiment that the owner approves and runs, and
the readout says keep, change or drop.

## When to use
- Before pilots' 3 free months end, to decide what each pilot is offered.
- When usage shows a plan doesn't fit a segment (the weekly metrics review flags it).
- When a competitor moves its price (`competitive-watch`).
- When the per-label fee or AI credit allowance is questioned.

## Know the current numbers (they disagree; say which you test)
- **In code:** `PLAN_CATALOG` in `invai-backend/src/modules/billing/service.ts`:
  - Trial: $0, 300 orders, 3 users, 2 connections
  - Starter: $149, 3,000 orders, 5¢/label
  - Growth: $349, 10,000 orders, 4¢/label
  - Pro: $699, 30,000 orders, 3¢/label
  - Scale: custom, 2¢/label
  Stripe is a mock (`env.mocks.billing`).
- **In the concept:** `00-platform-concept.md` ("Pricing and revenue") proposes $0.10/label.
- **In the cost model:** `calc/cost_model.py` uses $0.15/label and a $1,499 Scale tier.
- **Competitors:** Pythias $199 (500 orders, 2 channels) to $3,000. ShipStation and gang-sheet apps are the
  stack we replace (`research/02-competitors.md` §8: $150–400/mo).

## Steps
1. **Write the hypothesis** in one sentence: "<Segment> shops will <accept / choose / stay on> <offer> because
   <value>, shown by <metric> reaching <threshold>."
2. **Pick one variable.** Price, order cap, label fee, AI credits, trial length, or what's bundled. Never two
   at once with 2–3 pilots.
3. **Pick the segment.** Small, mid, large, or a marketplace-seller type (Etsy-heavy with personalization,
   TikTok spikes). Check plan fit first: ask the data-analyst for each pilot's monthly orders, labels and AI
   credits from `billing.get` (`BillingStatus.usage`) or the **Settings → Billing** screen, against the tier
   caps.
4. **Choose the method for the sample you have** (see `methods.md`):
   - 2–10 shops (now): structured willingness-to-pay interviews the owner runs, anchored on what the shop pays
     today for its stack, plus a real offer at pilot end. Van Westendorp or Gabor-Granger answers are **input
     only**: small samples are fine for input, but stated answers overstate what people pay.
   - After public launch: a pricing-page or checkout test that the growth-marketer runs, sized with the
     data-analyst.
5. **Model the money.** Run `python3 invai-docs/calc/cost_model.py` with the proposed values (copy it to a
   scratch path; don't edit the original, which the data-analyst owns through `unit-economics-model`). Record
   the gross margin per scenario, and the monthly bill for a 100, 300 and 1,000 orders/day shop.
6. **Set the success metric and stop rule** before anything runs. Examples: "2 of 3 pilots accept Growth at
   $349 with a 4¢ label fee." "Label fee questioned in under 1 of 3 calls." Name the guardrail: no pilot
   churns because of the offer.
7. **Write it up** in `invai-docs/product/pricing/<slug>.md` (created on first use) with `template.md`.
8. **Send to the owner** through `escalate-to-owner`. Pricing, plan limits and anything a shop is told are the
   owner's. Include the interview script or offer draft, prepared with `send-owner-draft`.
9. **After it runs,** the data-analyst writes the readout (`experiment-readout`). You then decide keep /
   change / drop and record it with `record-decision` (type: product). If the plan catalog must change, that's
   a task card for the billing area, after the owner approves.

## Rules
- MUST get the owner's approval before any price, limit or offer reaches a shop. Agents never contact shops.
- MUST pre-register: the hypothesis, metric, threshold and stop rule are written before the first
  conversation.
- MUST test one variable at a time, and name the segment.
- MUST show the shop's full monthly bill (plan plus labels) next to what they pay today, not the plan price
  alone.
- MUST NOT edit `PLAN_CATALOG`, `cost_model.py` or pricing copy as part of the experiment.
- MUST NOT treat stated willingness to pay as proof. Only accepted offers or real plan choices count as a
  result.
- MUST NOT offer different prices to shops in a way that looks unfair if they compare notes. Discounts need a
  stated reason (pilot, annual, founding cohort).

## Done when
- `product/pricing/<slug>.md` has a hypothesis, variable, segment, method, cost-model output, metric,
  threshold, stop rule and guardrail.
- An owner-inbox entry exists with the offer or script attached as a draft.
- A readout date and the data-analyst's `experiment-readout` owner are set.

## References
- `template.md`, `methods.md` (this folder)
- `invai-docs/00-platform-concept.md` ("Pricing and revenue"), `invai-docs/tools-stack.md` §2
- `invai-docs/research/02-competitors.md` §2 and §8
- Related playbooks: `experiment-readout`, `unit-economics-model`, `competitive-watch`, `send-owner-draft`,
  `escalate-to-owner`
