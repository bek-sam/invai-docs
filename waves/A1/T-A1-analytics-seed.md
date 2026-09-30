# T-A1: Analytics-ready seed (18 months of realistic history)

| Field | Value |
|---|---|
| Wave | A1 |
| Scope ref | `product/scope.md#mvp-in` items 5, 6, 7, 8 (the seed feeds profit, inventory, shipping and production analytics) |
| Spec | `specs/business-analytics-v2.md` (audit §1, gap analysis §3; feeds T-A3/T-A4/T-A5 acceptance criteria) |
| Owner | backend-foundation |
| Reviewer | reviewer (opus) |
| Co-reviewers | none (decision 0019: QA and data-analyst checks run at the gate) |
| Risk flags | golden path |
| Model | sonnet |
| Backlog ref | B-168 (absorbs B-130) |

## Owned paths (edit)
- `invai-backend/src/db/seed/**`

## Read-only paths
- `invai-backend/src/modules/**` (read the shapes you're seeding for; don't edit service code)
- `invai-docs/metrics/definitions/**`, `invai-docs/metrics/sql/**` (read the definitions your seed must satisfy)

## Depends on
- None (no contract dependency; can run in parallel with T-A2).
- T-A3/T-A4/T-A5's acceptance tests (AC-A1..A7, AC-B1..B3, AC-C1..C4) all read this seed, so this card must land (or at least its shape must be agreed) before those cards' tests are proven against real data. Runtime budget: today's seed already takes 15-20 minutes; say in your report what 18 months adds.

## Interfaces promised
- A demo company (Desert Bloom Tees) with 18 months of **closed** order history (not just the current in-flight window), including:
  - a Q4 seasonal peak (volume roughly 1.5-2x the trailing average in Nov-Dec of at least one year)
  - some late-shipped orders across at least 3 different drivers (personalization, rush, blocked > 24h, vendor turnaround) — enough per driver to clear the ≥30-order minimum sample in `metrics/definitions/` for at least 2 of the 4 drivers
  - realistic scan intervals per station (not the current unrealistically fast/uniform gaps — see `team/lessons.md` 2026-09-24 seed-realism lesson), enough to give ≥100 timed units per station for AC-B2
  - purchase orders with unit-cost changes and lead-time variation across at least 2 supplier/style pairs (for `supplier_trends.md`)
  - a handful (5-10) of repeat Shopify buyers across at least 2 order dates each (Shopify only; no Amazon/Etsy/TikTok/Walmart buyer identifiers touched — those stay Track D/gated)
  - several distinct reprint reasons (at least 3), spread across stations and at least 2 vendors
  - at least one blank style/color with a size-mix gap (one size selling well below its stock share) and at least one dead-stock variant (stock, no movement in 90+ days) worth a nontrivial dollar amount
- Golden-path order counts and Today's queue counts (due today, overdue, at risk, on hold, blocked) are unchanged from today's seed, or the diff is called out explicitly in the report with the golden-path suites re-run green.
- The T-23-8 digest-history seed step and the T-23-10 market-demand cache seed step both still run and produce the same shape they do today (don't regress wave 23b's fixes).

## Acceptance criteria
0. **Spec AC-Seed1** (the canonical numeric criteria for this card, `specs/business-analytics-v2.md` "Acceptance criteria"): ≥18 months of history with a Q4 peak ≥1.5x trailing average; ≥2 late-shipment drivers with ≥30 orders each; ≥1 station with ≥100 realistically-spaced timed scans; ≥2 supplier×style PO pairs with a ≥5% cost change or >3-day lead-time change; ≥2 Shopify buyers with ≥2 orders each; ≥3 distinct reprint reasons across ≥2 stations and ≥2 vendors; ≥1 size-mix gap ≥15 points with ≥30 units sold; ≥1 dead-stock variant at a nonzero dollar value; golden-path counts unchanged or the diff stated and re-verified green.
1. Given a fresh `pnpm db:reset && pnpm db:migrate && pnpm db:seed`, when the seed finishes, then `invai-web/e2e/api-golden-path.spec.ts` (`E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts`) passes with the same order/item counts it passes with today (or the report states the new counts and why).
2. Given the seeded order history, when `metrics/sql/late_rate.sql` (or the equivalent starter query) is run for at least 2 late-shipment drivers, then each returns ≥ 30 orders (clears the minimum-sample threshold used throughout the spec's acceptance criteria).
3. Given the seeded scan history, when press scans are grouped by station and item, then at least one station has ≥ 100 timed units with intervals that vary realistically (not a constant gap) — this is what AC-B2 in the spec needs to show a real median instead of "not enough scans yet".
4. Given the seeded inventory, when a query for stock with no movement in 90+ days is run, then at least one style/color/size variant qualifies as dead stock with a nonzero dollar value, and at least one style has a size selling at least 15 points below its stock share (matches `size_mix_gap.md`'s threshold).
5. Given the seeded purchase orders, when grouped by supplier × style × month, then at least 2 pairs show a unit-cost or lead-time change large enough for `supplier_trends.md`'s ≥3-day or ≥5% thresholds to fire.
6. Edge cases: cancelled orders after `on_sheet` exist in the seed (already required by the golden path — confirm unchanged); the seed includes orders with **no** profit line yet (in-flight / very recent) so AC-A7's "N orders aren't in these numbers yet" has something real to show, without breaking today's totals.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test` in `invai-backend`.
- Exercise for real: fresh `db:reset`/`migrate`/`seed`, then run the starter metric SQL (`.claude/skills/define-metric/starter-metrics.sql`) and the specific queries in "Acceptance criteria" above against the local DB; paste row counts in the report.
- E2E: `E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts` on the fresh seed (golden-path area).
- Time the full seed run and report it.

## Out of scope
- Any change to `src/modules/**` service code (read-only here).
- Track D data shapes (goals history, anomaly-alert history, buyer PII for customer analytics) — not needed until OI-18 is answered.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned. Only one seed card may be open at a time (`src/db/seed/**` is single-owner across the whole workspace while this card is open).
