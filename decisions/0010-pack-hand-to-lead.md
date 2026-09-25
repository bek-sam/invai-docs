# 0010: "Pack anyway" becomes "hand to lead"; no partial shipments

- Status: accepted (2026-09-25). This is an addendum to 0002.
- Type: product / architecture
- Card: T-4-1 (wave 4)

## Context
Decision 0002 says "Mark packed" checks that every non-cancelled unit is packed. The old floor "Pack anyway" button only released the tote. The wave 4 plan considered an override that forces `ready_to_ship`. However, the shipping model allows one live label per order, the ship queue drops orders with a live shipment, and a label covers every unit of the order. So a forced-ready order either couldn't be labeled or would ship units that don't exist.

## Decision
- `production.packOrder` with `override: { reason }` needs `production.override` (owner or admin). It records who, why and the missing units in `orders.pack_override`, writes the audit entries `order.pack_override` and `order.handed_to_lead`, and releases the tote.
- It does **not** change the order status. The order ships only when every non-cancelled unit is really packed. The lead resolves the missing units by finding them, reprinting, or cancelling units.
- The floor labels the action "Hand to lead".
- Split or partial shipments are out of scope for the MVP. They would need a shipping-model change: several live shipments per order, and labels scoped to units.

## Consequences
A short order waits, which is safer than shipping an incomplete order. If pilots ask for partial shipments, that's a scope-change request with its own card.
