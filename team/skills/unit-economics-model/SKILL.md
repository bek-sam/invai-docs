---
name: unit-economics-model
description: Model InvAI's unit economics - per-label margin, cost and revenue per shop by segment, AI and infra cost per tenant, plan fit and gross margin - from invai-docs/calc/cost_model.py and tools-stack.md, reconciled with the prices in code and, once pilots run, real usage. Use before a pricing decision, a pricing experiment, a vendor negotiation, or monthly after cost-review.
---

# Unit economics model

The owner and PM see what each shop size earns and costs InvAI, built from one reproducible model whose
assumptions match the prices actually in the code, with every unverified number flagged.

## When to use
- Before `pricing-experiment` or any plan or label-fee decision.
- Before the owner negotiates with EasyPost or another vendor (the label fee drives margin).
- Monthly, after platform-sre's `cost-review`, to swap estimates for actuals.
- When code, the concept doc and the model disagree on a price (they do today; see below).

## Sources
- `invai-docs/calc/cost_model.py`: scenarios (Pilot 3 shops × 300/day, Growth 20 × 400, Scale 100 × 400),
  tiers, label price and cost, fixed vendor costs, Claude costs, Stripe ACH fees, and a label-fee sensitivity
  table. Its "U" values are unverified.
- `invai-docs/tools-stack.md` §2 (the same model explained) and §4 ("Verify before committing").
- **Prices in code:** `PLAN_CATALOG` in `invai-backend/src/modules/billing/service.ts`.
- **Actuals (once pilots run):** `labels.postage_cents` and `labels.label_fee_cents`, `usage` (orders
  imported, labels bought, AI credits), `ai_credit_ledger`, `subscriptions`, and platform-sre's cost reports
  in `invai-docs/ops/`.

## Known mismatches to reconcile first (as of 2026-09-24)
| Item | cost_model.py | Concept / tools-stack | Code (`PLAN_CATALOG`) |
|---|---|---|---|
| Label fee to shops | $0.15 | $0.10 recommended | 5¢ Starter, 4¢ Growth, 3¢ Pro, 2¢ Scale |
| EasyPost cost per label | $0.08 (unverified) | negotiate to ≤ $0.05 | — |
| Scale tier | $1,499 | Custom | $0 (custom) |
| Trial | not modeled | — | $0, 300 orders, 3 users, 2 connections |
| AI design generation | $63 / $630 / $3,360 per month | cut from v1 (`decisions/0006-v1-cuts.md`) | not built |
| Pilot revenue | full price | 3 months free | — |

With the code's fees and EasyPost at list price, margin at Scale falls to about 6% (`run_scenarios.py code-prices`). Put this in front of the PM and owner, not in a footnote.

## Steps
1. **Keep `calc/cost_model.py` as the baseline.** The data-analyst owns `invai-docs/calc/**` and may change
   the baseline, adding a dated version line to the module docstring for each change (for example
   `Version 2026-10-01: EasyPost cost per label from the signed quote, $0.08 → $0.06`). What-if questions go
   in `run_scenarios.py` (this folder) as named scenarios, not in the baseline.
2. **Run the baseline and the reconciliation scenarios** from the workspace root:
   ```
   python3 .claude/skills/unit-economics-model/run_scenarios.py baseline
   python3 .claude/skills/unit-economics-model/run_scenarios.py code-prices
   python3 .claude/skills/unit-economics-model/run_scenarios.py concept-prices
   python3 .claude/skills/unit-economics-model/run_scenarios.py no-design-gen
   ```
   Add a scenario for the question at hand (for example a small-shop plan at $49–99 from `product/scope.md`'s
   pricing hypothesis). The "Label fee revenue ($0.15)" row label in the model's output is static text: it
   still says $0.15 when a scenario overrides `LABEL_PRICE`. Read the price from the scenario header line
   (`LABEL_PRICE $…`), not the row label.
3. **Build the per-shop view by segment** (the model is per scenario; the owner thinks per shop). For a small
   (50 orders/day), mid (300/day) and large (1,000/day) shop, list revenue (plan plus label fees) and direct
   cost (label platform fee, AI use, Stripe, hosting share), then contribution per month and per order. Use
   `worksheet.md` for the table.
4. **Per-label margin:** fee charged minus platform cost per label, per plan. Flag any plan where it's
   negative at list cost, and the negotiated EasyPost price that makes it positive.
5. **AI and infra cost per tenant:** from `cost-review` actuals when available, else from `FIXED` and `CLAUDE`
   in the model divided by shops. Compare included AI credits per plan (`aiCreditsPerMonth`) with what an
   average shop uses.
6. **Swap in actuals** once pilots run: labels per order, AI credits per order, orders per day, and real
   vendor invoices. Mark each input as `verified`, `actual (source, date)` or `U`.
7. **Sensitivity:** show which 2–3 inputs move gross margin most (label fee and EasyPost cost always; Claude
   model choice, hosting). The model's `sensitivity()` table covers labels.
8. **Write** `invai-docs/metrics/unit-economics/<YYYY-MM-DD>.md` from `worksheet.md`: the reconciliation
   table, scenario outputs (paste the tables), per-segment shop economics, per-label margin, AI and infra per
   tenant, sensitivities, unverified inputs, and 2–3 findings in plain words.
9. **Hand off:** the PM (for `pricing-experiment` and scope), platform-sre (cost lines), and the owner for
   anything about prices, vendor contracts or spending, through `escalate-to-owner`.

## Rules
- MUST state which price source each number uses (model, concept or code), and highlight where they disagree.
- MUST mark every unverified input ("U" in the model, or tools-stack §4), and never present a U-based margin
  as fact.
- MUST keep money in the model's units and state them (the model uses dollars; the code uses cents).
- MUST NOT change prices, plan limits or `PLAN_CATALOG`. Findings become an owner decision and then a task
  card.
- MUST NOT use buyer data. Only counts, fees and costs per shop.

## Done when
- The dated model file has the reconciliation table, all four scenario runs plus any new one, per-segment shop
  economics, per-label margin by plan, AI and infra cost per tenant, sensitivity and a list of unverified
  inputs.
- Any negative-margin plan or label fee is raised to the owner with options.
- The scenario code needed to reproduce every number is in `run_scenarios.py`.

## References
- `run_scenarios.py`, `worksheet.md` (this folder)
- `invai-docs/calc/cost_model.py`, `invai-docs/tools-stack.md` §2 and §4, `invai-docs/00-platform-concept.md`
  ("Pricing and revenue")
- Related playbooks: `pricing-experiment`, `cost-review`, `weekly-metrics-review`, `escalate-to-owner`
