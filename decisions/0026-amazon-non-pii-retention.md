# 0026: Amazon non-PII data older than 18 months is cleared daily; bookkeeping records stay

- Status: accepted (2026-10-09) (security and compliance)
- Type: security

## Context
Amazon's Data Protection Policy (update effective 2025-11-25) says non-PII Amazon data "must not be stored for longer than 18 months, unless longer retention is legally required" (`security/v1-review.md`, DPP table; backlog B-187). Buyer PII on orders older than 18 months is already removed daily by `redactStaleBuyerPii` (`modules/privacy/service.ts`, T-12-4), and the 30-day PII purge (S-16) runs before that. Nothing cleared the non-PII rest. US sellers must keep sales and expense records for years (IRS: at least 3, often 7), so the money, dates and order numbers of an order are the "legally required" exception: profit for a past month must still add up. Card T-28-3; plan reviews `waves/28/reviews/plan-architect.md` items 12–14 and `plan-pm.md` item 5; drafted by backend-engineer (privacy), reviewers named above. Calls marked **OI-19** go to counsel with the other legal drafts; until counsel answers, they are kept.

## Decision
**Which data is Amazon data.** An order is an Amazon order when `orders.channel = 'amazon'` (SP-API or an Amazon CSV connection) or its last import run used the `amazon` CSV format (an Amazon file uploaded to a generic CSV connection). Company-level Amazon data: `import_runs` of an Amazon connection or the `amazon` format, `listings` with `channel = 'amazon'`, and `market_price_snapshots` from `amazon_pricing` or `amazon_brand_analytics`.

**When.** The cutoff is the module's existing month rule, `buyerPiiCutoff(now)` (`setUTCMonth(-18)`). Orders: `placed_at < cutoff` **and** status `shipped`, `delivered` or `cancelled` (`invai-contracts/src/states.ts`). Open orders of any age are never touched. Import runs: `started_at < cutoff` and status `completed` or `failed`. Listings: `coalesce(last_synced_at, updated_at) < cutoff`. Price snapshots: `as_of < cutoff`. No order, item or shipment row is ever deleted.

| Table | Keep (bookkeeping record or InvAI's own record) | Drop (value after the sweep) |
|---|---|---|
| `orders` | id, company, connection, channel, `channel_order_id` and `order_no` (the order number on the shop's books), status, all `*_cents`, currency, item count, `placed_at`, `ship_by`, `shipped_at`, `delivered_at`, `cancelled_at`, cancel/hold reason and staff notes, tags, pack override, bin, `import_run_id`, `channel_updated_at` (guards against stale payloads), `created_at`/`updated_at` | `shipping_method` (Amazon ship service level) → `NULL`. PII columns `buyer_note`, `buyer_ref`, `raw_payload_key` (+ the S3 raw payload) → `NULL` by `redactStaleBuyerPii`, same cutoff, runs first in the same job |
| `order_items` | ids, line/unit numbers, `channel_line_id` (Amazon order-item code: the settlement report's reconciliation key), `channel_sku` (the seller's own SKU), `unit_price_cents`, state, design/product/blank links, print size, artwork keys, flags, reprint fields, production pointers; `title`, `variant_title` (the line description on the sales record: **OI-19**) | `channel_listing_id` (ASIN) → `NULL`. Personalization answers → `NULL` by the PII sweep |
| `buyer_pii` | none | row deleted by the PII sweep (30-day purge already ran) |
| `shipments` | everything the shop bought from its carrier: postage, label fee, carrier, service, tracking code/URL/status, label key, package size, dates, push status | `tracking_push_error` (channel API response text) → `NULL` |
| `address_verifications` | none | row deleted (a hash of the Amazon ship-to plus carrier text; no bookkeeping value) |
| `profit_lines`, `refund_events` | everything: money, fees, dates, refund note (refund reason on the books: **OI-19**) | none |
| `import_runs` (Amazon) | id, connection, format, status, counts, dates | `errors` → `'[]'`; `file_key` → `''` (the CSV object itself expires on the S3 lifecycle) |
| `listings` (Amazon) | id, listing id, title, state, url, links (the shop's own catalog) | `raw` → `'{}'` |
| `market_price_snapshots` (Amazon sources) | none | row deleted |
| `order_item_transitions`, `scans`, `transfers`, `gang_sheets`, `bins`, `reprints`, `inventory_movements` | InvAI's own production and stock records (ids, states, times); no Amazon content beyond ids | none |
| `item_artwork` | ids, item link, state, times | PII, not cleared today: `values`, `file_key`, `preview_key` hold the buyer's personalization answers and art rendered with that text. To be cleared by the PII sweep; open gap S-56 (backlog B-293), not part of this sweep |
| `labels` | tracking number and label key (the shop's carrier record, kept) | none; the label PDF itself is removed by the 30-day S3 rule |
| `audit_log` | kept (append-only; DPP asks 12 months of logs; log retention is B-75) | none |
| `webhook_deliveries`, `outbox_events`, BullMQ job data | already purged on their own short windows (7 days; relay cleanup; queue age) | none here |

**Placeholders for NOT NULL drop columns** are the column defaults: `''` for `import_runs.file_key`, `'[]'` for `import_runs.errors`, `'{}'` for `listings.raw`. Swept rows keep their `updated_at`.

**How.** `sweepStaleAmazonData(now, { dryRun })` in `modules/privacy/service.ts`, called by the daily `privacy.retentionSweep` job after `redactStaleBuyerPii`. Company ids are read with `withSystem` (ids only); every change runs per company in `withTenant`, at most 500 orders (plus 500 import runs, listings and snapshots) per transaction, looping until nothing matches. Each batch selects only rows that still hold drop data, so a second run changes nothing. A failing company is logged and skipped; the rest continue. Each batch writes one `privacy.amazon_retention` audit row with counts only. A dry run returns the same counts and writes nothing.

## Consequences
- Profit, refunds, fees and order numbers for old Amazon orders stay exactly as they were; old orders lose their ASIN, ship service level, address-check row and channel error text.
- A refund that arrives for an order older than 18 months is still matched by line (`channel_line_id` is kept).
- Re-importing an old Amazon file brings the dropped values back until the next nightly run.
- Enforced by `src/modules/privacy/amazon-retention.test.ts` (fences: other channels, younger orders, open orders, keep columns, profit total, idempotency, dry run). Any new column that stores Amazon data must be added to this table and to the sweep (owner: the module adding it; reviewer checks it).
- OI-19 rows (item titles, refund notes) are revisited when counsel answers; dropping them later is a one-line change.
