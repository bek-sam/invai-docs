---
name: define-metric
description: Define one InvAI metric so everyone computes it the same way - name, plain-language meaning, exact formula, tested SQL, source tables, owner, segment cuts, target and caveats - in invai-docs/metrics/definitions/. Use before a spec names a success metric, before a KPI is shown to the owner or a shop, or when two numbers for "the same thing" disagree.
---

# Define a metric

Each number the team reports (late rate, film use, reprint rate, minutes saved) has one written definition and
one tested query, so a pilot's number means the same thing every week and in every doc.

## When to use
- A spec's "Success metrics" section needs a metric that has no definition yet (`write-spec`).
- The weekly review, a churn review or an experiment needs a new number.
- Two sources disagree. Example: the seed shows about 70% film use across all sent sheets, while v1-plan says
  86–91% "on full sheets". Both can be true; the definition says which one we report.
- An analytics event is being added (`instrument-analytics-event`); define the metric it feeds first.

## Steps
1. **Check it doesn't exist:** `ls invai-docs/metrics/definitions/`. Extend an existing definition rather than
   adding a near-duplicate.
2. **Name it** in snake_case (`late_rate`, `film_use`, `reprint_rate`, `scan_block_rate`, `sku_auto_map_rate`,
   `label_attach_rate`, `minutes_saved`), with a plain-language label in English and Spanish for anything a
   shop sees.
3. **Write the meaning in one sentence** a shop owner would agree with: "Of the orders you shipped this week,
   the share that shipped after their ship-by time."
4. **Write the exact formula:** numerator, denominator, time window, time zone (a shop's day, e.g.
   `America/Phoenix` as in `orders/shipby.ts`), what's excluded (cancelled, reprints, test orders), and units.
   Follow the conventions: money in cents, `*Pct` as 6.5 for 6.5%, ratios 0..1.
5. **Tie it to the source of truth.** Name the tables and columns (`invai-backend/src/db/schema/*.ts`,
   snake_case in SQL) and the state or reason enums (`invai-contracts/src/states.ts`,
   `schemas/production.ts`). If the metric depends on an outside definition, quote the rule and link it:
   Amazon counts late shipment from ship confirmation, Walmart from the carrier's first scan, TikTok late
   dispatch, Etsy Star Seller 95% (`research/10-marketplace-engineering-rules.md` §2 "Performance" row, and
   §3–7 per channel; Walmart §7). Say how InvAI's number differs from the
   marketplace's.
6. **Write and test the SQL.** Start from `starter-metrics.sql` (this folder: late rate, overdue open, film
   use, reprint rate and reasons, scan block rate, label attach rate). Save the final query as
   `invai-backend/scripts/analytics/<metric>.sql` (folder to be created; the data-analyst owns it). Run it
   locally:
   ```
   docker exec -i local-postgres-1 psql -U invai -d invai -v from=2026-08-25 -v to=2026-09-25 < invai-backend/scripts/analytics/<metric>.sql
   ```
   Check the result on the seed shop by hand for a few rows (open the order in **Orders** and compare).
7. **Define segment cuts:** by shop segment (small, mid, large from `product/scope.md`), channel, station,
   role, and new vs established shop. Say which cuts are valid; small samples (fewer than ~30 events) get "not
   enough data", not a percentage.
8. **Set owner, target and alarm:** who acts when it moves (PM, customer-success, platform-sre), the target,
   and the threshold that triggers a note in the weekly review.
9. **Write caveats:** seed data vs real data, estimated values (for example `profit_lines.estimated`), mock
   providers (labels bought on the mock carrier aren't real postage), and what the metric can't see (minutes
   saved is an estimate until timed).
10. **Save** `invai-docs/metrics/definitions/<metric>.md` from `template.md`, and add a row to
    `invai-docs/metrics/definitions/README.md` (the index; create it if missing).
11. **Review:** the PM checks that the meaning matches the product question. If the metric reaches shops or
    public copy, the compliance-officer checks the claim.

## Rules
- MUST publish one definition per metric; a changed formula gets a version line and a date, and old reports
  keep their version.
- MUST test the SQL and record the date, the database and the result.
- MUST NOT read or output buyer PII (`buyer_pii`, raw payloads, addresses, personalization text). Group by
  `company_id`, never by buyer.
- MUST NOT query any shared or deployed database directly. Outside local, use approved read-only views (to be
  created) and the owner's approval for access.
- MUST NOT report a percentage when the denominator is under the minimum sample; report the counts.

## Done when
- `metrics/definitions/<metric>.md` has name, en/es label, meaning, formula, source tables, marketplace
  comparison if relevant, SQL path, test result, cuts, owner, target, alarm and caveats.
- The SQL runs cleanly on the local seed and was spot-checked by hand.
- The index lists the metric, and the PM reviewed it.

## References
- `template.md`, `starter-metrics.sql` (this folder)
- `invai-docs/research/13-team-gap-analysis.md` §4 (data-analyst: pilot KPIs, taxonomy), §5.5
- `invai-backend/src/db/schema/` (tables), `invai-contracts/src/states.ts`,
  `invai-contracts/src/schemas/production.ts`
- Related playbooks: `weekly-metrics-review`, `experiment-readout`, `instrument-analytics-event`, `write-spec`
