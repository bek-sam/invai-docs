---
name: amazon-report-columns
description: Which Amazon order flat files carry prices/shipping credit; the Unshipped report has none (B-183, T-22-3, 2026-09-29)
metadata:
  type: reference
---

Checked 2026-09-29 at https://developer-docs.amazon/sp-api/docs/report-type-values-order (page updated 2026-09-09):
- Unshipped Orders (GET_FLAT_FILE_ACTIONABLE_ORDER_DATA_SHIPPING, 27 cols): NO item-price, shipping-price, tax or promotion columns. Imports get 0 amounts.
- Order Report (GET_FLAT_FILE_ORDER_REPORT_DATA_SHIPPING, 36 cols): item-price, item-tax, shipping-price, shipping-tax, latest-ship-date; no promotion discounts.
- All Orders (GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL): has ship-promotion-discount but uses `amazon-order-id`/`quantity` and has no ship-to; our CSV parser rejects it.

**Why:** the older fixture `amazon-unshipped-orders.txt` had price columns the real report lacks, which hid B-183. Seed also hardcodes Amazon shipping 0 (db/seed/builder.ts).
**How to apply:** build fixtures from the official column list, not memory. Re-importing an Unshipped file after an Order Report zeroes totals in orders/import.ts updateExisting (reported to backend-engineer, T-22-3).
