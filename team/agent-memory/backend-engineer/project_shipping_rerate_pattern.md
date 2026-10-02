---
name: project-shipping-rerate-pattern
description: How buyLabel's rate-TTL re-rate branch (B-25/T-22-3) stays double-buy-safe under concurrency
metadata:
  type: project
---

`buyLabel` in `invai-backend/src/modules/shipping/service.ts` has a `"rerate"` `BuyPlan` branch
(added T-22-3, commit 3bd775d) for an expired quote: it calls `rateOrder` (fresh carrier rate,
no transaction held) then re-enters `buyLabel` with `{ rerated: true }`, buying only if the
carrier+service+cents are identical to the original quote; a moved price or vanished service
throws `RATE_EXPIRED` with the new quotes already stored.

**Why:** AC3 forbids a silent charge at a new price after a quote expires (24h TTL or a carrier
price-change boundary, see `src/integrations/carriers/rate-ttl.ts`).

**How to apply:** the `"rerate"` branch writes nothing to the shipment row (unlike the normal
buy path, which sets `status: "buying"` before the carrier call), so two concurrent expired-quote
buys can both take it. This is still safe: `rateOrder`'s own row lock serializes the
`rateQuotes`/`ratedAt` overwrite, so the loser's stale `rateId` won't be found in the winner's
fresh `rateQuotes` and it fails closed with `rateExpired()` — never a double buy. When reviewing
future changes near this path, check that the `"rerate"` branch still writes nothing to the row
(that's what makes the failure mode "fail closed", not "double buy").
