# Provider deadlines

Seeded from `invai-docs/research/10-marketplace-engineering-rules.md` (checked 2026-09-24). Tags: **[3P]** third-party source only, **[U]** unverified. "Past" rows stay while our code still violates them.

| Date | Provider | Change | Our impact | Status / card |
|---|---|---|---|---|
| 2025-09-27 | EasyPost | Zero parcel dimensions rejected | Parcel fallbacks and saved presets must never be 0 (`modules/shipping/service.ts` fallbacks) | Check (B-25) |
| 2025-11-01 | TikTok Shop | Sales tax charged on referral fees | Profit fee model | B-13 |
| 2025-11-23 | EasyPost | Index endpoints limited to 5 rps | Rate limiter for list calls | Watch |
| 2025-11-25 | Amazon | Data Protection Policy update (PII ≤ 30 d after delivery, non-PII ≤ 18 mo, logs ≥ 12 mo, KMS, MFA, 7/30-day patch SLAs) | Security controls before the SP-API application | B-23, B-29 |
| 2025-12-22 | UPS | 5.9% general rate increase | Use bought label cost | Done by design |
| 2026-01-26 | UPS | Additional Handling above 10,368 in³ [3P] | Package presets | Watch |
| 2026-02-09 | Etsy | `x-api-key` must be `keystring:shared_secret` | Etsy adapter (not built yet) | Build with it |
| 2026-02-17 | Etsy | Webhooks for personal apps and `order.canceled` | Etsy intake design | Build with it |
| 2026-02-27 | Shopify | Partner Program Agreement bans training on merchant data without consent [3P] | No training on marketplace data (R15) | Policy |
| 2026-02-28 | Amazon | OTDR < 90% deactivates listings [3P]; EasyPost labels not OTDR-protected | Amazon Buy Shipping adapter | Backlog idea |
| 2026-03-04 | Amazon | Business Solutions Agreement agent-policy rules [U] | Keep human approval on AI publishes | Verify |
| 2026-04-01 | Shopify | Non-expiring offline tokens banned for new public apps | `exchangeShopifyCode` lacks `expiring=1`; no refresh | **P0**, B-05 |
| 2026-04 (API 2026-04) | Shopify | `inventorySetQuantities` drops `compareQuantity`/`ignoreCompareQuantity`; `@idempotent` mandatory on inventory and refund mutations | `setAvailability` in `shopify/live.ts` fails on our pinned 2026-07 | **P0**, B-04 |
| 2026-04-14 | Walmart | Refund Rate replaced by Item Not Received ≤ 2%, Return Rate ≤ 6% [3P] | Metrics display | Watch |
| 2026-05-13 | Shopify | Shopify Tax threshold counts lifetime sales for new stores | Shopify tax model | B-13 |
| 2026-06-29 | S&S / SanMar | Bella+Canvas moved to SanMar; S&S sells it only until stock runs out | Several suppliers per blank SKU; SanMar adapter is a stub | B-36 |
| 2026-07-12 | USPS | L×W×H required on commercial manifests; DIM divisor 166 → 139; $50 mislabel fee | Parcel dims always sent, never 0 | Check (B-25) |
| 2026-07-22 | Amazon | Photoreal AI people need XMP `contains-synthetic-performer` [3P] | Imaging must tag if AI models/people are ever added | Watch |
| 2026-08-04 | TikTok Shop | Referral fee 8% (was 6%) [3P] | `CHANNEL_RULES` fee note; mark "verify" in UI | B-13 |
| 2026-08-29 | EasyPost | New `shipment.invoice.updated` event (billing adjustments) | Consume with EasyPost webhooks | B-11 |
| 2026-09-27 → 2027-01-16 | UPS | Peak surcharge $0.50 residential/Ground Saver, $0.75 Nov 22 – Dec 26 | Profit uses bought label cost | Done by design |
| 2026-10-04 → 2027-01-17 | USPS | Ground Advantage peak surcharge $0.40–$0.55 (0–3 lb) | Same; rate TTL must not cross a price-change midnight (Central) | B-25 |
| 2027-01-01 | Shopify | Non-expiring tokens stop working for **all** public apps | Every Shopify connection breaks without refresh | **P0**, B-05 |
| 2027-03-27 | Amazon | Orders API v0 reads removed (`getOrders`, `getOrder`, `getOrderItems`, `getOrderAddress`, buyer info) | Plan v2026 reads; keep v0 `confirmShipment`; fix `channels/amazon/index.ts` comments | Build with it |
| Every 180 d | Amazon | LWA client secret rotation (notice 90 d ahead; old secret dies 7 d after a new one) or all calls stop | Credential calendar | B-05 |
| Every 365 d | Amazon | Refresh token re-authorization (also when app roles change) | Health alert at 30/7/1 d | B-05 |
| 1 yr | Walmart | Refresh token lifetime | Health alert | B-05 |
| 90 d rotating | Etsy, Shopify | Refresh token lifetime; rotates on each refresh | Persist new refresh token atomically | B-05 |
| Ongoing | Walmart | Item spec 4.x sunset; 5.x (5.0.20260114) required | Listing push (not built) | Build with it |
| Ongoing | Shopify | Pinned `SHOPIFY_API_VERSION = "2026-07"`; each version has a limited support window | Check the Shopify API release calendar for the 2026-07 end-of-support date and plan the bump | Verify date |

Last checked: 2026-09-24 (from research 10; provider sites not re-fetched for this table).
