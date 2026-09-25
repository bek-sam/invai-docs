# T-5-1: Order detail actions, shipment section, address fix

| Field | Value |
|---|---|
| Scope ref | `product/scope.md#mvp-in` items 1 and 7 |
| Backlog | B-84 |
| Owner | web-engineer; backend-engineer (orders) for `orders.updateAddress` |
| Reviewer | reviewer; co-reviewers product-designer, architect |
| Risk flags | ui |

## Owned paths
- invai-web `features/orders/**`, `routes/_app/orders/**`, own i18n keys
- invai-backend `modules/orders/**` (`updateAddress` only)
- tests

## Evidence
`build/audit-2026-09-24.md` §A-FE B-84 (`order-detail.tsx:246-320`, `orders/index.tsx:180-193`).

**Clarified in plan review (architect r1):** B-62 ("cancel after label," originally cited as open in `orders/service.ts:790-861`) is resolved — wave 2's T-2-5 landed crash-safe voids and `guardShipmentsForItems` (`shipping/service.ts:1312-1368`) refuses cancel/hold once tracking is pushed. The only remaining gap here is the **web void confirmation dialog** (no confirm exists today in `shipping.tsx`'s void button), which is T-5-2's scope, not this card's. `orders.updateAddress`'s exact shape, gating and validation approach are now specified in `wave.md` under "Contract stubs (exact)" §1 — use that, not the one-line summary in "Agreed interfaces."

## Acceptance criteria
1. **Unit actions** on order detail:
   - rush toggle (`setRush`);
   - set or clear a flag (`setFlag`);
   - artwork override for non-personalized `needs_artwork` units (`setArtwork`, with a design picker);
   - order tags (`setTags`).
   Flag messages are translated from codes.
2. **Shipment section:** carrier, service, tracking number with a link, label PDF link, status timeline and cost. Void is there too, with a confirmation dialog; it uses the existing `voidShipment` and respects the T-2-5 rules.
3. **Address holds:** an order held for `address_check` (or any pre-ship order with no live label) shows an "Edit address" form. Saving calls `orders.updateAddress`, runs the format-only check (street1 non-empty, valid zip — there is no carrier-verified check available before the order is packed, don't imply one in the copy), and releases the hold when it passes. Show `ADDRESS_LOCKED` clearly if a label already exists ("void the label first").
4. **Order list:**
   - tab counts are correct (needs mapping, needs artwork, ready);
   - new views: In production, Shipped, Cancelled, Due today, Overdue;
   - filters for date range, tag and channel;
   - bulk cancel with confirmation;
   - CSV export of the current view.
5. **Quality:** en and es, 390 px, keyboard accessible; loading, empty and error states.

## Verification
- Typecheck, lint, test and build in web and backend.
- Browser on a DB copy: each action, an address fix releasing a hold, void with confirm, bulk cancel, export. Screenshots in en and es.
