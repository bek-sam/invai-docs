# T-3-2: EasyPost live tracking

| Field | Value |
|---|---|
| Wave | 3 |
| Scope ref | `product/scope.md#mvp-in` item 7 |
| Backlog | B-66; T-2-5 follow-up (a sweep for stuck buy, void and push intents) |
| Owner | integrations-engineer |
| Reviewer | reviewer |
| Co-reviewers | security-reviewer |
| Risk flags | webhooks |
| Model | opus |

## Owned paths (edit)
- `invai-backend/src/integrations/carriers/**`
- New `invai-backend/src/api/webhooks-carriers.ts`, plus one mount line in `src/api/app.ts` (see wave.md: also extend the `noMockWebhooksInProd`-style guard to `/webhooks/easypost`, and mount it so it can't be shadowed by `/webhooks/:channel`)
- `invai-backend/src/modules/shipping/jobs.ts` (tracker handling and the sweep; `service.ts` is read-only except for calling existing functions)
- A schema file for carrier webhook dedupe (follow decision 0009 exactly — see wave.md for the `carrier_webhook_events` shape), and its migration
- One narrow, named line in `invai-backend/src/env.ts`: `EASYPOST_WEBHOOK_SECRET` (secret, optional) — that file is otherwise backend-foundation's; coordinate with this wave's T-3-4 owner before committing your hunk
- tests next to these files

## r1 review note (architect): the EasyPost HMAC doesn't exist yet
Checked `integrations/carriers/**` and `env.ts`: there is currently no webhook-signature verification code and no webhook secret for EasyPost anywhere in the codebase (unlike Shopify, which has `verifyShopifyHmac` in `shopify/common.ts`). Build the same pattern: `EASYPOST_WEBHOOK_SECRET` in `env.ts`, a `MOCK_EASYPOST_WEBHOOK_SECRET` dev constant, `easypostWebhookSecret()` fallback, and `verifyEasypostSignature(headers, body, secret)` doing `timingSafeEqual` over `HMAC-SHA256(secret, rawBody)`, checked against the `x-hmac-signature` header (EasyPost's format is `hmac-sha256-hex=<hex>`; compare the hex). Reject with 401 before anything is read or enqueued, same as the marketplace webhook route.
Also corrected: `markInTransit`/`markDelivered` are `(tx, ctx, shipmentId[, at])`, not `(shipmentId, at)` — `markInTransit` currently takes no `at` at all. Add one if you need the real carrier-scan time for out-of-order comparison (additive, default `new Date()`).

## Acceptance criteria
1. **Webhook route:**
   - `POST /webhooks/easypost` verifies the EasyPost HMAC signature first (401 otherwise) and dedupes on the event id.
   - `tracker.updated` maps to shipment states: `in_transit` on the first carrier scan (this also ships CSV-channel units, per T-2-5), `delivered`, `return_to_sender`/`failure` → exception.
   - Out-of-order events never move a state backwards.
2. **Tracker creation:**
   - Buying a live label creates or uses the EasyPost tracker.
   - A daily fallback poll refreshes shipments stuck in `labeled` for more than 3 days.
3. **Mock carrier:** its timer path keeps working (dev and E2E), and uses the same state function.
4. **Stuck intents:** a sweep job finds buy, void and push intents older than 15 minutes, retries them safely with the existing read-back logic, and raises an alert after N failures.
5. **Error mapping:** `carriers/easypost/index.ts:70` maps only rate-expiry codes to `rate_expired`, not `RATE_LIMITED`. Other carriers' rates are no longer dropped silently (they're filtered by allowed carriers).
6. **Tests:** fetch-mocked tests cover the signature, dedupe, state mapping, out-of-order events and the sweep.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build` with your test DB.
- For real: signed tracker events posted to your API move a shipment to `in_transit`, then `delivered`, and an older event is ignored.

## Out of scope
- USPS SCAN form and address verification (B-25).
