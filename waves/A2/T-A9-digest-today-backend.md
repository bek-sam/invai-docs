# T-A9: Digest D9–D13, D2 names the bridge mover, Today actions service (B-176, B-177 backend)

| Field | Value |
|---|---|
| Wave | A2 |
| Scope ref | `product/scope.md#mvp-in` items 14, 17 |
| Spec | `specs/business-analytics-v2.md` Track E; AC-E1, AC-E1b..E1f, AC-E2 (backend half), AC-E4, AC-E5, AC-G1 (digest leg) |
| Owner | backend-engineer (areas: digest, today) |
| Reviewer | reviewer (opus) |
| Co-reviewers | backend-foundation (migration, sonnet), security-reviewer (tenancy, sonnet) |
| Risk flags | tenancy, migration, money |
| Model | opus |

## Owned paths (edit)
- `invai-backend/src/modules/digest/**` (detectors, snapshot, facts, rank, render and en/es copy, tests)
- `invai-backend/src/modules/today/**` (new `actions.ts`, router wiring replacing T-A10's stubs, jobs, tests)
- `invai-backend/src/db/schema/digest.ts` or a new `today` schema file for the click/actions table, plus the generated migration (`pnpm db:generate --name today_actions`)
- `invai-backend/src/modules/analytics/finance-service.ts` (+ test): only the A1 note: add a stable tiebreak (label, then key) to the channel and service groupings sorted by margin. (`shipmentsWithoutZone` is fixed in the contract text by T-A10; no backend change.)

## Read-only paths
- `invai-backend/src/modules/analytics/**` (call the exported services; don't change them beyond the grant above), `src/lib/**`, `src/db/client.ts`, `invai-contracts/**`, `invai-web/**`

## Known on start (T-A10 report)
- After T-A10's contract commit, backend typecheck fails at `digest/rank.ts(14,39)` (`config.ts:44` severity has no D9–D13 weights) and `digest/build.ts(315,11)` (`DIGEST_DETECTOR_KEYS` in `db/schema/digest.ts:37` lacks D9–D13; type-only, no migration). Both are yours to fix first.

## Depends on
- T-A10 contract (0.10.0) committed: detectors D9–D13, action kinds, `today.actions`, `today.recordActionClick`.

## Interfaces promised
- `d9ShippingLoss`, `d10LosingOrders`, `d11StockHealth`, `d12BlankCost`, `d13BreakEven` in `digest/detectors.ts`, included by `detect()`.
- `computeTodayActions(tx, ctx, { date }) -> TodayActions` in `today/actions.ts`: the digest snapshot, detectors and `rank()` on a trailing 7-day window ending yesterday in the org timezone. Storage per the architect's ruling 2 (`reviews/plan-architect.md`): tables `today_actions` and `today_action_clicks` (shapes there), an hourly sweep in `today/jobs.ts` that builds any shop whose local date has no set (jobId `today-actions-${companyId}-${date}`, rebuild = delete+insert in one tx), read = plain SELECT; before the build, `generatedAt: null`, `actions: []` and the read enqueues the build.

## Acceptance criteria
1. D9: loss per labeled order worse by ≥ $0.50 vs the 4-week median and ≥ 30 labeled orders → action "Review shipping prices on {{channel}}" with $ impact; below either minimum, no action (AC-E1). Numbers from `analytics.shippingMargin`.
2. D10: losing orders > 5% of orders and ≥ 30 orders → "Review your losing orders" with $ impact (AC-E1b), from `analytics.losingOrders`.
3. D11: dead stock > 15% of stock value, or a size gap ≤ −15 points with < 14 days of cover → action naming style/color (and size for a gap) (AC-E1c), from `analytics.inventoryHealth`. Use the new seed's gaps (BC3001 Black 3XL +18.0 pts, Dusty Blue L −18.6 pts), not the old G64000 Sand premise.
4. D12: a supplier's unit cost ≥ 5% above 3 months ago → action naming supplier and style with margin impact (AC-E1d), from `analytics.supplierTrends`.
5. D13: fires only when fixed costs are set and pace is below break-even; never with no fixed costs (AC-E1e), from `analytics.breakEven`.
6. D2 names the same top mover that `analytics.profitBridge` ranks first for the same period (AC-E1f).
7. Each detector has a fires / doesn't-fire pair of tests at the threshold edge. Digest copy for D9–D13 exists in en and es; no buyer data in any param.
8. `today.actions` returns at most 5 ranked actions with integer-cent `impactCents` and the digest's fixed wording kinds and deep links; zero firing detectors → `actions: []`, `steady: true` (AC-E2). `today.recordActionClick` is idempotent: two calls → one row, same `clickedAt`.
9. Tenancy: the new table has `company_id` and RLS (the RLS coverage test passes); company A's call never shows company B's actions or clicks (AC-E4). designer, presser, packer, receiver and vendor get `FORBIDDEN` on both procedures (AC-E5).
10. AC-G1 digest leg: the digest snapshot's net for the last completed week equals `analytics.unitEconomics` (dimension order, no channel) to the cent, via `computeNet`.
11. Job: the sweep and build job run twice for the same date leave one set of actions; rows older than 90 days are purged (test). Unknown `key` on `recordActionClick` → `ACTION_NOT_FOUND`.
12. A1 note: channel/service groupings with equal margin sort the same way on every run (test with a tie).

## Verification
- `cd invai-backend && pnpm typecheck && pnpm lint && pnpm test src/modules/digest src/modules/today src/modules/analytics src/db 2>&1 | tail -n 40` (full suite runs at the gate)
- Live: `PORT=3161 REDIS_URL=redis://localhost:6379/<own db> pnpm dev:api`; sign in as `owner@desertbloom.test`, call `today.actions` (expect ≤ 5 actions with cents), click one twice (same `clickedAt`); as `designer@` expect `FORBIDDEN`. Build a digest preview and show which of D9–D13 fire on the seed and why.
- Migration: generated by drizzle-kit, not hand-edited; applies on `invai_test`.

## Out of scope
- Web (T-A7). B-146 fee tables and price refresh. B-224 (Today alert bodies' language) stays a backlog row. Track D.

## Budget
- About 3 hours. Escalate if blocked for more than about 30 minutes or if the card grows.
