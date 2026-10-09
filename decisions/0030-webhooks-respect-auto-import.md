# 0030: While a connection's auto-import is off, webhooks do not create new orders

- Status: accepted (2026-10-09)
- Type: product

## Context
A shop that turns auto-import off on a channel connection is saying "do not bring new orders in on your own". Poll-started syncs already respect it (T-28-5), but `channels/sync.ts` `handleWebhook` still created orders for new-order webhooks, so shops got surprise orders. Cancels and updates are different: an order already imported must stay correct, and a missed cancel can cause a wrong print. Links: backlog B-292, card T-29-4, `waves/28/reviews/plan-architect.md` item 15. Decided by product-manager.

## Decision
With `autoImport === false` on the connection:
1. A verified webhook for an order we do not have is acknowledged (2xx) and skipped, with a log line holding no PII.
2. Updates and cancels for orders already imported still apply as today.
3. A manual "Sync now" imports the skipped orders; none are lost. Turning auto-import back on imports them on the next webhook or poll, once.
4. `autoImport` on or unset is unchanged. Signature checks and dedupe are untouched.

## Consequences
- Shops that pause auto-import stop getting orders they did not ask for, and never lose one.
- A shop that forgets it paused import sees orders arrive late; a web hint on the connection is a later UI item, not part of T-29-4.
