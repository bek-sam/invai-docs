# Review: T-28-3 Amazon 18-month retention, compliance co-review r1
Reviewer: compliance-officer. Inputs: decision 0026 (after security r2), security r1/r2, DPP table in security/v1-review.md. Code not re-run (read-only); control facts taken from security r1/r2 and the dd4907e stat.

## Verdict: approve (0026 set to accepted 2026-10-09)

## Keep list: defensible under "unless longer retention is legally required"
- Money (`*_cents`), currency, dates, `order_no`, `channel_order_id`, `channel_line_id`, `unit_price_cents`, `profit_lines`, fees, refund amounts: US sales/expense records (IRS 3 to 7 years); the line code is the settlement reconciliation key. Yes.
- `channel_sku`: the seller's own product code. Yes.
- Carrier postage, label fee, tracking number: the shop's own purchase from its carrier (an expense record). Yes.
- Production, scan, state and stock rows: InvAI/shop records, ids only. Yes.
- `audit_log`: DPP wants 12 months of logs. Yes.
- `title` / `variant_title`, refund notes: a hedge (line description on a sales record), not strictly required by tax rules. Marked OI-19; fine until counsel answers, dropping is a one-line change.

## Drop list: nothing a shop legally needs
ASIN, ship service level, push error text, address-check hash, import-run errors/file keys, listing raw JSON, Amazon price snapshots are not tax records. Order number, line code, seller SKU and amounts stay. OK.

## Findings (non-blocking)
1. Staff notes, cancel/hold reasons and refund notes are free text typed by staff and may hold a buyer's name or address. Backend (privacy) should confirm the PII redaction covers them, or the keep call is wrong for that text. Do it with B-293 (due 2026-11-08).
2. Counsel should look at 0026 once. Tech lead: add "0026 keep list (titles, refund and staff notes, tracking)" to OI-19; no new inbox entry.
3. DPP 18-month row stays Partial until B-293 lands and counsel answers; do not mark it closed in the evidence pack.

## Answer to security's question: does personalization text fall under the 30-day PII purge?
Yes, treat it as buyer PII and purge within 30 days of delivery. (a) Buyer-supplied customization text routinely carries names, gift messages and addresses, so it is buyer-identifying Amazon data. (b) Even if a string were not PII, it is Amazon data and could never exceed 18 months, so keeping it forever is non-compliant either way. (c) When unsure, take the strictest clock. Scope for B-293: `item_artwork.values`, plus S3 `file_key` and `preview_key` (art rendered with that text); the `order_items` copy is already redacted. The 30 days run from delivery, so the reprint window stays open. Apply the same rule to Etsy and Shopify for consistency.
