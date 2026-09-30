# T-A4: Operations and shipping analytics (reprint/film $, waits, measured press time, late drivers, `destZone`)

| Field | Value |
|---|---|
| Wave | A1 |
| Scope ref | `product/scope.md#mvp-in` item 5 (production floor), item 7 (shipping) |
| Spec | `specs/business-analytics-v2.md` Track B; AC-A4, AC-B1, AC-B2, AC-B3, AC-E4, AC-E5 |
| Owner | backend-engineer (production, shipping) |
| Reviewer | reviewer (opus) |
| Co-reviewers | backend-foundation (migration), security-reviewer (no address/PII stored) |
| Risk flags | tenancy, migration, pii |
| Model | opus |
| Backlog ref | B-171 (implements B-153) |

## Owned paths (edit)
- `invai-backend/src/modules/analytics/router.ts` (add **only** the `operations` procedure registration; land after T-A3 lands, don't touch T-A3's existing registrations)
- `invai-backend/src/modules/analytics/operations-service.ts` (**create**: reprint cost by reason/station/vendor, film waste $, waits per step (median/p90/still-waiting) and bottleneck step, measured press minutes per unit per station, late-shipment drivers with counts)
- `invai-backend/src/modules/shipping/**` (zone only: add a `destZone` computation at label-purchase time, from origin/destination ZIP3 held in memory — no new field storing an address or ZIP)
- `invai-backend/src/db/schema/shipping.ts` (add `shipments.dest_zone` smallint, nullable) + its migration (`pnpm db:generate --name shipping_dest_zone`, run **after** T-A3's finance migration is committed, per `CLAUDE.md`'s migration-collision rule)

## Read-only paths
- `invai-backend/src/modules/production/**` (read `scans.scanned_at`, `order_item_transitions`; don't edit — this card reads timing, T-A1's seed provides realistic data)
- `invai-backend/src/modules/analytics/finance-service.ts`, `shared.ts` (read only; don't edit T-A3's files)

## Depends on
- T-A2 (contract stub for `analytics.operations`, `Shipment.destZone`) must land first.
- T-A3 must land first (shares `analytics/router.ts`; also frees the migration slot).
- T-A1 (seed) needed for AC-B2 (≥100 timed units) and AC-B3 (≥30 orders per driver) to have real numbers, not "not enough data".

## Interfaces promised
- `analytics/router.ts` gains one new registration: `operations`. No edits to `unitEconomics`/`losingOrders`/`leakage`/`shippingMargin`/`profitBridge`/`breakEven`.
- `shipments.dest_zone` is set once, at label-purchase time, by a pure function taking origin/destination ZIP3 (never persisting the ZIP itself beyond the existing shipment address fields that already exist for label printing — no new column holds an address, ZIP or name).

## Acceptance criteria
1. **AC-A4**: Given a shipment labeled after this card lands, when it is bought, then `shipments.dest_zone` holds a zone 1-9 and no new column holds an address, ZIP or name (test asserts the exact column list on `shipments`).
2. **AC-B1**: Given reprints and sheets in the period, when `analytics.operations` is called, then reprint cost by reason and film waste $ match `metrics/sql/reprint_cost.sql` and `film_waste_cost.sql`.
3. **AC-B2**: Given press scans at realistic intervals (from T-A1's seed), when `analytics.operations` is called, then measured press minutes per unit per station appear with the timed count; when the measured median differs from the labor setting by > 25% with ≥ 100 timed units, the response includes a suggestion pointing at Settings → Costs; with fewer timed units it returns "not enough scans yet" instead of a number.
4. **AC-B3**: Given late-shipped orders in the seed, when `analytics.operations` returns late-shipment drivers, then each cut shows counts, cuts under 30 orders show counts only (no rate), and any label/copy uses "were more often", never "caused".
5. **AC-B/C-screen1**: Given a shop below every metric's minimum sample overall (e.g. live under 2 weeks), when `analytics.operations` is called, then the response's `hasEnoughHistory` flag is `false` (in addition to, not instead of, each metric's own per-widget threshold), so the web screen (T-A7) can show one whole-screen "not enough history yet" state.
6. **AC-E4/AC-E5**: Given two companies A and B, `analytics.operations` for A shows no row of B; a role without `finance.read` gets `FORBIDDEN`.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test` in `invai-backend`.
- Exercise for real: buy a label on the running API (mock EasyPost) and confirm `dest_zone` is populated and no new PII column exists (`\d shipments` in psql, or the schema test).
- Migration: `pnpm db:generate --name shipping_dest_zone`; if the drizzle journal collides with T-A3's, regenerate (this card regenerates, since it lands second).

## Out of scope
- Finance/profit analytics (T-A3), inventory/design analytics (T-A5), any web screen (T-A7), the assistant tools (T-A8).
- Per-person (named presser) speed views — stations only, pending an owner decision (spec open question 4).
- Track D — gated on OI-18.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
