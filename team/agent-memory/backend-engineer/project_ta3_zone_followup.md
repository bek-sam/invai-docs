---
name: ta3-zone-followup
description: shippingMargin zone grouping now reads shipments.dest_zone (T-A3 review note 2 follow-up)
metadata:
  type: project
---

`analytics/finance-service.ts` `shippingMargin({groupBy: "zone"})` groups labeled shipments by
`shipments.dest_zone` (rows `"1"`..`"9"`, numeric sort); a shipment with a null zone is counted in
`shipmentsWithoutZone`, never turned into a row — matches the contract comment on
`ShippingMargin.shipmentsWithoutZone`. Commit `8c616ef`.

**Why:** T-A3's original build predated T-A4's `shipments.dest_zone` column, so it correctly left
zone rows empty rather than fabricate them (reviewer note 2, non-blocking). Once `dest_zone` landed
this was a same-day follow-up, not a new decision.

**How to apply:** `dest_zone` is nullable smallint, set once at label purchase (`shipping/zone.ts`,
T-A4). Any other finance/analytics grouping that reads `shipments.*` should check whether `dest_zone`
is populated for the rows it touches before assuming zone data exists.
