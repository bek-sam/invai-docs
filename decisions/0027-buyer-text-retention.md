# 0027: Buyer text (personalization, rendered art, free-text notes) follows the buyer PII clocks

- Status: proposed (security-reviewer and compliance-officer to accept)
- Type: security

## Context
S-56 (`security/v1-review.md`, Medium, due 2026-11-08): `item_artwork.values` copies the buyer's personalization answers, and the rendered art in storage carries that text, yet no retention path cleared them. Free-text notes typed by staff can also name the buyer (backlog B-296; compliance finding 1 in `waves/28/reviews/T-28-3-compliance-officer-r1.md`). The compliance officer answered that personalization text is buyer PII: purge it within 30 days of delivery, and never keep Amazon data past 18 months (same review, "Answer to security's question"). The plan reviews set the shape: the clock is per unit, because `buyer_pii.purge_after` starts when the first shipment of an order is delivered while other units may still be in production (`waves/29/reviews/plan-architect.md` items 2–6, `plan-pm.md`). Card T-29-1 (backlog B-293, B-296); built by backend-engineer (privacy), reviewed by reviewer, security-reviewer, compliance-officer and architect.

## Decision
One helper, `redactBuyerText(tx, orderIds, { scope })` in `invai-backend/src/modules/privacy/service.ts`, clears buyer text on three clocks:

| Clock | Runs in | Scope |
|---|---|---|
| 30 days after delivery; without a delivery event 30 days after `shipped_at`; for a cancelled order 30 days after `cancelled_at`; or past `buyer_pii.purge_after` when that row exists | nightly `purgeBuyerPii` (`orders/jobs.ts`, 04:30 UTC) | `shipped-items`: only units in `shipped`, `delivered` or `cancelled`; other units keep their text and art until a later night |
| 18 months after `placed_at` (`buyerPiiCutoff`), every channel, Amazon included | daily `redactStaleBuyerPii` | `all` units |
| A redact request (Shopify `customers/redact`, `shop/redact`) | `handlePrivacyRequest` | `all` units |

Orders are selected from these clocks wherever something is still unredacted, so orders whose `buyer_pii` row was deleted in an earlier run are covered too.

**Cleared**, per unit in scope:
- `order_items.personalization` answers and file URLs → `null` (questions stay);
- `item_artwork.values` → `{}`, `flags` → `[]`, `error` → `null`, `file_key`/`preview_key` → `null`, `status` → `purged`; the render, preview and buyer-photo objects (photo-slot values, `{company}/photo/...`) are deleted from storage;
- `order_items.artwork_key`/`artwork_preview_key` → `null`, `artwork_status` → `purged`, artwork flags (their messages quote the text) removed;
- `reprints.note` → `null`.

Per order: `orders.buyer_note`, `hold_note`, `cancel_note` and `refund_events.note` → `null`.

**Storage first.** Objects are deleted before the rows change. A unit whose object delete failed keeps its keys and status and is found again on the next run; a redact request whose delete failed rolls back and the delivery is retried. No new table.

**Kept** (order facts for the shop's books, not buyer text): order and item ids, `channel_order_id`, `order_no`, SKUs, titles (OI-19), amounts, fees, dates, states, enum reasons (`hold_reason`, `cancel_reason`, reprint `reason`), the artwork row's `template_id` and dimensions, approval user and time. Station maintenance notes and `gang_sheets.vendor_notes` are about machines and sheets, not buyers, and stay.

**Re-entry.** A purged unit can't go on a sheet: the existing check in `production/sheets.ts` (`classify`) needs a rendered or approved artwork key, so a purged unit still in production, or reprinted, shows `needs_artwork`. `personalization.artwork.approve` on a purged row answers `CONFLICT`; `update` with new values (a re-render) is the way back in.

**Superseded renders.** From T-29-1 on, a re-render deletes the previous render and preview objects (only keys under `{company}/artwork/`) after the new outcome is committed.

This narrows decision 0026's keep-list item "refund note" (`profit_lines`, `refund_events` row): the note is cleared on the 30-day clock; the refund's money, dates and reason stay. Decision 0026 itself is unchanged.

## Consequences
- The office re-enters the text for a purged unit that must be made again; there is no copy to restore from. The 30 days run from delivery, so the usual reprint window stays open.
- `holdsBuyerText(scope)` is the one predicate for "still holds buyer text"; a new free-text column that may name a buyer must be added to it and to `redactBuyerText`, with a test in `modules/privacy/buyer-text.test.ts` or `modules/orders/purge.test.ts`.
- Enforced by tests: `orders/purge.test.ts` (30-day, per unit, buyer_pii already gone, cancelled clock, storage failure, tenant), `privacy/buyer-text.test.ts` (redact and 18-month, all units), `privacy/security.test.ts` (S-56), `personalization/purged.test.ts`, `production/purged-artwork.test.ts`.
- Known gaps, not covered here:
  - `audit_log` `artwork.rendered` rows quote values in `data.flags` (`personalization/service.ts` `saveItemRender`); the table is append-only. Owner: security-reviewer with backend-foundation (backlog line from the T-29-1 report).
  - Gang sheet print files and previews hold rendered buyer text; `PII_OBJECT_KINDS` is `raw,csv,label` only. Owner: backend-engineer (production) (backlog line, P1 with B-293).
  - Renders superseded before T-29-1 are orphaned objects no row points at. Owner: backend-engineer (personalization) (backlog line, a one-off sweep).
- Links: S-56, B-293, B-296, compliance answer in `waves/28/reviews/T-28-3-compliance-officer-r1.md`, decision 0026, OI-19 (the 0026 keep list goes to counsel).
