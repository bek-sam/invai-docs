---
name: churn-risk-review
description: Review every live InvAI shop for churn risk from usage signals (imports, scans, labels, logins), support pain and milestones like the end of the free pilot, rate each green/amber/red with evidence, and draft a save plan for the owner. Use weekly, before a pilot's free period ends, or when a shop goes quiet.
---

# Churn-risk review

Every live shop has a dated risk rating backed by usage numbers and tickets, and every amber or red shop has a
save plan in the owner's hands before it's too late.

## When to use
- Weekly, after the data-analyst's `weekly-metrics-review` (use its numbers).
- 30 days before a pilot's 3 free months end, and again at 14 days.
- When a shop goes quiet: no imports or scans for 2 working days, or an unanswered owner message.
- After an S1 incident that hit a shop.

## Signals (per shop, last 7 days against the 4 before)
| Signal | Source | Amber | Red |
|---|---|---|---|
| Orders imported | `import_runs`, `orders.created_at`; **Settings → Billing** usage | Down 30% | Down 60%, or none for 2 working days |
| Floor adoption | `scans` per day vs items pressed | Scans on under 80% of pressed items | Floor not used on a working day |
| Labels through InvAI | `labels` vs shipped orders | Under 70% (they're still using ShipStation or Pirate Ship) | Under 30% |
| Stuck work | items in `needs_mapping` or `needs_artwork` over 24 h | Over 20 | Over 100, or growing daily |
| Late shipping | late rate (`define-metric`: late-rate) | Up 2 points | Above the marketplace limit (Amazon 4%, Etsy 95% on time, Walmart on-time delivery ≥ 90% and valid tracking ≥ 99%, research 10 §7) |
| Support pain | `customers/issues.md` (created on first use by `triage-support-ticket`) | An open S2, or 3+ open S3 | An open S1, or a repeat S1 in 30 days |
| People | `sessions` (logins by role), staff count | Owner not logged in for 7 days | Only one person still using it |
| Value shown | profile value numbers, **Analytics → Profit** use | Value numbers not yet computed | Shop says it saves no time |
| Commercial | pilot end date, plan fit, plan-limit hits (`PLAN_LIMIT_REACHED`) | Pilot ends in 30 days, no offer | Pilot ends in 14 days, no offer; or price objection logged |

## Steps
1. **List live shops** from `invai-docs/customers/*/onboarding.md` (status `live`), with level (self-serve,
   assisted, white-glove), plan and pilot end date.
2. **Get the numbers.** Ask the data-analyst for the per-shop signal table, or read the latest
   `invai-docs/metrics/weekly/` file (created on first use by `weekly-metrics-review`). Don't query production
   yourself. Locally or on pilots, use the approved views the data-analyst defines.
3. **Read the qualitative side:** open issues and their age, the owner's call notes, and the last weekly
   update's asks.
4. **Rate each shop** green, amber or red. Any single red signal makes the shop red. Two ambers make it amber.
   Write one line of evidence per signal; "no data" is itself amber.
5. **Find the cause**, not the symptom. Scans dropping could mean the scanner broke, staff turnover, a slow
   floor screen, or distrust after a wrong print. Check issues and audit findings for the same period.
6. **Write a save plan** for each amber or red shop, with 1–3 concrete actions, each with an owner and a date:
   - product: push the blocking issue up (PM ranking, or the tech lead for S1 and S2),
   - training: a help article or a short session the owner runs (`write-help-article`, `usability-test-plan`),
   - setup: missing SKU rules, costs or stations (`onboard-shop` steps),
   - commercial: an offer or plan change, which is the owner's decision (`pricing-experiment` if it's a
     pattern).
7. **Write the review** to `invai-docs/customers/churn/<date>.md` (format below). Compare with last week: who
   moved, and why.
8. **Escalate every red shop** with `escalate-to-owner`: the evidence, the save plan, the cost of waiting
   (e.g. "pilot ends Oct 30") and a deadline. Drafts of any message to the shop go through `send-owner-draft`.
9. **Feed the team:** repeated causes across shops go to the PM (`prioritize-backlog` evidence) and to
   `log-lesson` if it's a process miss (for example, go-live without a scanner test).

## Output format
```
# Churn-risk review YYYY-MM-DD
| Shop | Level | Plan / pilot end | Rating (last week → now) | Top signals (with numbers) | Cause | Save plan (action, owner, date) | Inbox id |
Moves since last week:
Patterns across shops:
```

## Rules
- MUST back every rating with numbers or a dated note. "Feels quiet" isn't evidence.
- MUST escalate every red shop to the owner the same day.
- MUST use shop slugs only, with no staff or buyer names.
- MUST NOT contact shops or offer discounts. Commercial moves are the owner's.
- MUST NOT read raw production tables. Numbers come through the data-analyst's approved views.

## Done when
- Every live shop has a rating with evidence per signal, and a change from last week.
- Every amber or red shop has a save plan with owners and dates.
- Every red shop has an owner-inbox entry.
- Cross-shop patterns are passed to the PM.

## References
- `.claude/agents/customer-success.md`, `invai-docs/product/scope.md` (segments)
- Marketplace limits: `invai-docs/00-platform-concept.md` (pain #1), `research/01-shop-workflow.md` §2
- Related playbooks: `weekly-metrics-review`, `define-metric`, `triage-support-ticket`, `onboard-shop`,
  `escalate-to-owner`, `send-owner-draft`
