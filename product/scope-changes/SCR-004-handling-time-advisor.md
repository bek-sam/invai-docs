# SCR-004: Handling-time and processing-time advisor from real floor data
Filed by: product-manager  Date: 2026-09-28  Type: add
Scope section affected: scope.md#mvp-in item 1 (Order Hub, ship-by, at-risk alerts); new capability

## Request
From item scan timestamps, compute the 90th-percentile time from import to ship per design × blank × channel over the last 28 days, add the shop's buffer, and recommend a handling time (Amazon, per SKU) and a processing time (Etsy, per variation or profile). Export the values as CSV in each channel's template. Show a "peak mode" suggestion when the backlog grows. It suggests only and never writes to a listing, consistent with the "no automatic listing changes" fence.

## Why (evidence)
- Amazon moved every seller-fulfilled SKU to Automated Handling Time or accurate manual per-SKU values on 2026-06-29; Automated Handling Time gives 180 days of late-shipment protection; custom SKUs are exempt ([3P] novadata and ecomcrew, cited in `research/16` §1.1 and §3 #1).
- Etsy moved processing time to the variation level, and slow shipping lengthens the delivery estimate buyers see (research 16 §1.1).
- `research/03` pain #1 (late-shipment penalties; frequency 5, severity 5) and pain #11 (peak season).
- Shops confirmed: 0 pilots. The Amazon rule applies to every Amazon seller-fulfilled shop.

## Who it helps
Mid and large shops on Amazon or Etsy (office and owner roles).

## Cost and risk
- Effort: M, about 2–3 cards (production and orders stats, a contract procedure, web screen and export).
- No spend. Direct writes to channels are out (they would need SP-API and Etsy approval).
- Risk: small samples give noisy numbers. Show a minimum sample and confidence (30 units) before suggesting.

## If we don't
Shops keep guessing handling times: too short means late shipments, too long means lost sales and search rank.

## Decision
Sent to owner (OI-17). The PM recommends **accept**.
Reason: directly protects the top pain, uses data only InvAI has (scan times), no spend.  Decided by: —  Date: —
