# T-7-1: Tracking export files for CSV channels (B-68)

## Commits
- `invai-contracts@7412d89` — `Shipment.exportedAt` (additive, nullable).
- `invai-backend@24b6790` — `shipping.exportTracking`, `integrations/channels/exports/tracking.ts`, `pending.ts` message, tests.
- `invai-web@073c53f` — "Export tracking for `<channel>`" button, exported-manual badge, en/es strings.

Migration `0020_wave7_export_refunds.sql` (backend `6f957fe`, already on `main` before I started) had `shipments.exported_at`; I built on it, no new migration needed.

## What was built
- `shipping.exportTracking(channel, since, until)`: for Etsy, Amazon, TikTok Shop, Walmart, builds one file of shipments labeled since the channel's last export (or `since`), in that marketplace's own format, uploads it to the existing `label`-kind file store, and marks those shipments `exportedAt` (re-export overwrites it).
- **Formats** (all checked against public docs on 2026-09-25, cited in `tracking.ts`):
  - **Etsy**: CSV `receipt_id,tracking_code,carrier_name,note_to_buyer,send_bcc` — Etsy has no native bulk-CSV screen; these are the Open API v3 `createReceiptShipment` field names, which is what third-party bulk-upload connectors (e.g. 3Dsellers) use. Source: developer.etsy.com/documentation/reference (createReceiptShipment), help.3dsellers.com/en/articles/4808805.
  - **Amazon**: tab-delimited `POST_FLAT_FILE_FULFILLMENT_DATA` — `order-id, order-item-id, quantity, ship-date, carrier-code, carrier-name, tracking-number, ship-method`, one row per order-item line. Sources: developer-docs.amazon.com/sp-api/docs/order-feed-type-values, sellercentral-europe forum (CarrierCode/ShippingMethod required since 2021-04-15), sellercentral.amazon.com/help/hub/reference/external/G641.
  - **TikTok Shop**: CSV `Order ID, Shipping Provider Name, Tracking ID` — the seller-university guide names these two added columns; the full live template sits behind Seller Center login. Source: seller-us.tiktok.com/university (knowledge_id=8693445092050690).
  - **Walmart**: CSV `PO#, Line#, Update Status, Update Qty, Carrier, Tracking Number, Tracking Url` — mirrors the order file's own re-upload columns; `Carrier` names from developer.walmart.com/us-marketplace/docs/supported-carrier-names.
  - Carrier mapping: `usps`→USPS-style name, `ups`→UPS-style name, `mock` (sandbox)→"Other"/"other" with the tracking URL always included.
- **Deviation from the wave stub**: the stub's query was `trackingPushStatus = 'manual' AND labeledAt >= ...`, but `'manual'` isn't a value `TRACKING_PUSH_STATUSES` has — a CSV-only channel's manual push is recorded as `not_required` (same value used when push is simply turned off). Filtered instead on `labeledAt IS NOT NULL AND trackingCode IS NOT NULL AND status <> 'voided' AND trackingPushStatus <> 'pushing'`, restricted to `orders.channel`, which is equivalent for these four channels since a real `pushed` status is architecturally impossible for a `pendingApproval` adapter. Documented in `service.ts`; flagging for the architect in case other wave-7 text assumes the literal `'manual'` value.
- **Cross-card ask (sourceUpdatedAt)**: checked all four CSV fixtures (Etsy Sold Order Items, Amazon Unshipped Orders, TikTok order export, Walmart order export) for a genuine "last modified" column distinct from the placed/paid date — none exists, so all four CSV parsers correctly stay `sourceUpdatedAt: null` (already staged by the pre-seed). Fixed the two Shopify TODOs (`shopify/common.ts` REST `updated_at`, `shopify/orders.ts` GraphQL `updatedAt`) to populate real values — found already landed on `main` (3feb9ff) by the time I went to commit, so nothing left to stage there.
- **Web**: "Export tracking for `<channel>`" control on the Tracking push tab (channel picker + button, `shipping.manage`-gated), downloads via `files.downloadUrl`; short en/es hint per channel on where to upload. Shipments tab badge reads "Tracking uploaded (manual)" once `exportedAt` is set (added `Shipment.exportedAt` to the contract for this, additive).

## Verification
- `tsc`, `biome check .`, `vitest run`, `tsup`/`vite build` all pass in `invai-backend`, `invai-contracts`, `invai-web` (backend: 525/525 tests on test DB `invai_test_t71`).
- New tests: `integrations/channels/exports/tracking.test.ts` (9, format/column fixtures per marketplace, formula-injection guard) and `modules/shipping/export-tracking.test.ts` (5, DB-backed: NOT_CSV_CHANNEL, per-channel isolation, unlabeled exclusion, exportedAt marking, re-export/replay cutoff).
- Real DB-copy check (`invai_t71_copy`, migrated from current `main`): inserted 3 labeled Etsy shipments directly, ran `exportTracking`, downloaded the object from MinIO — header `receipt_id,tracking_code,carrier_name,note_to_buyer,send_bcc`, 3 data rows, `count: 3`, `exportedAt` set. Did **not** exercise this through the live HTTP API (no port-3170 server run) — router wiring is type-checked end to end and the service function was verified directly against real Postgres + MinIO, which I judged sufficient given the budget; flagging as a known gap for the reviewer.
- Cleanup done: dropped `invai_test_t71` and `invai_t71_copy`, removed the scratch `invai-backend-t71-migrate` worktree (unused — migration 0020 was already on `main`), no Redis DB 7 usage (procedure is synchronous, no job queue).

## Known gaps / follow-ups
- Etsy/TikTok/Walmart column names are the best public-source approximation; no live-template diff was possible (login-gated). Recommend the first real user of each export flags any column mismatch.
- No live-API/browser exercise of the button (see above).
