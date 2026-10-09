# Wave 29 plan review: product-manager (2026-10-09)

## Verdict: approve (no blocking edits)
All five cards are always-in-scope work in `product/scope.md` ("Always in scope": bugs, security, compliance deadlines, reliability). No scope-change request is needed and `scope.md` needs no change-log line. The wave has 5 cards, one owner each, and protects the wedge (orders, sheets, floor) without widening it.

## Decisions
1. **B-299: yes.** The seeded Desert Bloom follows the real two-step rule; exempt = `isSampleRow` only. Reason: the owner tests the feature on this login, and a rule the demo shop skips can rot unseen. Cost accepted: a dev DB older than 7 days blocks `owner@` until enrolled or `db:reset`. No seed bypass. Recorded as decision 0029 (accepted). T-29-2 AC 1 stands as written; its decision 0028 should link 0029.
2. **B-292: yes.** With auto-import off, a verified webhook for an unknown order is acknowledged and skipped (logged, no PII); updates and cancels for imported orders still apply; Sync now imports the skipped ones. Recorded as decision 0030 (accepted). T-29-4 stands as written; its "Depends on" is resolved.
3. **T-29-1 clocks: confirmed.** Personalization text (`order_items.personalization`, `item_artwork.values`), rendered art (`file_key`, `preview_key`) and the five notes (`orders.buyer_note`, `hold_note`, `cancel_note`, `refund_events.note`, `reprints.note`) go on the 30-day-after-delivery clock and into `redactOrders` (18 months, Shopify redact, Amazon path). Compliance already answered yes (T-28-3 compliance r1). A reprint after the purge asks the office to re-enter the text (AC 4). No column moved. Enum reasons, money and station/vendor machine notes stay, as AC 2 says.

## Blocking items
None.

## Optional notes (none gate the wave)
- T-29-1 / decision 0027: refund notes were kept as a hedge in decision 0026 (OI-19). State in 0027 that this narrows that keep-list item (0026 body untouched) and add it to the OI-19 text so counsel sees it.
- T-29-1 AC 1: a cancelled order is never "delivered". Report which date starts the 30 days for cancelled orders (suggest the cancel date, as `purgeBuyerPii` uses today) so `cancel_note` and `hold_note` on them are covered.
- T-29-1 out of scope: sheet PNG/PDF files that already hold rendered text. Fine for now, but the report must add the backlog line the card promises; I rank it P1 with B-293 (same buyer text).
- T-29-2 AC 5: the runbook/demo-guide line for a stale dev DB goes to docs-writer; list it as a follow-up (no card in this wave).
- T-29-4: a web hint on the connection ("Auto-import is off: new orders wait for Sync now") is a good later UI item; one-shop evidence only, no spec yet.
- T-29-3 (assistant is MVP-in item 13) and T-29-5 (team reliability) scope refs are fine.
