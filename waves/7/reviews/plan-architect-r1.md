# Wave 7 plan review — architect, round 1

Verdict: **approve with clarifications applied** (see each card and `wave.md`).

## Path overlaps

**Within wave 7:**
- T-7-1 ("export procedure only") and T-7-3 ("the fee lookup only") both edit `modules/shipping/service.ts`, and both are started first per the wave order — real risk of colliding on the same file at once. Left as separate hunks per the cards' own scoping, but added a rule to both cards: commit only your own hunks, and whoever lands second rebases onto the first's commit.
- T-7-2's refund parsing (`integrations/channels/{shopify,csv}/**`) and T-7-1's exports (`integrations/channels/exports/**`) are adjacent but disjoint directories — no file overlap.

**Against wave 6 (in-progress, checked read-only in the actual worktrees):**
- `invai-backend-t63` (T-6-3, uncommitted) is editing `src/modules/finance/router.ts`, `service.ts` and `service.test.ts` — T-7-2 owns `modules/finance/**` in full. This is a live collision waiting to happen, not a hypothetical one. Added a hard gate: T-7-2 does not touch `modules/finance/**` until T-6-3's commit is on `invai-backend`'s `main`.
- `invai-backend-t64` (T-6-4, uncommitted) only touches `src/ai/**` and `modules/ai/**` — no overlap with any wave 7 path.
- T-6-1, T-6-2 and T-6-5 are already merged to `main` (commits `55ea446`, `3b08f5a`, `5339a57`). No live conflict, but T-6-5's merge (`5339a57`, 35 files) already rewrote call sites in `modules/shipping/service.ts`, `modules/shipping/jobs.ts`, `modules/channels/sync.ts` and `modules/billing/service.ts` (adding a required company/scope argument to `carrierAdapter`/`getChannelAdapter`). T-7-3's and T-7-4's cards were drafted against the pre-T-6-5 shape of these files; flagged on both cards to build against current `main`, not the shape implied by the card text or the audit's cited line numbers (which predate this merge and will have drifted).

## Contract stubs (exact)
Written into `wave.md` under "Contract stubs (exact)" (4 stubs) since none exist today for what these cards need:
1. `shipments.exportedAt` (new column) + `shipping.exportTracking` procedure (T-7-1). Deliberately not reusing `trackingPushStatus`/`trackingPushedAt` — B-67 already documents `manual` being conflated with "pushed" in void logic; conflating export-marking with that same field would compound it.
2. `refund_events` (new table, ledger not a field) + `RefundEvent` schema + `finance.refunds.record`/`.list` procedures (T-7-2). This is the substantive finding: `profit_lines` is one row per order item keyed by `(companyId, orderItemId)` with a single `placedAt`. AC2 ("refunds reduce profit on their date") cannot be satisfied by writing into that row — a refund weeks after the order needs its own dated record, and `finance.profit`'s period grouping needs to read refunds from `refundedAt`, not `placedAt`. This is a data-model gap, not a missing endpoint; sized accordingly rather than as an "add a field" change.
3. `NormalizedOrder.sourceUpdatedAt` (T-7-4's staleness AC3). No channel-side timestamp exists anywhere in the pipeline today to compare against.
4. `ITEM_FLAG_CODES` gains `channel_edit_after_press` (T-7-4 AC5). Existing `ORDER_ITEM_STATES` already has everything needed to detect "already pressed" (`pressed`/`packed`/`shipped`/`delivered`); only the flag code was missing.

All four are additive (new table/column/procedure/enum value) — no `contract-deprecation` process triggered.

## Grants needed (owned paths don't cover the stubs above)
- T-7-1 → `db/schema/shipping.ts` (the one column) and the `exportTracking` procedure in `invai-contracts`.
- T-7-2 → `db/schema/finance.ts` (the one table) and `RefundEvent`/`finance.refunds.*` in `invai-contracts`.
- T-7-4 → `invai-contracts` for `sourceUpdatedAt` and the new flag code.
- Cross-card: populating `sourceUpdatedAt` per adapter lands in `integrations/channels/**`, which is T-7-1's territory this wave, not T-7-4's (which only owns `modules/orders/**` plus the `sync.ts` hunk). T-7-4 should land the contract field and the orders-side check; T-7-1 populates it while it's already touching each adapter for exports.

## Other hidden dependencies
- `orders/import.ts`'s `updateExisting` doesn't currently receive `timeZone`/`processingDays` (only `createOrder` does), so today's bug — comparing the raw channel `shipBy` against the already-computed `o.shipBy` — can't be fixed by changing the comparison alone; it needs those two threaded through to recompute ship-by the same way `createOrder` does. Flagged on T-7-4 so it isn't estimated as a one-liner.
- `finance/service.ts` already reads a persisted `labelFeeCents` off the label/shipment row for the profit calc (`:415`, `:581`), separate from the `LABEL_FEE_CENTS` constant T-7-3 removes — confirms T-7-3's AC3 ("billing usage, the shipping label record and profit all use the same fee") is already half-true structurally; T-7-3 just needs to make sure the value written at buy time comes from `PLAN_CATALOG.labelFeeCents` instead of the constant, which the card's AC1 already covers.

## Cards edited
`T-7-1`, `T-7-2`, `T-7-3`, `T-7-4` — clarifications and owned-path grants added. `T-7-5`: no backend/contract surface, no path overlap with any other card this wave or wave 6; unchanged.
