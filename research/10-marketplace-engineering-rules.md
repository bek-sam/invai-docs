# Marketplace engineering rules (integrations and backend rulebook)

As of Sep 24, 2026. Every source below was checked on **2026-09-24** unless the entry gives another date.

This complements `04-apis-and-ai-feasibility.md`, `01-shop-workflow.md` and `03-pain-points.md`; it does not repeat them.

- **What this document adds:** new facts, corrections to those docs, and concrete rules. It ends with §9, where our v1 code is checked against the rules.
- **How facts are tagged:**
  - Untagged facts come from official docs, or from official pages via Wayback snapshots where etsy.com and help.etsy.com return 403.
  - **[3P]** means the fact comes from a third-party source only.
  - **[U]** means it is unverified. Confirm it before depending on it.
- **How rules are worded:** **MUST** means breaking the rule causes an outage, a rejection or a policy violation. **SHOULD** means strongly recommended.

---

## 1. Rules for every channel

These apply to Etsy, Amazon, Shopify, TikTok and Walmart, and to EasyPost.

**Tokens and credentials**
- **R1. MUST: tokens rotate, so treat every token as expiring.** On every refresh, store the new access token **and the new refresh token**, atomically, in the same transaction as the expiry time. Refresh under a per-connection lock (Redis `SET NX` or a row lock). That stops two workers from refreshing at once, which invalidates one of the refresh tokens.
  - Etsy, Shopify (expiring offline tokens) and TikTok rotate refresh tokens.
  - Amazon refresh tokens expire after 365 days.
  - Walmart refresh tokens last 1 year.
- **R2. MUST: expose credential expiry as connection health.** Track each connection's refresh-token expiry and alert the shop 30 days, 7 days and 1 day before it (Amazon, Walmart, TikTok, Shopify, Etsy). An expired refresh token needs the seller to re-authorize, which is not something an engineer can fix.

**Webhooks**
- **R3. MUST: verify every webhook against the raw request bytes** before parsing JSON. Compare in constant time, then enqueue and return 2xx fast. Response budgets:
  - TikTok: 3 s [3P]
  - Shopify: 5 s
  - EasyPost: 7 s
- **R4. MUST: dedupe on the channel's delivery or event id, persisted for longer than the channel's retry window.**
  - Retry windows: Etsy about 30 h, EasyPost 6 retries, Shopify 4 h, TikTok about 15 h [3P].
  - A BullMQ `jobId` that gets removed after 24 h is not enough for Etsy. Use a `webhook_deliveries(channel, delivery_id)` table with a unique key and a 7-day TTL.
- **R5. MUST: webhooks can arrive out of order and are not guaranteed.**
  - Never let an older payload overwrite newer state. Compare the channel's `updated_at` (Shopify `X-Shopify-Triggered-At` or `updated_at`, Amazon `OrderChangeTrigger.TimeOfOrderChange`) with the last value stored on the order.
  - Always run a reconciliation poll as the source of truth.
  - Where the webhook carries only ids (Etsy, and Amazon's Summary), refetch the order.
- **R6. SHOULD: treat a webhook as a trigger to fetch, not as data.** Etsy payloads carry only `resource_url`. Amazon ORDER_CHANGE sends a summary. TikTok masks PII while an order is ON_HOLD.

**Rate limits and retries**
- **R7. MUST: rate-limit per (channel, seller connection), shared across processes.** Reuse the Redis token bucket in `integrations/suppliers/ratelimit.ts`.
  - On 429, back off exponentially with jitter, or wait until the channel's replenish hint (Shopify `restoreRate`, Walmart `x-next-replenish-time`, Etsy `retry-after`).
  - Never retry in a tight fixed loop.
- **R8. MUST: POST calls that cost money or send emails are not safely retryable.** Examples: label buy, `createReceiptShipment` (it emails the buyer each time), `fulfillmentCreate` with notify, and S&S `POST /orders`.
  - Record intent in the DB first and commit.
  - Call the API **outside** the DB transaction.
  - On a timeout, **read back** before retrying: GET the shipment, list the receipt's shipments, or list the fulfillments.

**Orders and state**
- **R9. MUST: model cancellation and shipment per line and per quantity, not per order.**
  - Amazon `confirmShipment`, Walmart ship-lines, Shopify fulfillment-order lines and TikTok packages are all per line and quantity.
  - Amazon, Walmart and TikTok cancel per line.
  - Shopify order edits remove lines or reduce quantities.
- **R10. MUST: a buyer cancel request blocks production.**
  - Amazon `BuyerRequestedChange`, TikTok cancellation requests (the seller has 24 h to respond or it is auto-approved) and Walmart intent-to-cancel must put the order on hold before it goes on a gang sheet.
  - The UI must force a decision.
- **R11. MUST: marketplace performance clocks run on the carrier's first scan or a manifest, not label creation.**
  - Walmart VTR needs a carrier scan. TikTok counts a carrier acceptance scan or a USPS manifest.
  - Create USPS SCAN forms (EasyPost `scan_form`) for each day's labels. This makes dispatch count at manifest time.
- **R12. MUST: push tracking with carrier codes from the channel's own list.**
  - The lists: Etsy `getShippingCarriers`, Amazon carrierCode, Walmart supported carrier names (exact match), Shopify tracking company names, and TikTok's shipping provider list.
  - Use the "Other" carrier only with a name and a tracking URL.
- **R13. MUST: ship-by is per line and comes from the channel when the channel provides it.**
  - Etsy: `transactions[].expected_ship_date`.
  - Amazon v2026: `fulfillment.shipByWindow.latestDateTime`.
  - Walmart: `estimatedShipDate`.
  - Compute locally only when the channel sends nothing, and then respect the shop's time zone and **postal holidays**. Etsy rolls Sundays and postal holidays to the next business day.

**Data and security**
- **R14. MUST: PII minimization and retention by the strictest rule.**
  - Amazon DPP: delete PII within 30 days after delivery. Keep non-PII for at most 18 months. Keep logs at least 12 months.
  - Etsy: listing data at most 6 h stale, other data at most 24 h stale, nothing kept "longer than reasonably necessary".
  - Shopify: honor `customers/redact` and `shop/redact` within 30 days.
  - Report breaches within 24 h to Amazon (`security-incident@amazon.com`) and Etsy (`dpo@etsy.com` plus the seller).
- **R15. MUST NOT: use Etsy, Shopify or Amazon data to train or fine-tune models.**
  - Etsy API Terms prohibit it without written authorization.
  - Shopify's Partner Program Agreement (from 2026-02-27 [3P]) prohibits it without written consent.
  - Sending data to Claude for inference on the shop's own task is fine. Our zero-retention inference must stay configured.

**Money**
- **R16. MUST: reconcile profit with actual fees, not only modeled ones.** Estimated fees are fine until the channel's payout or ledger data arrives. After that, show actuals and flag the variance. Endpoints:
  - Etsy: `getShopPaymentByReceiptId`, ledger entries
  - Amazon: Finances API
  - Shopify: order transactions and payouts
  - Walmart: recon reports
  - TikTok: finance statements

---

## 2. Per-channel quick reference

| | Etsy v3 | Amazon SP-API | Shopify Admin GraphQL | TikTok Shop | Walmart Marketplace |
|---|---|---|---|---|---|
| **Auth** | OAuth2 PKCE; access token 1 h, refresh token 90 d, rotates. `x-api-key: keystring:shared_secret` (required since 2026-02-09) | LWA access token 1 h. Refresh token **expires after 365 d**, and when roles change. **Client secret rotation every 180 d**, or all calls stop | Auth code with `expiring=1`: access token 1 h, refresh token 90 d, rotates. Non-expiring tokens are banned for new public apps since 2026-04-01 and for all public apps from 2027-01-01 | Auth code; access and refresh tokens (read `*_expire_in`; 7 d / 365 d reported [U]). HMAC-signed requests, `x-tts-access-token` header, `shop_cipher` | OAuth2 auth code (delegated keys no longer offered to new solution providers). Access token 15 min, refresh token 1 yr |
| **App approval** | Personal app, then Commercial Access (manual, weeks) | Public developer, plus PII architecture review | App Store review; protected customer data L2 per field | Partner Center; custom apps reviewed at ≥25 shops, 5–7 business days [U] | App Store registration, review and demo: **3–5 weeks** |
| **Webhooks** | Registered per app in the portal only. Payload has ids only. Standard Webhooks HMAC over `id.timestamp.body`, multi-signature header. Retries 0s, 5s, 5m, 30m, 2h, 5h, 10h, 10h | Notifications API via SQS (EventBridge for some types). ORDER_CHANGE; dedupe on `NotificationId`; duplicates expected | 8 retries in 4 h. Shop-scoped (API-created) subscriptions **deleted after repeated failures**; TOML app-scoped subscriptions preferred. Dedupe on `X-Shopify-Webhook-Id` | `Authorization` = hex HMAC-SHA256(secret, app_key + body), no timestamp; retries at 2 m, 30 m, 3 h, 12 h; dedupe `tts_notification_id` [3P] | Notifications API: PO_CREATED etc.; BASIC, HMAC or OAUTH destination auth; dedupe `eventId`; only about 3 retries [U] |
| **Rate limits** | Per app QPS and QPD (rolling 24 h); headers `x-remaining-*` | Token bucket per seller+app. v2026 `searchOrders` **0.0056 rps, burst 20**; `getOrder` 0.5/30; v0 `confirmShipment` 2/10. Header unreliable | Cost-based leaky bucket: restore 100 (Standard), 200 (Advanced), 1000 (Plus), 2000 (Enterprise) points/s; max 1000 per query; 250 items per input array | Dynamic per app × shops, no quota API; handle 429 | Token bucket per seller: orders GET 5000/min, ack/ship/cancel 60/min, inventory 200/min; `x-current-token-count`, `x-next-replenish-time` |
| **Order intake** | Poll `getShopReceipts?min_last_modified` + webhook trigger | ORDER_CHANGE, then `getOrder(includedData=…)`; low-frequency `searchOrders` sweep | `orders/*` webhooks + `updated_at` reconciliation (60-day window without `read_all_orders`) | Webhook, then order detail; ignore until AWAITING_SHIPMENT | PO_CREATED, then **acknowledge**, then ship |
| **Ship-by** | `transactions[].expected_ship_date` | `fulfillment.shipByWindow.latestDateTime` | none (shop rule) | Handling 1–2 business days; must reach In Transit within 2 business days | `estimatedShipDate` |
| **Tracking push** | `createReceiptShipment` (emails buyer on each call; tracking required for US orders > $10) | **v0 `confirmShipment`** (per item and quantity; `packageReferenceId` numeric) | `fulfillmentCreate` on fulfillment-order lines | Ship package API | `POST /v3/orders/{po}/shipping` per line; `processMode: PARTIAL_UPDATE` to fix |
| **Cancel** | Receipt `status=canceled`, `refunds[]` | Buyer request in `orderItems.cancellation`; seller cancel only through the **order acknowledgement feed** | `orders/cancelled`, order edits, refunds | Buyer request: respond within 24 h, else auto-approved; auto-cancel 7 business days after order | Line-level; `intentToCancelOverride` |
| **Performance** | Star Seller 95% on time with tracking; ship-by can be extended once, before it passes, by up to 21 d | LSR < 4%, VTR ≥ 95%, OTDR ≥ 90% (below it, the top-contributing listings are deactivated since 2026-02-28 [3P]) | none | LDR enforced > 10%, VTR ≥ 95%, auto-cancel if not Awaiting Collection within 5 business days | VTR ≥ 99%, OTD ≥ **90%**, cancellation < 2%; from 2026-04-14 Item Not Received ≤ 2%, Return Rate ≤ 6% [3P] |
| **Tax** | Marketplace facilitator | Marketplace facilitator | **Seller remits** | Marketplace facilitator (and sales tax on referral fees since 2025-11-01) | Marketplace facilitator |
| **Apparel fees** | 6.5% transaction (item + shipping + gift wrap + paid personalization, not US tax) + 3% + $0.25 processing on total **including tax** + $0.20 listing; Offsite Ads 15%/12%, cap $100 | Referral **5% ≤ $15, 10% $15–20, 17% > $20**, min $0.30, on item + shipping + gift wrap; refund admin fee min($5, 20% of referral) [3P]; $39.99/mo | Payments 2.9% + 30¢ (Basic [3P]); +1.25% when using a third-party gateway too; Shopify Tax 0.35% after threshold, cap $0.99 per order | Referral **8% since 2026-08-04** (was 6%) [3P, several sources agree; not found on the official page]; tax on fees | Referral **5% ≤ $15, 10% $15–20, 15% > $20** on total incl. shipping; no monthly fee |

---

## 3. Etsy Open API v3: new rules and corrections

**Auth and webhooks**
- **MUST: send `x-api-key: <keystring>:<shared_secret>`.** Keystring alone has been rejected since 2026-02-09. https://developers.etsy.com/documentation/essentials/authentication , https://github.com/etsy/open-api/discussions/1529
- **MUST: persist the new refresh token returned on every refresh.** Stale refresh tokens fail with `invalid_grant` [3P]. https://github.com/etsy/open-api/discussions/1351
- **Webhooks are configured once, per app, in the Developer Portal. There is no API.** They were available to Commercial apps from 2025-12-11; `order.canceled` and personal apps came 2026-02-17. https://developers.etsy.com/documentation/essentials/webhooks , https://github.com/etsy/open-api/discussions/1509
- **Payloads carry ids only:**
  - Shape: `{"event_type":"ORDER_PAID","resource_url":".../shops/{id}/receipts/{receipt_id}","shop_id":…}`.
  - Real payloads use **uppercase `ORDER_PAID`**, while the docs say `order.paid`. Match case-insensitively on both forms.
  - Route by `shop_id`, then GET `resource_url`. (discussion 1509)
- **Signature:**
  - `webhook-signature` may hold **several space-separated `v1,<b64>` entries**, and any match is valid.
  - The key is base64-decode(secret without the `whsec_` prefix). The signed string is `webhook-id.webhook-timestamp.rawBody`.
  - Reject timestamps more than 5 min off.
  - **Dedupe on the `webhook-id` header.**

**API Terms** (updated 2025-06-16; read from the Aug 2026 Wayback snapshot of https://www.etsy.com/legal/api)
- **Required notice, exact wording:** "The term 'Etsy' is a trademark of Etsy, Inc. This Application uses Etsy's API, but is not endorsed or certified by Etsy."
- **Freshness:** listing content must be at most 6 h stale; other content at most 24 h.
- **MUST NOT:**
  - Collect data for analytics, ML or AI training.
  - **Send Etsy buyers order, shipping or tracking information by email or text.** Our shipping module and mailer must never email Etsy buyers.
  - Help create listings that violate the Creativity Standards.
  - Connect Etsy data to ad platforms.
  - Request more than the minimum data needed.
  - Use multiple keys to evade rate limits.
- **Breach reporting:** within 24 h to `dpo@etsy.com` and to the seller.

**Receipts** (OAS spec https://www.etsy.com/openapi/generated/oas/3.0.0.json)
- **Filters:** `min_last_modified`, `was_paid`, `was_shipped`, `was_canceled`, `was_delivered`, and `sort_on=updated`.
- **`status`:** paid, completed, open, payment processing or canceled.
- **Refunds and fees:**
  - Partial refunds appear in `refunds[]`.
  - Fee adjustments appear in `getShopPaymentByReceiptId → payment_adjustments[]`, in integer pennies.
- **Contact fields can be null:**
  - `buyer_email` is null unless access is granted case by case.
  - Address fields can be restricted by region or partner status.
  - **MUST: handle null buyer contact.**
- **Ship-by is per transaction:** `transactions[].expected_ship_date`, epoch seconds.
- **Gift fields:** `is_gift`, `gift_message` and `gift_wrap_price`. Print the gift message on the packing slip and never put the price on it.
- **`createReceiptShipment`:**
  - Each call adds a shipment **and emails the buyer**. Split shipments work, but each one sends an email.
  - `carrier_name` must be a value from `getShippingCarriers`, or `other`.
  - **Tracking is required for US orders over $10.**

**Fees** (policy updated 2026-02-13, https://www.etsy.com/legal/fees ; processing https://help.etsy.com/hc/en-us/articles/115015628847)
- **Transaction fee:** 6.5% of item + shipping + gift wrap + **paid personalization**. US sales tax is excluded.
- **Payment processing (US):** 3% + $0.25 on the total **including tax**, credited proportionally on refunds.
- **Other fees:**
  - Offsite Ads: 15%, or 12% at $10k+ in sales over 365 days; capped at $100 per order; never charged on US tax.
  - Currency conversion: 2.5%.
  - Etsy Plus: $10/month.
- **Marketplace facilitator:** Etsy collects and remits state sales tax. https://www.etsy.com/seller-handbook/article/321914904041

**Listings**
- **AI disclosure:**
  - Creativity Standards: "Sellers must disclose **within their listing description** if an item is created with the use of AI." https://www.etsy.com/legal/creativity
  - There is no API field for this.
  - The rule targets the *item or design*, not AI-written copy.
- **Production partners:** use the structured field `production_partner_ids`, with ids from `getShopProductionPartners`. A sentence in the description does not replace it.
- **Title rules:**
  - Title regex: `/[^\p{L}\p{Nd}\p{P}\p{Sm}\p{Zs}™©®]/u` marks the disallowed characters.
  - **Each of `%`, `:`, `&` and `+` may appear only once.**
  - Guidance since 2025 is titles under about 15 words [U].
- **Tag and material rules:** tags allow letters, digits, spaces, `-`, `'` and ™©®. Materials allow letters, digits and spaces only.
- **IP policy:** repeat IP infringement means termination, and new shops are refused. https://www.etsy.com/legal/ip
- **Ship-by rules** (https://help.etsy.com/hc/en-us/articles/115015588087):
  - The deadline is the end of the processing time, in the **shop's time zone**, by 11:59 pm.
  - Sundays and postal holidays roll forward.
  - The ship-by date can be extended once, before it passes, by up to 21 days.

---

## 4. Amazon SP-API: new rules and corrections

(developer-docs.amazon.com now 301-redirects to developer-docs.amazon.)

**Auth**
- **Correction to doc 04: refresh tokens are not permanent.**
  - Public-app authorizations expire after **365 days**, and also when the app adds roles.
  - Amazon emails the seller 30 days ahead. Re-authorization issues a new refresh token.
  - https://developer-docs.amazon.com/sp-api/docs/renew-authorizations
- **MUST: rotate the LWA client secret every 180 days.**
  - Amazon notifies 90 days ahead. The old secret dies 7 days after a new one is generated.
  - **Missing the deadline stops all calls.**
  - Automate it with the Application Management API.
  - https://developer-docs.amazon.com/sp-api/docs/rotating-your-apps-lwa-credentials

**Data Protection Policy** (update effective 2025-11-25, https://developer-docs.amazon/sp-api/changelog/updates-to-the-data-protection-policy-and-acceptable-use-policy)
- PII retention: no longer than 30 days after delivery.
- Non-PII: at most 18 months.
- Logs: at least 12 months.
- Security controls:
  - TLS 1.2+ and a KMS.
  - Lockout after 10 failed logins; password history of 10.
  - Critical vulnerabilities fixed within 7 days, high within 30.
  - A named Incident Management Point of Contact.
  - Risk assessments of subcontractors (so our AWS, Anthropic and EasyPost vendor list must be documented).

**Restricted Data Tokens and orders**
- **RDTs are still required** for Orders v0 PII calls, Merchant Fulfillment, Shipping `getShipment`, `getReportDocument` for PII reports and Easy Ship. https://developer-docs.amazon/sp-api/docs/tokens-api-use-case-guide
  - Orders v2026-01-01 uses role-based access instead.
  - Amazon Custom: the zip link is at `orderItems[].product.customization.customizedUrl`.
- **Orders v0 end of life:**
  - v0 reads (`getOrders`, `getOrder`, `getOrderItems`, `getOrderAddress`, the buyer-info calls) are **removed 2027-03-27**.
  - **`confirmShipment` and `updateShipmentStatus` exist only in v0.** So: read on v2026, confirm shipments on v0.
  - https://developer-docs.amazon/sp-api/docs/orders-api
- **v2026 details:**
  - Status enum uses **`CANCELLED`** (double L), plus UNFULFILLABLE, PENDING_AVAILABILITY and INVOICE_UNCONFIRMED.
  - Request `includedData=FULFILLMENT,RECIPIENT,CANCELLATION`.
  - The `searchOrders` pagination token expires after 24 h.
  - https://developer-docs.amazon/sp-api/docs/orders-api-migration-guide
- **MUST: `searchOrders` is 0.0056 rps (about 1 call per 3 min, burst 20).**
  - Drive intake from **ORDER_CHANGE notifications** and `getOrder` at 0.5 rps.
  - Use `searchOrders` only for a slow reconciliation sweep.
  - https://developer-docs.amazon/sp-api/docs/orders-api-rate-limits
- **ORDER_CHANGE:**
  - Fields: `OrderChangeType` (OrderStatusChange, **BuyerRequestedChange**) and `OrderChangeTrigger.TimeOfOrderChange`.
  - Filter with `orderChangeTypes`.
  - SQS may deliver copies; dedupe on `NotificationId`.
  - https://developer-docs.amazon/sp-api/docs/tutorial-subscribe-to-order-change-notification , https://developer-docs.amazon.com/sp-api/docs/set-up-notifications-with-amazon-sqs
- **`confirmShipment`:**
  - Needs `packageReferenceId` (a positive numeric string), `carrierCode` (`carrierName` only when the code is Other), `trackingNumber`, `shipDate` and `orderItems[{orderItemId, quantity}]`.
  - Seller-initiated cancellation is **only** through `POST_ORDER_ACKNOWLEDGEMENT_DATA` feeds. https://developer-docs.amazon/sp-api/reference/confirmshipment
- **OTDR (from 2026-02-28, [3P] forum announcement):**
  - Below 90%, Amazon deactivates the listings that contribute most.
  - OTDR protection needs automated handling time plus Buy Shipping or Veeqo labels.
  - Implication: **EasyPost labels are not OTDR-protected.** Shops heavy on Amazon may prefer Amazon Buy Shipping for Amazon orders. That adapter is backlog.

**Listings and policy**
- **From 2026-07-22, photoreal AI-generated people** in images, video or A+ content must carry the XMP `dc:subject` keyword `contains-synthetic-performer` [3P]. https://www.geekseller.com/blog/amazon-introduces-new-rules-for-ai-generated-images-july-2026/
  - Our mockups: if a generated model or person is ever added, imaging must write that XMP tag.
- **Agent Policy:** the BSA update effective 2026-03-04 adds rules for automated software and AI agents. Requirements such as human-approval thresholds for bulk changes are [U]. Keep human approval on every AI publish, which we already do. https://sellercentral.amazon.com/seller-forums/discussions/t/84e3f6b1-42f7-4cf3-a189-a5cc8d78d838

**Fees and tax**
- Clothing referral fee: **5% ≤ $15, 10% $15–20, 17% > $20**, minimum $0.30, on item + shipping + gift wrap, not tax. https://sell.amazon.com/pricing
- Amazon is marketplace facilitator in all sales-tax states. https://sellercentral.amazon.com/help/hub/reference/external/G7VYHGJ8ZT2M58CP

---

## 5. Shopify: new rules and corrections

**Tokens**
- **MUST: use expiring offline tokens (`expiring=1`).**
  - Access tokens last 1 h. Refresh tokens last 90 d and **rotate on every refresh**.
  - Required for public apps created on or after 2026-04-01; non-expiring tokens stop working for **all** public apps on 2027-01-01.
  - https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/offline-access-tokens , https://shopify.dev/changelog/expiring-offline-access-tokens-required-for-all-public-apps-as-of-january-1-2027

**Inventory mutations**
- **MUST (API 2026-04+):**
  - `inventorySetQuantities` no longer accepts `compareQuantity` or `ignoreCompareQuantity`. Pass `changeFromQuantity` (the expected quantity, or explicitly `null`).
  - **`@idempotent(key: "<uuid>")` is mandatory** on inventory and refund mutations. The check happens at runtime even though the schema does not show it as required.
  - https://shopify.dev/changelog/finalizing-compare-and-swap-redesign-for-inventory-set-quantities , https://shopify.dev/changelog/making-idempotency-mandatory-for-inventory-adjustments-and-refund-mutations
- **SHOULD:** use `inventoryAdjustQuantities` unless we really are the source of truth. With opt-in availability push, we are the source of truth only for mapped SKUs.

**App review and privacy**
- **MUST for the App Store:**
  - Compliance webhooks (`customers/data_request`, `customers/redact`, `shop/redact`) declared in `shopify.app.toml`, completed within 30 days. `shop/redact` arrives 48 h after uninstall. https://shopify.dev/docs/apps/build/compliance/privacy-law-compliance
  - GraphQL only.
  - Billing API for charges.
- **Protected customer data Level 2** (name, address, email, phone):
  - Each field is approved separately.
  - **Without approval the fields return `null` with HTTP 200.** An order with a null ship-to must go to a "needs address" hold, never to an empty label.
  - https://shopify.dev/docs/apps/launch/protected-customer-data

**Webhooks**
- **Subscriptions:**
  - Shop-scoped subscriptions created through the API are **deleted after repeated failures within 24 h**.
  - Prefer app-scoped TOML subscriptions, or re-check subscriptions daily. https://shopify.dev/docs/apps/build/webhooks/troubleshoot
- **Dedupe and ordering:**
  - Dedupe on `X-Shopify-Webhook-Id`. `X-Shopify-Event-Id` groups deliveries from the same merchant action.
  - Order events by `X-Shopify-Triggered-At` or `updated_at`.
  - https://shopify.dev/docs/apps/build/webhooks/ignore-duplicates , https://shopify.dev/docs/apps/build/webhooks/best-practices

**Rate limits**
- Read `extensions.cost.throttleStatus {currentlyAvailable, restoreRate}`. Before each call, wait `(requestedCost − available) / restoreRate` seconds.
- Use bulk operations for backfills.
- https://shopify.dev/docs/api/usage/limits

**Orders**
- Only the last 60 days of orders are readable without `read_all_orders`.
- `displayFinancialStatus` includes PARTIALLY_PAID, PARTIALLY_REFUNDED and more.
- https://shopify.dev/docs/api/admin-graphql/latest/enums/OrderDisplayFinancialStatus

**Money**
- The seller remits sales tax; Shopify is not a marketplace facilitator [3P].
- Shopify Tax: 0.35%, capped at $0.99 per order, after the $100k threshold. For stores created on or after 2026-05-13 the threshold counts lifetime sales, not a year. https://help.shopify.com/en/manual/taxes/shopify-tax/pricing
- Using another payment provider alongside Shopify Payments adds 1.25%. https://help.shopify.com/en/manual/payments/shopify-payments/onboarding/cost-of-shopify-payments

---

## 6. TikTok Shop: new rules and corrections

partner.tiktokshop.com needs JavaScript and could not be fetched, so the API details in this section are [3P] or [U]. Seller Center policy pages were readable.

**Seller Shipping**
- **Correction to doc 01: Seller Shipping is still allowed in the US.**
  - TikTok announced the end (Mar 31, 2026), then withdrew it on 2026-02-17/18.
  - https://www.modernretail.co/operations/tiktok-halts-plan-to-end-independent-shipping-for-u-s-sellers-after-backlash/
  - https://seller-us.tiktok.com/university/essay?knowledge_id=3995852763301633&lang=en

**Fulfillment policy**
- Handling time is 1–2 business days.
- Dispatch (carrier scan or USPS manifest) within 2 business days. Made-to-order gets the configured handling time + 1 day.
- Auto-cancel if the order is not Awaiting Collection within 5 business days.
- LDR enforcement above 10%; VTR ≥ 95%.
- https://seller-us.tiktok.com/university/essay?knowledge_id=3668989549299511&lang=en

**Cancellations** (https://seller-us.tiktok.com/university/essay?knowledge_id=6201736389805867&lang=en)
- There is a 1-hour buyer remorse window, during which the order sits in `ON_HOLD`.
- **The seller must answer a cancel request within 24 h**, or it is auto-approved.
- Requests made after the dispatch deadline are auto-approved.
- Unshipped orders auto-cancel 7 business days after the order date.
- **MUST NOT: send an order to production while it is ON_HOLD.**

**API mechanics** [3P/U]
- **Request signing:**
  1. Sort the query params (excluding `sign` and `access_token`) and concatenate them as `key+value`.
  2. Prefix the path.
  3. Append the raw body (except for GET and multipart).
  4. Wrap the result as `secret + … + secret`.
  5. Take the hex HMAC-SHA256.
- **Other conventions:**
  - Success is `code == 0` in the body, not the HTTP status.
  - The API version is pinned **per endpoint** (202309, 202407, 202509…).
  - `shop_cipher` is required on most shop-scoped calls.
- **Webhook events:** ORDER_STATUS_CHANGE, CANCELLATION_STATUS_CHANGE, RETURN_STATUS_CHANGE, PACKAGE_UPDATE, **RECIPIENT_ADDRESS_UPDATE**, SELLER_DEAUTHORIZATION and UPCOMING_AUTHORIZATION_EXPIRATION.
  - The signature has no timestamp. Dedupe on `tts_notification_id`.
  - https://hookdeck.com/webhooks/platforms/guide-to-tiktok-shop-webhooks-features-and-best-practices

**Fees and tax**
- Referral fee: 6% official since 2024-04-01 (https://seller-us.tiktok.com/university/essay?knowledge_id=5982454398175018). Reported as **8% for most non-food categories from 2026-08-04** [3P, multiple sources, e.g. https://www.darkroomagency.com/observatory/tiktok-shop-fees-seller-cost-breakdown-2026 , https://delzonic.com/blogs/tiktok-shop-fee-increase-2026/].
- Sales tax is charged on referral fees since 2025-11-01. https://seller-us.tiktok.com/university/essay?knowledge_id=1017269682849550
- TikTok is marketplace facilitator. https://seller-us.tiktok.com/university/essay?knowledge_id=77147478607658&lang=en

**Content**
- The Aug 2026 Policy Pulse bans AI edits that show fictional functions or exaggerated results. https://seller-us.tiktok.com/university/essay?knowledge_id=6747273381791534&lang=en
- An AIGC label on AI-generated models or scenes is [U] for the US.

---

## 7. Walmart Marketplace: new rules and corrections

**Auth and approval**
- **Correction to doc 04:** new solution providers use **OAuth 2.0 authorization code**, not client credentials or delegated keys.
  - The authorize URL is `login.account.wal-mart.com/authorize?...&clientType=seller`.
  - Access token lasts 15 min; refresh token lasts 1 yr.
  - Headers: `WM_PARTNER.ID`, `WM_MARKET`, `WM_QOS.CORRELATION_ID`.
  - https://developer.walmart.com/us-marketplace/docs/oauth-20-authorization
- **App Store approval takes 3–5 weeks.** https://developer.walmart.com/us-marketplace/docs/app-registration-and-approval-process-for-publishing-to-app-store

**Orders**
- **MUST: acknowledge seller-fulfilled POs** (`POST /v3/orders/acknowledge`). Timing is [U]; do it on intake. https://developer.walmart.com/us-marketplace/docs/acknowledge-order
- **Ship lines** (https://developer.walmart.com/us-marketplace/reference/shippingupdates):
  - Per `lineNumber` with `statusQuantity`.
  - Use `carrierName.carrier` from the exact supported list, or `otherCarrier` plus `trackingURL`.
  - `shipDateTime` is epoch ms.
  - Set `intentToCancelOverride` only when deliberately shipping despite a cancel request.
- **Push tracking only after the carrier handoff.** VTR needs a scan within 2 business days of confirmation [3P].

**Performance and rate limits**
- **Correction:** on-time delivery is **≥ 90%** (not 95%), VTR ≥ 99%, cancellation < 2%.
- Refund Rate was replaced on 2026-04-14 by Item Not Received ≤ 2% and Return Rate ≤ 6% [3P]. https://marketplacelearn.walmart.com/guides/Policies%20&%20standards/Shipping%20&%20fulfillment/Shipping-and-fulfillment-policy
- Rate-limit headers `x-current-token-count` and `x-next-replenish-time` (also spelled `...-replenishment-time`) are read case-insensitively. A solution provider's allotment is separate from the seller's own. https://developer.walmart.com/us-marketplace/docs/rate-limiting

**Listings**
- Item spec **5.x** (5.0.20260114) is required; 4.x is sunset. https://developer.walmart.com/us-marketplace/lang-fr_CA/page/deprecation-notice-items-spec-4x-versions
- AI content must be truthful, rights-held and seller-reviewed; there is no labeling mandate. https://marketplacelearn.walmart.com/releasenotes/new-compliance-guidelines-for-ai-generated-content

**Fees**
- Apparel referral: **5% ≤ $15, 10% $15–20, 15% > $20**, on the total including shipping. https://marketplace.walmart.com/pricing

---

## 8. Shipping, suppliers and DTF production

### EasyPost
- **Webhooks:**
  - Signature: `X-Hmac-Signature: hmac-sha256-hex=<hex>`, an HMAC-SHA256 of the raw body. The secret is NFKD-normalized and UTF-8 encoded before use. Source: official client, https://raw.githubusercontent.com/EasyPost/easypost-python/master/easypost/util.py
  - A v2 header signs timestamp + method + path + body [U].
  - Respond within **7 s**. EasyPost retries up to 6 times, and **endpoints that keep failing are auto-disabled**. https://docs.easypost.com/guides/webhooks-guide
  - Events to consume: `tracker.updated` (delivered, which starts the PII clock and the delivered state), `refund.successful`, `scan_form.*`, and `shipment.invoice.updated` (billing adjustments, new 2026-08-29). https://docs.easypost.com/docs/events , https://docs.easypost.com/releases
- **No documented idempotency on `/buy`.** Lock the shipment row and commit a "buying" state. Call buy outside the transaction. On timeout, `GET /shipments/{id}` and check `postage_label` before any retry. https://docs.easypost.com/docs/shipments
- **Rate limits:** index endpoints allow 5 rps (since 2025-11-23); buy and rate calls have a load-based limiter. Expect 429 with no `Retry-After`. https://docs.easypost.com/guides/rate-limiting-guide
- **Refunds:**
  - USPS labels must be refunded within **30 days** and before any scan. UPS and FedEx allow 90 days.
  - The refund is asynchronous: treat `submitted` as pending until `refund.successful` arrives.
  - SHOULD: auto-void unused USPS labels before day 28.
  - https://docs.easypost.com/docs/shipments/shipping-refund
- **Address verification:** `verify` does not block and returns details in `verifications.delivery`; `verify_strict` fails the request. https://docs.easypost.com/docs/addresses
- **Multi-tenant (Referral Customers):**
  - Each shop gets its own billing.
  - **API keys are returned once, at creation**, so store them encrypted immediately.
  - Needs partner status.
  - https://docs.easypost.com/docs/users/referral-customers

### USPS and UPS 2026
- **USPS from July 12, 2026:**
  - **Length, width and height are required** on commercial parcel manifests.
  - The dimensional-weight divisor drops from 166 to **139**, and dimensions round up to whole inches.
  - $50 fee per mislabeled package.
  - https://www.govinfo.gov/content/pkg/FR-2026-05-15/html/2026-09785.htm , https://www.easypost.com/blog/usps-july-12-2026-price-change/
  - Unmanifested / package-quality non-compliance fee of $0.25 per piece [3P].
- **Peak surcharges** (https://www.easypost.com/blog/peak-season-surcharges-2026/):
  - USPS Ground Advantage, **Oct 4, 2026 – Jan 17, 2027**: $0.40–$0.55 for 0–3 lb.
  - UPS residential and Ground Saver, **Sep 27, 2026 – Jan 16, 2027**: $0.50, rising to $0.75 from Nov 22 to Dec 26.
  - Profit estimates must use the bought label's cost, never a cached rate.
- **UPS:** 5.9% general rate increase (2025-12-22). Additional Handling applies above 10,368 in³ from 2026-01-26 [3P]. OAuth is mandatory; multi-account integrators use the auth-code flow [3P].

### S&S Activewear
- **Rate limit:** 60 req/min, with an `X-Rate-Limit-Remaining` header. 429 behavior is undocumented, so back off 60 s on a 429.
- **Inventory:** `GET /v2/inventory/?style=` returns `warehouses[{warehouseAbbr, qty}]`. https://api.ssactivewear.com/V2/Inventory.aspx
- **Orders** (https://api.ssactivewear.com/V2/Orders_Post.aspx):
  - `POST /v2/orders` supports `testOrder` and **`rejectLineErrors`**. Set it so partial acceptance doesn't silently drop lines.
  - Shipping method codes: 1 Ground (S&S picks the carrier), 40 UPS Ground, 6 Will Call, and others.
- **Invoices are PDF only.** Landed cost has to come from the order response or the PO. https://api.ssactivewear.com/V2/Invoices.aspx
- **Bella+Canvas has moved to SanMar** (closed June 29, 2026), and S&S sells B+C only until its stock runs out.
  - The catalog needs **several suppliers per blank SKU** and SanMar PromoStandards SOAP (`ws.sanmar.com:8080`, UAT at `uat-ws.sanmar.com`).
  - https://www.sanmar.com/medias/sys_master/root/h5b/hde/10127344533534/SanMar-Web-Services-Integration-Guide-v18.8.pdf

### DTF production practices our docs lack
Mostly vendor sources [3P].

- **Gang-sheet spacing:**
  - At least **0.25 in** between designs, 0.5 in where contour cutting is used.
  - A 0.25 in margin on every edge, with 22 in as the safe artwork width.
  - Make sheet length and RIP queue (device, print mode, media) configurable per vendor or tenant.
  - https://pdfpress.app/blog/dtf-gang-sheet-spacing-and-gaps , https://ontargetprintsolutions.com/blogs/learn/dtf-gang-sheet-file-setup
- **Files:** 300 DPI at final size is the target and **150 DPI is the hard floor**. Transparent RGB PNG, or TIFF.
- **CADlink Digital Factory:** looks up jobs **by job name or barcode**, and the white underbase has choke settings. So the sheet file name and the barcode must carry our sheet id. https://help.cadlink.com/website/digital_factory/en/production/vpm_interface.htm
- **Capacity planning:**
  - Prestige XL2 is quoted at 65–80 ft²/hr (spec sheet) vs 80–100 (marketing). Plan with the lower number.
  - Epson G6070: 35.4 in wide.
  - Printers need daily nozzle checks, at least 15 min of white-ink agitation, and weekly capping-station cleaning. So capacity should subtract a morning maintenance block.
- **Transfer shelf life:** 6–12 months stored flat at 40–60% RH, sealed. SHOULD: flag printed transfers (`transfer_in`) older than about 90 days.
- **QC:**
  - Stretch test and edge check per batch.
  - Wash-test one sample per batch, 24 h or more after pressing.
  - Cracking points to under-cure, a weak underbase or a thick ink layer. Peeling points to under-cure, moisture or uneven pressure.
  - Add these as QC fail reasons (`under_cure`, `peeling`, `cracking`) so defects trace back to curing and pressing.

---

## 9. What our current code and docs get wrong or miss

These were checked against `invai-backend/src` and `invai-contracts/src` on 2026-09-24. Severity is marked **P0** (breaks in production or violates a policy), **P1** or **P2**.

### Shopify (the only live adapter)
1. **P0 — inventory push will fail on 2026-07.** `channels/shopify/live.ts` `setAvailability` sends `ignoreCompareQuantity: true` and no `@idempotent` directive. Both were changed in 2026-04, and our pinned version is 2026-07.
   - Fix: use `changeFromQuantity: null` (or the known quantity) and add `@idempotent(key: <uuid stored per push>)`.
2. **P0 — no token refresh.**
   - `exchangeShopifyCode` does not send `expiring=1` and does not store `refresh_token` or `expires_in`.
   - Nothing in `modules/channels` refreshes tokens.
   - `ChannelCredentials.refreshToken/expiresAt` exist but are never used.
   - Consequences: a new public app is rejected today, and every connection breaks on 2027-01-01.
3. **P0 (App Store) — no compliance webhooks.** There is no `customers/data_request`, `customers/redact` or `shop/redact` handling and no `shopify.app.toml`. Webhooks are created per shop through `webhookSubscriptionCreate` (`finishShopifyInstall`), so Shopify may delete them silently after failures, and nothing re-checks them.
4. **P1 — polling misses orders.**
   - `fetchOrders` filters `financial_status:paid`, so PARTIALLY_REFUNDED, PARTIALLY_PAID and authorized orders are skipped by polling. A partially refunded order that still needs shipping is lost if its webhook was missed. Filter on `updated_at` only and decide by status in code.
   - The first sync looks back 7 days, but only 60 days are readable anyway, so this is fine.
   - Line items use `quantity`, not `currentQuantity`, so order edits and removals are not reflected.
5. **P1 — throttling ignores `throttleStatus`.** The code queries `extensions.cost` but sleeps a fixed 1 s or 2 s and gives up after 3 tries. `setAvailability` also runs one `productVariants` query per SKU. Batch the lookups (`sku:a OR sku:b`), cache inventory-item ids, and wait on `restoreRate`.
6. **P1 — null PII not handled.** Without Level-2 approval, `shippingAddress` and `email` come back null, and `gqlOrderToNormalized` gives `shipTo: null`. Confirm that orders with `shipTo: null` go to an "address needed" hold, and add the data-access request to the launch checklist.

### Webhooks (all channels)
7. **P0 — Etsy dedupe uses the wrong header.**
   - `api/webhooks.ts` dedupes generic channels on `x-etsy-delivery-id`, which does not exist. Etsy sends `webhook-id`, so every Etsy delivery gets a random UUID and is never deduped.
   - Also, that route enqueues **before** verifying the signature. Verify synchronously as the Shopify route does, and use Standard-Webhooks verification with multi-signature support and a 5-minute tolerance.
8. **P1 — the dedupe window is too short.** Dedupe relies on the BullMQ `jobId`, and `removeOnComplete` keeps jobs for 24 h (`lib/queues.ts`). Etsy retries for about 30 h. Use a persisted `webhook_deliveries` table (R4).
9. **P1 — no staleness check.** `orders/import.ts` `updateExisting` applies totals, ship-by and **address** from any payload without comparing the channel's `updated_at`. An out-of-order `orders/updated` delivery can revert an address change. Store `channelUpdatedAt` on orders and ignore older payloads.

### Order model
10. **P1 — cancellation is whole-order only.**
    - `cancelFromChannel` cancels every open unit, and `FetchOrdersResult` carries only `cancelledChannelOrderIds`.
    - Amazon, Walmart and TikTok cancel per line, and Shopify edits remove lines.
    - Needed:
      - line and quantity cancellation events (`{channelOrderId, channelLineId, quantity}`);
      - a **buyer-cancel-request** state that holds units before they go on a sheet (TikTok's 24 h clock, Amazon BuyerRequestedChange, Walmart intent-to-cancel);
      - an `on_hold`/`awaiting_release` state for TikTok ON_HOLD and Amazon PENDING orders.
11. **P1 — ship-by gaps.**
    - `shipby.ts` skips weekends but not **postal holidays**, and Etsy counts Sundays and postal holidays differently from Saturdays.
    - Etsy CSV import sets `shipBy: null`, so Etsy orders fall back to a flat 3 business days even though `CHANNEL_RULES.etsy.shipBy.source` is `channel_provided`. The Etsy API adapter must read the per-transaction `expected_ship_date`. For CSV, show "estimated" in the UI.
    - `ChannelShipByRules` has a single order-level ship-by. Etsy sends it per transaction.
12. **P2 — pending adapter comments are outdated.**
    - `channels/amazon/index.ts` plans Orders `getOrders/getOrderItems` (v0, removed 2027-03-27) and `POST_ORDER_FULFILLMENT_DATA`. Plan instead: v2026 `getOrder` plus ORDER_CHANGE for reads, v0 `confirmShipment` for tracking, and the acknowledgement feed for cancels.
    - `channels/walmart/index.ts` does not mention the acknowledge step or OAuth auth-code.
    - `channels/tiktok/index.ts` should note per-endpoint versions and ON_HOLD.

### Shipping
13. **P1 — label buy is not crash-safe.**
    - `modules/shipping/service.ts` `buyLabel` takes `SELECT … FOR UPDATE`, calls EasyPost `buy` and downloads and uploads the PDF, all inside the DB transaction.
    - If anything after the buy fails (S3, the insert or a timeout), the transaction rolls back and the postage stays paid but unrecorded. A retry then buys a **second** label.
    - Fix: commit a `buying` state, buy outside the transaction, persist `carrierShipmentId`, and on retry GET the shipment first (R8).
14. **P1 — no EasyPost webhooks.**
    - Delivered status (for the PII purge and the "delivered" state) and asynchronous refund results are not consumed.
    - `void()` treats `submitted` as success. It should be `refund_pending` until `refund.successful`.
15. **P1 — no USPS SCAN form.** SCAN forms make TikTok dispatch and Walmart scan-based metrics count at manifest time (R11). Add a daily "end of day" SCAN-form action.
16. **P2 — no address verification.** Add `verify` at label-rate time and surface `verifications.delivery.errors` before buying. The `rate` call sends no `verify` today.
17. **P2 — rate TTL is too long across USPS price changes.** Our rate TTL must not cross a USPS price-change midnight (Central). Parcel dimensions are sent (good, since they are required since July 12), but the parcel fallbacks (length 10 in, height 1 in, from `service.ts` around line 541) and any saved presets must never be 0 (EasyPost rejects zero values since 2025-09-27).

### Money (contracts `CHANNEL_RULES` and `finance/profit.ts`)
18. **P1 — flat referral percentages.**
    - Amazon (flat 17%) and Walmart (flat 15%) are really **tiered by the unit's sale price**: 5% ≤ $15, 10% $15–20, 17% or 15% > $20. Amazon also has a $0.30 minimum per item.
    - Many DTF tees sell at $15–20, so our fees overstate costs by 7 or 5 points there.
    - `ChannelFeeDefaults` needs tiers (`[{upToCents, pct}]`) and a per-item minimum.
19. **P1 — TikTok fee note is outdated.** The note says "referral ~6% + 2% transaction". Reports say the referral fee is **8%** since 2026-08-04, with sales tax charged on the fee. Mark it "verify" in the UI.
20. **P1 — refunds don't recover the right fees.** Refund cost is modeled only as cancelled units, with fees dropped entirely.
    - Etsy credits processing fees proportionally and refunds the transaction fee.
    - Amazon keeps a refund administration fee of min($5, 20% of referral).
    - TikTok claws back commission.
    - Partial refunds that aren't cancellations (Etsy `refunds[]`, Shopify refunds) are ignored.
21. **P2 — Etsy fee gaps.** Paid personalization and gift wrap are part of the transaction-fee base. Offsite Ads (15% or 12%, capped at $100 per order) is not modeled. It is only knowable from the ledger, so reconcile it (R16).
22. **P1 — Shopify sales tax.** Shopify is the only channel where the **shop owes the sales tax**. Profit excludes tax from revenue, which is correct. Two gaps:
    - Nothing shows the tax owed.
    - Shopify Tax (0.35%, capped at $0.99 per order) and the 1.25% third-party gateway premium are not modeled.
    - Marketplace-facilitator channels are fine (tax is a pass-through).

### AI listings (`ai/validators/listing.ts`)
23. **P1 — the Etsy disclosures are aimed wrong.**
    - `AI_DISCLOSURE` says the *copy* was drafted with AI. Etsy's rule is about the **item or design** being created with AI, stated in the description. We must add that text when the design itself was AI-assisted; the copy disclosure is optional.
    - `PARTNER_DISCLOSURE` says the design is "printed as a DTF transfer by our production partner". That is **false for shops that print in-house**, which is our target segment. The text must come from the shop's settings.
    - Etsy requires the structured `production_partner_ids` field, not text.
24. **P1 — Etsy title validation is incomplete.** It only rejects `$^\``. Add the "each of `% : & +` at most once" rule and the Unicode class whitelist (§3).
25. **P2 — `requiresAiDisclosure` is a single boolean.** Amazon now needs the `contains-synthetic-performer` XMP tag when an image shows a photoreal AI person (from 2026-07-22). TikTok bans exaggerated AI edits. Walmart requires truthful, rights-held content. Model these as per-channel image rules for the imaging service.

### Compliance, security and ops
26. **P1 — Etsy terms: no emailing buyers.** The mailer or notifications must never send order, shipping or tracking emails to Etsy buyers. The required Etsy trademark notice ("…is not endorsed or certified by Etsy") must be in the web footer and on the connect screen.
27. **P1 — Amazon DPP 2025-11 items to add to the security review before applying:** KMS, 12-month log retention, 18-month cap on non-PII, 10-attempt lockout, 7- and 30-day patch SLAs, a named IMPOC, and a subprocessor risk-assessment list.
    - Our 30-days-after-delivery PII purge (`orders/jobs.ts`) matches the DPP, but it depends on delivery events we don't ingest yet (item 14). Today it falls back to 30 days after ship.
28. **P1 — credential calendar.** We need a job that tracks the Amazon 180-day LWA secret rotation, Amazon's 365-day re-authorization, Walmart's 1-year refresh token, TikTok's `UPCOMING_AUTHORIZATION_EXPIRATION`, and the Etsy and Shopify 90-day refresh tokens (R2).
29. **P2 — suppliers.**
    - `suppliers/sanmar/index.ts` is a 2-line stub, yet Bella+Canvas is now SanMar-only. Supplier choice must be per blank SKU.
    - The S&S adapter doesn't retry on 429, and should send `rejectLineErrors: true` on orders.
30. **P2 — DTF defaults to add:** 0.25 in gap and edge margin in nesting (check it against the imaging service's rectpack settings), a 150 DPI hard floor, QC reasons `under_cure`/`peeling`/`cracking`, a transfer-age warning, and a printer maintenance block in capacity.

### Corrections to earlier research docs
- **Doc 04:**
  - Amazon refresh tokens are not permanent (365-day re-authorization), and client secrets rotate every 180 days.
  - Walmart uses an auth-code OAuth for solution providers, not client credentials.
  - Amazon Orders v0 `confirmShipment` is still required after moving reads to v2026.
- **Doc 01:**
  - TikTok Seller Shipping continues; the shutdown was withdrawn.
  - Walmart on-time delivery is 90%.
  - Amazon apparel referral is tiered; "15–17%" is wrong below $20.
  - The TikTok fee is now reported at 8%.
  - The Etsy trademark notice wording has changed (§3).
- **Doc 03:** "TikTok claws back commission on every refund" is incomplete. Etsy also refunds fees proportionally, and Amazon keeps a refund administration fee.
