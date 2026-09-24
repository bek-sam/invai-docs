# T-2-5: Crash-safe labels, tracking push outside transactions, cancel voids labels

| Field | Value |
|---|---|
| Wave | 2 |
| Scope ref | `product/scope.md#mvp-in` items 1 and 7; always-in-scope: bug (money) |
| Backlog | B-11 (without EasyPost webhooks, which move to wave 3), B-44, B-62, B-67 (backend) |
| Owner | backend-engineer (shipping), with `modules/orders/service.ts` cancel/hold code and `integrations/carriers/**` granted |
| Reviewer | reviewer |
| Co-reviewers | security-reviewer, qa-engineer (golden path) |
| Risk flags | payments, marketplace-policy, migration |
| Model | opus |

## Owned paths (edit)
- `invai-backend/src/modules/shipping/**`
- `invai-backend/src/integrations/carriers/**`
- `invai-backend/src/modules/orders/service.ts` (cancel and hold functions only)
- `invai-backend/src/modules/channels/service.ts`: only `pushTrackingForShipment`. T-2-1 edits `connect` in the same file; commit with a pathspec after checking `git diff` holds only your hunk.
- `invai-backend/src/db/schema/shipping.ts` and its migration
- tests next to these files

## Evidence
`build/audit-2026-09-24.md` §A-BE B-62, B-67; backlog B-11, B-44.

## Acceptance criteria
1. **`buyLabel` is crash-safe:**
   - Record the intent (`buying`, with an idempotency key) and commit.
   - Buy outside any transaction, with the carrier idempotency key or reference.
   - Record the result.
   - A retry reads back from the carrier before buying again.
   - A test simulates a commit failure after the carrier charged, and the retry doesn't charge twice.
2. **No carrier call while holding a row lock:** `rateOrder` doesn't call the carrier under `FOR UPDATE`.
3. **`pushTracking` runs outside the DB transaction:**
   - It's idempotent per shipment (one push per shipment and tracking number).
   - A retry never re-notifies the buyer.
   - It checks the items' state and holds at push time: cancelled or held items are never pushed.
4. **Cancel or hold after a label:**
   - Cancelling a unit or an order that has a bought, not-yet-shipped label voids the label (refund) and blocks its tracking push. A hold blocks the push until it's released.
   - If the tracking was already pushed, cancel is refused with a clear message.
5. **Voids for CSV-only channels:**
   - Etsy, Amazon, TikTok and Walmart (while they're CSV-only) no longer count as "pushed" at once. Their items become shipped on the scan or the manifest, not on a fake push.
   - `voidShipment` works for them until the item is shipped.
6. **Tests:** the new tests cover `buyLabel`, `rateOrder`, `voidShipment` and `pushTracking` (part of B-71).

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build` in invai-backend, with your own test DB.
- For real on a DB copy with the mock carrier:
  - buy, then kill the process mid-way (or inject a failure), retry, and show one label;
  - cancel a labeled order and show the void and no push;
  - void a label on an Etsy CSV order.
- `E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts` against your API on a fresh copy seed.

## Out of scope
- EasyPost tracker webhooks (wave 3). The tracking export file (B-68).

## Note from plan review (architect, r1)
This card is large for one agent: it spans two state machines (shipment and order item) plus a
migration and a channel-behavior change. It stays as one card for this wave (splitting it would
push the wave past the 5-card cap), but land it as two internally sequenced commits against the
same card — (a) `buyLabel`/`rateOrder` crash-safety and idempotent `pushTracking`, (b) cancel/hold
voids a label and the CSV ship-on-scan change — so a stuck second half doesn't block the first.
`reviewer` and the `qa-engineer` co-reviewer should check each half on its own evidence. If this
slips past two review rounds, split it into two cards for the next wave instead of a third round.
