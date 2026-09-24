# Channel facts for adapters (as of 2026-09-24)

From `invai-docs/research/10-marketplace-engineering-rules.md` §2–8. **[3P]** = third-party source only, **[U]** = unverified. Confirm both against the provider's current docs before you depend on them, and record the doc URL in the adapter.

## Auth and tokens

| Channel | Flow | Access token | Refresh token | Gotcha |
|---|---|---|---|---|
| Etsy v3 | OAuth2 PKCE | 1 h | 90 d, **rotates** | `x-api-key: <keystring>:<shared_secret>` required since 2026-02-09; stale refresh token → `invalid_grant` |
| Amazon SP-API | LWA | 1 h | **expires after 365 d** and when the app adds roles | LWA **client secret must rotate every 180 d** or all calls stop (old secret dies 7 d after a new one); RDTs still needed for v0 PII calls |
| Shopify | auth code with `expiring=1` | 1 h | 90 d, **rotates** | non-expiring tokens banned for new public apps since 2026-04-01, for all public apps from 2027-01-01. `exchangeShopifyCode` doesn't send `expiring=1` today (research 10 §9 item 2) |
| TikTok Shop | auth code | read `*_expire_in` (7 d reported [U]) | 365 d reported [U], rotates | requests HMAC-signed; `x-tts-access-token`; `shop_cipher` on shop calls; success is `code == 0` in the body; version pinned **per endpoint** |
| Walmart | OAuth2 **auth code** (`clientType=seller`) | 15 min | 1 yr | headers `WM_PARTNER.ID`, `WM_MARKET`, `WM_QOS.CORRELATION_ID`; must **acknowledge** POs on intake |

## Webhooks

| Channel | Transport and signature | Dedupe on | Retry window | Payload |
|---|---|---|---|---|
| Etsy | Portal-registered per app (no API). Standard Webhooks HMAC over `webhook-id.webhook-timestamp.body`; `webhook-signature` may hold several `v1,<b64>`; key = base64-decode(secret minus `whsec_`); 5-min tolerance | `webhook-id` | ~30 h (0s, 5s, 5m, 30m, 2h, 5h, 10h, 10h) | ids only: `event_type` (real payloads say `ORDER_PAID`, docs say `order.paid`; match both, case-insensitive), `resource_url`, `shop_id` |
| Amazon | Notifications API via SQS (EventBridge for some types) | `NotificationId` | duplicates expected | ORDER_CHANGE summary: `OrderChangeType` (OrderStatusChange, **BuyerRequestedChange**), `OrderChangeTrigger.TimeOfOrderChange` |
| Shopify | `X-Shopify-Hmac-SHA256`; TOML app-scoped subscriptions preferred; shop-scoped ones **deleted after repeated failures within 24 h** | `X-Shopify-Webhook-Id` | 8 retries in 4 h | full order; order by `X-Shopify-Triggered-At` or `updated_at`. Compliance topics `customers/data_request`, `customers/redact`, `shop/redact` are mandatory for the App Store |
| TikTok Shop [3P] | `Authorization` = hex HMAC-SHA256(secret, app_key + body), no timestamp | `tts_notification_id` | 2m, 30m, 3h, 12h | PII masked while `ON_HOLD`; events incl. `RECIPIENT_ADDRESS_UPDATE`, `UPCOMING_AUTHORIZATION_EXPIRATION` |
| Walmart [U] | Notifications API, BASIC/HMAC/OAUTH destination auth | `eventId` | ~3 retries | `PO_CREATED` etc. |

Response budget: TikTok 3 s [3P], Shopify 5 s, EasyPost 7 s. Verify, persist the id, enqueue, return.

## Rate limits

| Channel | Limit | Signal |
|---|---|---|
| Etsy | per-app QPS and QPD (rolling 24 h) | `x-remaining-*`, `retry-after` |
| Amazon | per seller+app bucket. v2026 `searchOrders` **0.0056 rps (burst 20)**, `getOrder` 0.5/30, v0 `confirmShipment` 2/10 | headers unreliable; drive intake from ORDER_CHANGE, sweep with `searchOrders` slowly |
| Shopify | cost-based: restore 100/200/1000/2000 points/s by plan; max 1000 per query | `extensions.cost.throttleStatus {currentlyAvailable, restoreRate}`; wait `(cost − available) / restoreRate` |
| TikTok | dynamic, no quota API | 429 |
| Walmart | orders GET 5000/min, ack/ship/cancel 60/min, inventory 200/min | `x-current-token-count`, `x-next-replenish-time` (also `...-replenishment-time`), case-insensitive |

## Orders, tracking, cancels

- **Etsy:** poll `getShopReceipts?min_last_modified` + webhook trigger. Tracking `createReceiptShipment` **emails the buyer each call**; `carrier_name` from `getShippingCarriers` or `other`; tracking required for US orders > $10. Never email Etsy buyers ourselves.
- **Amazon:** reads on Orders **v2026** (`getOrder` with `includedData=FULFILLMENT,RECIPIENT,CANCELLATION`; status `CANCELLED` with double L); v0 reads are removed **2027-03-27**, but `confirmShipment` exists only in **v0** (needs numeric `packageReferenceId`, `carrierCode`, per item and quantity). Seller cancel only via `POST_ORDER_ACKNOWLEDGEMENT_DATA` feed.
- **Shopify:** `orders/*` webhooks + `updated_at` reconciliation (60-day window without `read_all_orders`); tracking via `fulfillmentCreate` on fulfillment-order lines; inventory `inventorySetQuantities` needs `changeFromQuantity` and **`@idempotent(key:)`** since API 2026-04 (our pin is 2026-07; `setAvailability` still sends the removed `ignoreCompareQuantity`, B-04). Null PII with HTTP 200 without Level 2 approval.
- **TikTok:** ignore until AWAITING_SHIPMENT; never produce while `ON_HOLD`; cancel requests auto-approve after 24 h; auto-cancel 7 business days after order.
- **Walmart:** PO_CREATED → acknowledge → ship per `lineNumber` with `statusQuantity`; exact carrier names or `otherCarrier` + `trackingURL`; `shipDateTime` epoch ms; push tracking after carrier handoff.
- **All:** cancellation and shipment are per line and quantity (R9); performance clocks run on the first carrier scan or a USPS SCAN form (R11).
