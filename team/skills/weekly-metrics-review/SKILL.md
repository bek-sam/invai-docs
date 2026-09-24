---
name: weekly-metrics-review
description: Produce InvAI's weekly metrics review - per-shop pilot KPIs (late rate, overdue orders, film use, reprint rate, scan blocks, label attach, SKU auto-map), trends, plan fit and cost per shop, alarms and who acts - in invai-docs/metrics/weekly/. Use every Monday once a pilot is live, or when asked "how are the pilots doing".
---

# Weekly metrics review

Every week the owner, PM and customer-success read one short page that says, with defined numbers, which shops
are fine, which are slipping and what each person should do about it.

## When to use
- Every Monday morning (the shop's time zone), from the week the first pilot goes live. The data-analyst role
  starts at that trigger.
- Before then, run it once on the seed shop as a rehearsal, and label every number **SEED**.
- Ad hoc when a spike or drop is reported (then add an "investigation" section).

## Steps
1. **Set the window:** last full week, Monday 00:00 to Monday 00:00 in each shop's time zone, plus the 4 weeks
   before it for trend.
2. **List shops** from `invai-docs/customers/*/onboarding.md` with status `live`, with segment (small, mid,
   large), level and go-live date. Shops live under 2 weeks are shown but not judged on trend.
3. **Pull the numbers** with the defined queries only (`invai-docs/metrics/definitions/`, SQL in
   `invai-backend/scripts/analytics/`, or the starters in `.claude/skills/define-metric/starter-metrics.sql`).
   Locally: `docker exec -i local-postgres-1 psql -U invai -d invai -v from=... -v to=... < <file>`. Anywhere
   else: approved read-only views only. Core table per shop:
   - orders imported, by channel,
   - `late_rate` by channel, and `overdue_open` now, against each marketplace's limit (Amazon under 4% late,
     Walmart on-time delivery ≥ 90% and valid tracking ≥ 99% (research 10 §7), TikTok late dispatch enforced above 10% (research 10 §2),
     Etsy 95% on time),
   - `film_use` (sheets sent to the vendor),
   - `reprint_rate` and the top 3 reasons,
   - `scan_block_rate` by station and mismatch reason (a block is the floor doing its job; a rise can mean a
     bad sheet, a mislabeled blank or a training gap),
   - `label_attach_rate` (labels bought in InvAI vs shipped orders),
   - `sku_auto_map_rate` on new imports, and items stuck in `needs_mapping` / `needs_artwork` over 24 hours.
4. **Plan fit and cost.** Per shop: orders, AI credits, users and connections against the plan caps (`billing`
   usage, **Settings → Billing**; caps in `PLAN_CATALOG`, `invai-backend/src/modules/billing/service.ts`).
   Flag shops above 80% of a cap. Add cost per shop from the platform-sre's `cost-review` (AI tokens, label
   fees, hosting share) when available.
5. **Compare** each number to last week and the 4-week average. Mark a change as real only if it clears the
   metric's alarm threshold and the sample minimum from its definition. Otherwise write "no clear change".
6. **Explain each alarm** before reporting it: check `customers/issues.md`, the wave that just shipped
   (`invai-docs/waves/`), incidents (`invai-docs/ops/`), and mock vs real (numbers from mock providers aren't
   business results). Say "cause unknown" when it is.
7. **Write** `invai-docs/metrics/weekly/<YYYY>-W<ww>.md` from `template.md`: 3-line headline first, then the
   per-shop table, alarms with causes, plan fit, cost, and the action list.
8. **Assign actions** by role, never to a shop: customer-success (a churn-risk update or ticket), PM (ranking
   evidence, a spec metric that moved), platform-sre (sync freshness, label success), tech lead (a regression
   after a wave). Anything needing the owner (pricing, a shop conversation) goes in with `escalate-to-owner`.
9. **Hand off:** tell customer-success (they use it for `churn-risk-review` and the weekly customer update)
   and the PM.

## Rules
- MUST use only defined metrics. A new number needs `define-metric` first, or is labelled "draft, not
  defined".
- MUST show counts next to every percentage, and respect minimum samples.
- MUST label seed, estimated and mock-based numbers as such.
- MUST NOT include buyer or staff names, or anything from `buyer_pii`. Shops appear by slug.
- MUST NOT send the review outside the team. Shop-facing numbers go through customer-success and the owner.
- MUST NOT explain a change you haven't checked. "Cause unknown" is a valid answer.

## Done when
- The week's file exists with a headline, a per-shop table with counts, trends, marketplace-limit comparison,
  plan fit, cost (or "not yet available"), and alarms with causes.
- Every alarm has an owner role and an action; owner-level items are in the inbox.
- Customer-success and the PM were told.

## References
- `template.md` (this folder)
- `invai-docs/metrics/definitions/`, `.claude/skills/define-metric/starter-metrics.sql`
- `invai-docs/research/13-team-gap-analysis.md` §4 (data-analyst trigger and KPIs)
- Related playbooks: `define-metric`, `churn-risk-review`, `cost-review`, `experiment-readout`,
  `unit-economics-model`
