RESEARCH REPORT: Integrations and AI feasibility for a multi-tenant DTF apparel SaaS (as of Sept 2026)

Sourcing note: I hit the session's WebSearch cap (200/200) partway through. After that I used WebFetch only, on official docs where I could. Items marked [K] come from my own knowledge and were not re-checked this session. Confirm them before you build on them.

==================================================
1. ETSY OPEN API v3
==================================================
Access tiers (vorplabs summary, reviewed 2026-07-27):
- Seller App: own shop only. Approval is automatic and near-instant. No commercial use.
- Personal App: can go beyond your own shop at limited scale. Gets a deeper review.
- Commercial Access: this is what multi-tenant SaaS needs (many sellers authorizing via OAuth). You must first have an approved Personal App, then pass a separate manual review. No timeline is published.
  - Review criteria: follow the API Terms and caching rules, clearly distinguish the app from Etsy (prominent trademark disclaimer, no "Etsy" in the brand name), and no scraping.
  - Plan for weeks, not days. The SaaS cannot onboard outside shops until this is approved.
- Etsy also has an "OpenAPI Dev MCP" server. It covers docs and schemas only, not live data. Useful for coding.

Auth:
- OAuth 2.0 with PKCE. Access token lasts 1 hour, refresh token 90 days.
- Every request also needs an x-api-key header ("keystring:shared_secret").
- Scopes: transactions_r/w, listings_r/w/d, shops_r/w, address_r/w, profile_r/w, email_r.

Rate limits:
- Limits are per API key (public calls) or per OAuth token (private calls), counted as queries per second (QPS) and queries per day (QPD).
- The daily count is a rolling 24-hour sliding window.
- Headers returned: x-limit-per-second, x-remaining-this-second, x-limit-per-day, x-remaining-today. Over the limit you get 429 with retry-after.
- Default is commonly cited as 10 QPS / 10k QPD. The docs now tell you to check your app's limits in the Developer Portal; their example headers show 150/s and 100,000/day.
- To raise limits, email developer@etsy.com with your app description and estimated QPS/QPD.

Orders / receipts:
- getShopReceipts, getShopReceipt, and transactions.
- Webhooks (new, late 2025): order.paid, order.canceled, order.shipped, order.delivered.
  - Signed with HMAC-SHA256 (Standard-Webhooks style: webhook-id, webhook-timestamp, webhook-signature; secret is prefixed whsec_).
  - Reject messages older than about 5 minutes.
  - 8 retries with backoff over about 37 hours. Make handlers idempotent and keep a polling fallback.

Tracking:
- createReceiptShipment: POST /v3/application/shops/{shop_id}/receipts/{receipt_id}/tracking with carrier and tracking code. Needs transactions_w.

Listings:
- createDraftListing requires quantity, title, description, price, who_made, when_made, taxonomy_id, shipping_profile_id and readiness_state_id (physical items), and image_ids before activation.
- Processing profiles (createShopReadinessStateDefinition: ready_to_ship or made_to_order) replaced the old processing-time fields. Those legacy fields were slated for removal in Q1 2026.
- Taxonomy: getSellerTaxonomyNodes, then getPropertiesByTaxonomyId. Only properties with supports_variations=true can be variations.

Images:
- uploadListingImage: POST .../listings/{id}/images, multipart binary. At least 1 image to publish; Etsy's UI allows up to 20 [K].
- Video: multi-video (2 per listing) is rolling out now. Transition window is Sept 21 to Oct 21, 2026, via the is_multi_video flag on uploadListingVideo.

Variations / inventory (updateListingInventory):
- Payload is products[] with sku, property_values, and offerings (price, quantity, is_enabled, readiness_state_id), plus price_on_property / quantity_on_property / sku_on_property.
- Gotcha: you must PUT the entire products array on every update. There is no per-SKU patch.
- Offerings sharing a SKU must have the same quantity.
- Product caps: 70 with one variation property, 4,900 with two (e.g. size x color), 2,500 with three, 400 above that.
- A third variation needs custom property IDs 513, 514 or 516.

Personalization (changed Feb 6, 2026; migration window closed Apr 9, 2026):
- Up to 5 questions per listing, each of type text, dropdown, or file upload.
- Endpoints: get/update/deleteListingPersonalization. Writing multiple questions requires ?supports_multiple_personalization_questions=true.
- In orders, answers appear in transaction.variations with property_id 54. Several entries can share that ID, formatted_name is set by the seller, and file uploads come through as URLs.
- The legacy fields (personalization_is_required, _char_count_max, _instructions) now cause errors if sent.
- This matters for DTF: customer-uploaded art arrives as a URL you can pull straight into the print queue.

Messages: there is no Conversations/Messages endpoint in v3 (GitHub discussion #1547 is still an open request). AI auto-replies to Etsy messages are not possible through the official API. Browser automation or scraping would breach the terms and endanger Commercial Access. Workable options:
- Draft replies in your app for the seller to paste.
- Handle non-Etsy channels.
- Trigger post-purchase emails from the order.paid webhook. Check Etsy's policy on emailing buyers first.

AI content rules for sellers:
- Etsy Creativity Standards require disclosure when AI is used, and the "Designed by" attribution.
- June 10, 2025: the allowance for "templated designs" was removed. Everything must be based on the seller's original design.
- Production partners (such as a DTF shop) must be disclosed.
- From March 1, 2026, listing images that are fully or substantially AI-generated must be disclosed (third-party reporting; confirm against the Etsy Seller Handbook).
- Mass-generated, uncurated listings are an enforcement target.
- Product implication: human review and approval of each design, auto-inserted disclosure text, and throttled publishing.

Etsy API Terms: I could not load them (etsy.com/legal/api returned 403). [K] They limit caching to about 6 hours for most data and restrict use of buyer data. Have counsel read them, especially on AI training with Etsy data.

Sources:
- https://developers.etsy.com/documentation/essentials/rate-limits/
- https://developers.etsy.com/documentation/essentials/webhooks/
- https://developers.etsy.com/documentation/essentials/authentication/
- https://developers.etsy.com/documentation/tutorials/listings
- https://developers.etsy.com/documentation/tutorials/personalization-migration/
- https://developer.etsy.com/documentation/tutorials/fulfillment/
- https://github.com/etsy/open-api/discussions/1547
- https://vorplabs.com/agent-tools/etsy-api
- https://www.etsy.com/seller-handbook/article/1275449912004
- https://iscompliant.app/Blog/etsy-creativity-standards-pod-sellers-guide

==================================================
2. AMAZON SP-API
==================================================
Registration:
- Private developer: for your own seller account, self-authorized.
- Public developer: required to serve other sellers via OAuth. The app must be listed in the Selling Partner Appstore, and you need a public website.
- You must accept the Acceptable Use Policy, Data Protection Policy, and Solution Provider Portal Agreement.
- The developer profile (500 words max) includes security-control questions answered by your security team.

PII (restricted roles, needed to see ship-to addresses for merchant-fulfilled orders):
- Public apps go through an architecture review by the SP-API Solutions Architecture team: data-flow diagrams and PII protection controls.
- Controls include: encryption at rest and in transit, vulnerability scans at least every 180 days, annual penetration test, PII deleted within 30 days after shipment, encrypted backups, and an incident-response plan (Amazon must be notified of incidents within 24 hours [K]).
- PII rejections are common. This is the hardest gate in this whole report.

Fees: Amazon announced a $1,400/year fee plus $0.40 per 1,000 GET calls (Nov 2025). It then delayed the fee, paused it indefinitely on Mar 9, 2026, and cancelled it on May 12, 2026. There is currently no charge.

Orders:
- Orders API v0 is deprecated. The new version is v2026-01-01:
  - searchOrders replaces getOrders.
  - getOrder with includedData replaces GetOrder, GetOrderItems, GetOrderBuyerInfo and GetOrderAddress.
- In v2026-01-01, Restricted Data Tokens are no longer needed for PII; access is controlled by role. Package-level status is available.
- Order history: last 2 years for most marketplaces.

Shipment confirmation:
- Use confirmShipment (Orders v0; it can also edit shipment details), or buy labels through the Shipping API v2 / Merchant Fulfillment API, which confirm automatically.
- [K] Seller performance is judged on Valid Tracking Rate (target above 95%) and on-time delivery, so confirm with the carrier and tracking number promptly.
- Orders-for-Personalization: customization data for Custom products comes as a customizedURL zip download, not inline [K].

Listings:
- Listings Items API v2021-08-01: put, patch, get, delete, search. Has a VALIDATION_PREVIEW mode.
- Bulk: JSON_LISTINGS_FEED via the Feeds API.
- Get the SHIRT product type's JSON schema from the Product Type Definitions API.
- [K] Variations: parent/child via parentage_level and child_parent_sku_relationship, with variation_theme such as SIZE/COLOR.
- [K] Watch for: GTIN exemption or brand approval (a POD brand usually needs Brand Registry or a GTIN exemption), required size_system/size_class/apparel attributes, and fabric/care/country-of-origin attributes.

Merch on Demand: no API. Confirmed out of scope.

Sources:
- https://developer-docs.amazon/sp-api/docs/sp-api-registration-overview
- https://developer-docs.amazon/sp-api/docs/register-as-a-public-developer
- https://developer-docs.amazon.com/sp-api/docs/security-compliance-overview
- https://developer-docs.amazon/sp-api/docs/guidance-to-address-key-security-controls-in-sp-api-integration
- https://developer-docs.amazon/sp-api/docs/orders-api
- https://developer-docs.amazon/sp-api/docs/orders-api-migration-guide
- https://developer-docs.amazon/sp-api/docs/listings-items-api
- https://novadata.io/resources/news/amazon-cancels-sp-api-fees-may-2026
- https://github.com/amzn/selling-partner-api-models/discussions/5025

==================================================
3. OTHER CHANNELS (brief)
==================================================
Shopify (easiest):
- Leaky-bucket rate limits. Max 250 items per input array. Pagination tops out at 25,000 objects. Stores past 500k variants can create at most 10k new variants per day (not on Plus).
- [K] GraphQL Admin is roughly 100 points/s on standard plans, about 1,000 on Plus. REST is legacy; new public apps must use GraphQL only (since Apr 1, 2025).
- [K] Orders: orders/create webhook plus fulfillmentCreate with tracking. Listings: productSet / productCreate with variants (up to 2,048 variants per product since 2025).
- [K] App Store review is moderate. A custom or unlisted app avoids review but loses discovery. Protected customer data access needs a separate request.
- Source: https://shopify.dev/docs/api/usage/limits

TikTok Shop (Partner Center):
- Both public and custom apps exist. Partner approval is needed. Covers orders, products and seller-shipped fulfillment with tracking upload; has webhooks and rate limits.
- [K] Approval is moderate to hard. Requires a business entity and a Partner Center account, and the category is audited. API versions change often. Order SLAs are strict: late dispatch is penalized, and the default dispatch window is about 2-3 business days.
- Source: https://partner.tiktokshop.com/docv2/page/tts-api-concepts-overview

Walmart Marketplace:
- OAuth2 client credentials; tokens last 15 minutes. Has a Dynamic Sandbox.
- [K] A solution-provider SaaS must be approved into the Solution Provider program. Sellers themselves need Walmart seller approval, which is selective. Orders and shipment updates via the Orders API; items via bulk feeds (MP_ITEM spec).
- Source: https://developer.walmart.com/us-marketplace/docs/introduction-to-marketplace-apis

eBay:
- [K] Easiest approval: open developer program with production keysets after an account deletion-notification compliance step.
- [K] Uses Sell Fulfillment API (getOrders, createShippingFulfillment) and Inventory API (inventory items, offers, publish). Default limit is about 5,000 calls per day per API, and increases require an application growth check.
- The docs page returned 403 this session.

==================================================
4. SHIPPING
==================================================
USPS:
- Web Tools (XML) was retired on Jan 25, 2026 and is degrading or down. Use the USPS APIs at developers.usps.com.
- REST with OAuth 2.0 client credentials. APIs: Addresses, Domestic/International Prices, Labels, Tracking (with webhook subscriptions), plus others.
- Labels API requires an Enterprise Payment System (EPS) account, a CRID, a MID, and payment authorization.
- Default quota is 60 requests per hour. Contact USPS for increases.
- Direct USPS integration is painful for multi-tenant (per-tenant EPS/CRID/MID). Use an aggregator instead.
- Sources: https://www.usps.com/business/web-tools-apis/ , https://www.usps.com/business/web-tools-apis/faqs-web-tools-to-usps-apis.pdf , https://developers.usps.com/

UPS [K; the developer.ups.com fetch timed out]:
- OAuth 2.0 via developer.ups.com. APIs: Rating, Shipping, Tracking, Address Validation, Paperless.
- Each tenant needs its own UPS shipper account.
- Third-party platforms must sign up as integrators, and the UPS tech agreement applies.
- Again easier through an aggregator.

Aggregator pricing (fetched this session):
- EasyPost:
  - Free for up to 3,000 labels per month on EasyPost's own carrier accounts, then per-label fees.
  - Bring-your-own carrier accounts: $20/month plus per-label fees.
  - Tracking: $0.01-0.03 per shipment.
  - Insurance: 1% of value.
  - Includes discounted USPS and UPS rates.
  - https://www.easypost.com/pricing
- Shippo API:
  - First 30 labels per month free, then $0.07 per label.
  - Tracking $0.02, rating $0.01, US address validation $0.02 (international $0.08).
  - Insurance 1.25% (US) or 1.5% (international).
  - Premier: custom pricing.
  - Shippo's app plans: Pro from $17/month.
  - https://goshippo.com/pricing/api
- ShipEngine (now "ShipStation API"):
  - Free plan: Shippo's carrier accounts, discounted rates.
  - Advanced: $75/month for 1k labels, $325 for 5k, $600 for 10k; overage $0.06-0.075 per label; includes bring-your-own carrier accounts and address validation.
  - Enterprise: 25k+ labels per month.
  - https://www.shipstation.com/shipping-api/pricing/
- [K] All three offer USPS rates at or below Commercial Plus (Ground Advantage cubic) and UPS discounts. Rates are similar across providers; platform fees are what differ.

Cost at 1,000 orders/day (about 30k labels/month per tenant):
- EasyPost wallet: roughly $0.05 per label after the free tier [K].
- Shippo: $0.07 per label, about $2.1k/month per tenant.
- Negotiate enterprise or partner (reseller) pricing. EasyPost, Shippo and ShipEngine all have platform-partner programs where the SaaS can mark up labels and earn revenue.

==================================================
5. BLANK SUPPLIER APIs
==================================================
S&S Activewear:
- REST API v2 with HTTP Basic auth (username = account number, password = API key; get the key from the portal or api@ssactivewear.com).
- Endpoints: categories, styles, products (with per-warehouse inventory), specs, brands, orders (GET/POST/DELETE), invoices, returns, tracking, days-in-transit.
- Limit: 60 requests per minute (X-Rate-Limit-Remaining header). Images come from cdn.ssactivewear.com.
- Best developer experience of the three.
- https://api.ssactivewear.com/V2/Default.aspx

SanMar [K; their pages returned 404]:
- SOAP web services: Product Info, Inventory, Pricing, PO submission, Order Status, Invoice.
- Also fully PromoStandards-compliant.
- Also offers SFTP bulk files (EPDD / SanMar_SDL product and inventory CSVs, refreshed often).
- Access needs a SanMar customer account plus web-services enrollment (email sanmarintegrations@sanmar.com).

AlphaBroder [K]:
- Supports PromoStandards SOAP services (inventory, product data, pricing/configuration, order status, shipment notification, PO).
- Also FTP inventory/product files. Needs a customer account and registration.

PromoStandards [K; pages returned 404]:
- An industry SOAP/XML standard. Services: Product Data v2, Inventory v2, Product Pricing & Configuration (PPC) v1, Media Content v1, Purchase Order v1, Order Status v2, Order Shipment Notification v2, Invoice v1.
- Endpoints are listed per supplier in the PromoStandards directory.
- One PromoStandards client covers SanMar, AlphaBroder and many others; add S&S REST alongside it.

==================================================
6. AI FEASIBILITY
==================================================
Listing titles, tags and descriptions: high feasibility.
- Constrain the LLM to each channel's rules:
  - Etsy: title 140 characters; 13 tags of 20 characters each.
  - Amazon: title about 200 characters (category rules plus a 2025 push toward 75-80-character titles on mobile [K]); 5 bullets; backend search terms under 250 bytes.
  - TikTok and Shopify: have their own limits.
- Add the Etsy AI disclosure and "Designed by" automatically. Validate against the Amazon SHIRT schema before submitting.

Keyword and trend data:
- Etsy has no search-volume API.
- Options: Google Trends official API (alpha since 2025 [K]); Amazon Brand Analytics / Search Query Performance via SP-API reports (requires Brand Registry [K]); the tenant's own sales and conversion data; paid tools such as eRank or Everbee (no official public APIs [K]); TikTok Creative Center trends (UI only, no API [K]).
- Do not scrape Etsy search.

AI design generation and IP risk:
- US Copyright Office (Jan 2025 report [K]): purely AI-generated images are not copyrightable. Sellers cannot enforce against copycats unless there is human authorship.
- Models can reproduce trademarks and characters. Use provider indemnity (e.g. Adobe Firefly, some OpenAI and Google enterprise terms [K]), filter prompts for brand, celebrity and character names, and require a human approval step.

Trademark screening:
- The USPTO has moved to the Open Data Portal (developer.uspto.gov now redirects to data.uspto.gov); the page didn't render for me.
- [K] Available: the TSDR API (free API key; about 60 requests per minute, lower for document downloads), plus daily and annual trademark XML bulk files.
- Build a local index: live marks in International Class 25 (clothing) and relevant slogans, matched against title words, tags, and OCR of design text.
- The TESS search tool was retired in Nov 2023 (replaced by the new Trademark Search); it had no API.
- Watch for: common-phrase trademarks ("Mama Bear" style), which drive Etsy and Amazon takedowns. Also check the Amazon Brand Registry list and Etsy IP-report patterns.
- Present results as a risk score, not legal advice.

AI mockups:
- Deterministic compositing works well: displacement map plus lighting overlay per blank style and color (Photopea/PSD smart-object style, or your own renderer).
- Generative mockups (image-to-image) risk misrepresenting the product.
- Etsy AI-image disclosure applies if images are "substantially AI-generated". Composited mockups arguably are not; confirm.

Print-ready files (DTF):
- Typical targets: 300 DPI, transparent PNG, sizes such as 12x16 in (3600x4800 px).
- Upscaling: Real-ESRGAN (open source) or hosted services (Topaz, Replicate, Higgsfield, etc.).
- Background removal: rembg/BiRefNet or commercial APIs.
- DTF-specific QA the product should run:
  - Remove semi-transparent pixels (halftone or threshold alpha, because DTF white underbase makes soft alpha look bad).
  - Set a minimum line thickness.
  - Check color gamut against CMYK+W.
- Upscaling creates pixels, not detail. Flag sources below about 150 effective DPI.

Gang-sheet auto-nesting:
- This is 2D bin/strip packing on a 22-inch-wide roll.
- Rectangles: MaxRects / Skyline heuristics are fast and give 80-90% utilization.
- Irregular shapes: no-fit-polygon (NFP) plus a genetic algorithm (SVGnest / Deepnest, open source, MIT/GPL — check licenses). Use alpha-contour polygons with a spacing offset of about 0.25 in.
- Allow 90-degree rotation. Batch by due date and film length. Export to RIP software (e.g. Cadlink, AcroRIP) as PNG or TIFF at 300 DPI.
- Very feasible in-house.

Inventory demand forecasting:
- Forecast blank demand (style/color/size) from order history.
- Use hierarchical and intermittent-demand models (Croston/TSB, LightGBM, or Prophet at the aggregate level), a size-curve distribution, supplier lead times (S&S days-in-transit endpoint) and reorder points.
- Reliable with 3+ months of history. For new tenants, fall back on industry size curves.

AI customer message replies:
- Etsy: not possible through the API (no messages endpoint).
- Amazon: the Messaging API only allows specific templated message types (e.g. confirmCustomizationDetails, unexpected problem). Free-form buyer replies are not available and buyer-seller messaging stays in Seller Central [K].
- Shopify, email and TikTok (Customer Service API exists [K]) are feasible.
- Offer "draft and copy" for Etsy and Amazon.

Profit analytics: high feasibility.
- Per-order margin = sale price - marketplace fees - label cost - blank cost - DTF film/ink/powder cost per square inch (from nesting output) - labor - ad spend.
- Fee sources: Etsy ledger (getShopPaymentAccountLedgerEntries, payments); Amazon Finances API / settlement reports; Shopify transactions; label cost from the shipping aggregator.

==================================================
KEY GOTCHAS / PRIORITIES
==================================================
1. The critical paths are Etsy Commercial Access (needs a Personal App first, manual review) and Amazon public-developer PII approval (architecture review, pen tests, 30-day PII deletion). Start both immediately. Design SOC2-style controls from day one.
2. Build on Amazon Orders v2026-01-01, not v0.
3. Etsy: no messages API. Inventory updates replace the full product array. Personalization is the new multi-question format (property_id 54, file URLs). Processing profiles are required. Multi-video transition ends Oct 21, 2026.
4. USPS Web Tools is dead. Direct USPS Labels needs EPS/CRID/MID per tenant with a 60 requests/hour quota, so use EasyPost, Shippo or ShipEngine (partner or reseller program).
5. AI output requires human curation and disclosure to satisfy Etsy Creativity Standards, and a USPTO Class 25 trademark check before publishing.
