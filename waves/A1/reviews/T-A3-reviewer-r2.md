Verdict: approve
# Review T-A3 r2 (zone follow-up): reviewer (opus 5.5), author backend-engineer (opus). Commit 8c616ef (invai-backend)

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint` | tsc clean; biome 434 files, no fixes |
| `vitest run src/modules/analytics/` (DB `invai_rv5_test`, Redis 12) | 3 files, 36/36 passed, including "T-A3 follow-up (review note 2)" |
Test DB dropped, Redis 12 flushed. Uncommitted `src/db/seed/**` (another agent) ignored.

## Checks
- Contract `ShippingMargin`: zone rows keyed `"1"`..`"9"` from `dest_zone`, null zone counted in `shipmentsWithoutZone` and left out of rows (finance-service.ts:419-434); 0 for the other groupings. Additive: no contract change.
- Money: `charged`/`labelCost`/`margin` stay integer cents (sums of `shipping_cents`, `postage_cents + label_fee_cents`); test pins 1000 / 908 / 92.
- Tenancy: `lab` CTE filters `sh.company_id`, the join filters `o.company_id`, under `withTenant`; test shows company B sees no rows and 0 without zone.
- Sort: zone rows sort numerically by key, and keys are unique, so the order is fixed (:457-462).
- Scope: `--stat` shows only `finance-service.ts` and its test. Channel and service totals are unchanged (the channel total is 4 in the test).

## Blocking findings
none

## Optional notes (non-blocking)
a. `shipmentsWithoutZone` now counts labeled orders, not shipments (the contract text says shipments). An order with 2 unvoided labels and no zone counts once. An order with mixed zones takes `max(dest_zone)`, so its null-zone label is not counted. Keeping rows + without = labeledOrders is fair; the architect should align the contract comment, or count shipments.
b. This is from r1 and not in this commit: the `channel`/`service` groupings still sort by `margin` only (:461). Rows come from a query with no ORDER BY, so two groups with equal margins can swap. No test asserts the order of tied rows today. Add `|| a.key.localeCompare(b.key)` before T-A6 shows these rows (this is the same pattern as the T-A4 r1 flake).
