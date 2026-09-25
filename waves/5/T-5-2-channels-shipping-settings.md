# T-5-2: Channels and shipping settings

| Field | Value |
|---|---|
| Scope ref | `product/scope.md#mvp-in` items 2 and 7 |
| Backlog | B-85, B-90, B-67 (web: void confirm on the Shipping page) |
| Owner | web-engineer |
| Reviewer | reviewer; co-reviewer product-designer |
| Risk flags | ui |

## Owned paths
- invai-web `routes/_app/settings/{channels,shipping}.tsx`, `routes/_app/shipping.tsx` (the void confirm only; T-3-4's batch code stays)
- new `features/channels/**`
- own i18n keys
- tests

## Acceptance criteria
1. **Channels, OAuth return:** the page reads `?connected=shopify&connectionId=` and `?error=`, and shows a translated success or error.
2. **Channels, connection list:**
   - Import history from `channels.imports`: rows, created, updated, errors, and running or queued status from T-3-4.
   - Connection health from `channels.health`: degraded webhooks and token problems from T-3-1.
   - "Reconnect" for pending or error connections.
   - The stock-push opt-in toggle (T-3-3), with an explanation.
3. **Shipping settings:**
   - allowed carriers;
   - label format;
   - weight per style;
   - package presets, with translated labels (not the hard-coded "L (in)" or "Poly mailer");
   - the ship-from address;
   - the carrier provider shown as "Test mode" vs "Live".
4. **Shipping page:** void has a confirmation dialog. Per T-2-5's rejection rules (`shipping/service.ts:1145-1244`), the confirm copy must say: this voids the current label and can't be undone from here; the refund may show as "pending" rather than instant (`refund_pending` vs `voided`); it's blocked once tracking was already sent to the buyer's channel (direct them to cancel/refund on the channel instead); and it's blocked once the carrier has scanned the package (CSV channels especially — they stay voidable right up to the physical scan, not the push, per `NO_PUSH_CHANNELS`).
5. **Quality:** en and es, 390 px, keyboard accessible.

## Verification
- Typecheck, lint, test and build in web.
- Browser on a DB copy: the OAuth return states (use the mock Shopify connect), import history after a CSV import, the opt-in toggle, and saving shipping settings. Screenshots in en and es.
