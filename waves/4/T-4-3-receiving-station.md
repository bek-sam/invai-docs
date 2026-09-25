# T-4-3: Receiving station on the floor

| Field | Value |
|---|---|
| Scope ref | `product/scope.md#mvp-in` items 5, 6 and 9 |
| Backlog | B-96 |
| Owner | floor-engineer |
| Reviewer | reviewer; co-reviewers product-designer, backend-engineer (inventory) |
| Risk flags | ui, floor-correctness |
| Model | opus |

## Owned paths
- New `invai-floor/src/stations/receiving/**`, plus a named grant for exactly two lines in `invai-floor/src/screens/StationShell.tsx` (one import, one `active === "receiving"` render case — that file isn't in any card's owned paths otherwise)
- Your own i18n keys (hand edit, commit only your hunks)
- tests

## Depends on
- The architect's stubs: `STATIONS` gains `receiving`, and `receiver` gains a new `production.receive` permission. T-4-1 implements the backend side, including changing `sheets.markReceived`'s required permission from `production.build` to `production.receive` (and granting `production.receive` to `office` too, so it keeps access). The existing `purchaseOrders.receive` (`purchasing.receive`) and `inventory.count` (`inventory.count`) procedures already allow floor sessions and `receiver` already has both permissions — verified in `roles.ts`. `sheets.markReceived` did **not** already allow `receiver` before this wave (it required `production.build`, which `receiver` never had) — that's the actual gap T-4-1 closes, not just an `auth` mode check.

## Acceptance criteria
1. **PO receiving:**
   - Pick an open PO, or scan its PO number.
   - Scan or tap blanks (`B:<variantId>` labels) or enter quantities per line.
   - Submit with an `idempotencyKey` (wave 1), so a double submit counts once.
   - Partial receipts are allowed.
   - Over-receipt warns.
2. **Vendor transfers:** scan a sheet QR or pick from a list of sent or shipped sheets, then mark it received.
3. **Stock count:** count a bin or location. The difference is shown before submitting, and it's recorded through `inventory.count`.
4. **Offline:** works with the offline queue (T-4-2 interface: enqueue commands like the other stations).
5. **Quality:** en and es, tablet layout, large touch targets, the same station-header patterns.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build` in floor.
- In the browser against your API on a DB copy, signed in as `receiver@desertbloom.test` (PIN from the seed): receive a PO partially, then fully; receive a vendor sheet; do a count. Screenshots in en and es.
