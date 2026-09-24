# Unit economics YYYY-MM-DD

Model: `calc/cost_model.py` at <git -C invai-docs log -1 --format=%h -- calc/cost_model.py>, scenarios from `run_scenarios.py`.

## 1. Price sources reconciled
| Item | Used here | Source | Status (verified / actual / U) |
|---|---|---|---|
| Label fee per plan | | code / concept / model | |
| EasyPost cost per label | | | U until the contract |
| Plan prices | | `PLAN_CATALOG` | |

## 2. Scenario outputs
Paste the tables for baseline, code-prices, concept-prices, no-design-gen, and any new scenario.

## 3. One shop per month, by segment
| | Small (50/day) | Mid (300/day) | Large (1,000/day) |
|---|---|---|---|
| Orders per month (×30) | 1,500 | 9,000 | 30,000 |
| Plan (from `PLAN_CATALOG` caps) | Starter $149 | Growth $349 | Pro $699 |
| Label fees charged (orders × fee) | | | |
| **Revenue** | | | |
| Label platform cost (above 3,000 free labels, platform-wide) | | | |
| AI (credits used × cost per credit) | | | |
| Hosting and services share | | | |
| Stripe (ACH 0.8% capped $5 + Billing 0.7% + $0.50) | | | |
| **Contribution** | | | |
| Contribution per order | | | |
| What they pay today for the stack we replace (from profiles) | | | |

## 4. Per-label margin by plan
| Plan | Fee charged | Cost at list ($0.08) | Cost negotiated ($0.05) | Margin at each |
|---|---|---|---|---|

## 5. AI and infra per tenant
| Line | Per shop per month | Source |
|---|---|---|
| Claude (listing copy, assistant) | | model / cost-review |
| Trademark (USPTO + Signa) | | |
| Hosting share | | |
| Included AI credits vs used | | `ai_credit_ledger` |

## 6. Sensitivity (top 3 inputs)
| Input | Low | Base | High | Gross margin at Scale |
|---|---|---|---|---|

## 7. Unverified inputs
-

## 8. Findings (plain words, 2–3)
1.
