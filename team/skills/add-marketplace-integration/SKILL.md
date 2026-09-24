---
name: add-marketplace-integration
description: Take a marketplace channel adapter (Etsy, Amazon SP-API, Shopify, TikTok Shop, Walmart) from pending or mock to live - docs-first, token refresh and rotation, verified webhooks with the real headers and dedupe windows, polling backstop, per-connection rate limiter, subscription re-check, health, mock and fixtures, sandbox run. Use when approval or sandbox keys arrive or a channel adapter changes.
---

# Add a marketplace integration

A live channel adapter that never loses an order, never double-pushes tracking, survives token rotation and
rate limits, and still has a working mock when the key is missing.

## When to use
- Replacing `pendingApprovalAdapter(...)` in `src/integrations/channels/{etsy,amazon,tiktok,walmart}/index.ts`
  with a live adapter once the app is approved or a sandbox exists.
- Changing the live Shopify adapter (`src/integrations/channels/shopify/{live,common,mock}.ts`).
- Owner: integrations-engineer (`src/integrations/**` except `ai`, and `src/api/webhooks.ts`). Module changes
  (`modules/channels`, `modules/orders`) are cards for backend-engineer.

## Steps
1. **Docs first.** Read the provider's current official docs (not memory). Put the doc URLs and the pinned API
   version at the top of the adapter file. Write down in the card: endpoints, scopes, token lifetimes, webhook
   topics, signature scheme, delivery-id header, retry window, rate limits and headers. Start from
   `channel-facts.md` (this folder) and research 10 §2–7, and re-check every [3P] or [U] fact.
2. **Implement `ChannelAdapter`** (`src/integrations/channels/types.ts`): `fetchOrders`, `pushTracking`,
   `setAvailability`, `verifyWebhook`, `parseWebhook`, `pendingApproval: false`. Adapters never touch the DB;
   credentials arrive decrypted in `ChannelConn.credentials`. Wire it in `getChannelAdapter()`
   (`channels/index.ts`) with live/mock selection like `shopifyAdapter(provider)`.
3. **Normalize at the edge** into `NormalizedOrder` (contracts). Rules the normalizer must keep:
   - per-line ship-by from the channel when it sends one (Etsy `transactions[].expected_ship_date`, Amazon
     `fulfillment.shipByWindow.latestDateTime`, Walmart `estimatedShipDate`);
   - null buyer contact is normal (Etsy `buyer_email`, Shopify without Level 2): `shipTo: null` must lead to
     an "address needed" hold, never an empty label;
   - line quantity from the current quantity after edits (Shopify `currentQuantity`, not `quantity`);
   - hold states: TikTok `ON_HOLD`, Amazon `PENDING`, buyer cancel requests never reach a gang sheet (R10);
   - store the raw payload in S3 (`rawPayloadKey`, 30-day purge), never pass it to services.
4. **Tokens (R1, R2).** On every refresh, store the new access **and** refresh token with the expiry,
   atomically, under a per-connection lock (Redis `SET NX` or a row lock `for("update")`) so two workers can't
   burn one refresh token. Refresh in a job before expiry. Expose the refresh-token expiry as connection
   health and alert the shop at 30, 7 and 1 days (a credential calendar job is backlog B-05, to be created).
   Never log or return tokens.
5. **Webhooks** in `src/api/webhooks.ts`, one route per channel:
   - verify the signature on the raw body in constant time **before** enqueueing (fixes S-28 for that
     channel); return 401 on a bad signature;
   - dedupe on the channel's real delivery-id header (table in `channel-facts.md`), persisted longer than the
     retry window (`webhook_deliveries`, to be created, B-07). Never fall back to `crypto.randomUUID()` for a
     real channel;
   - route by shop id only to a `connected` connection (S-04);
   - treat the webhook as a trigger: refetch the order by id, compare the channel's `updated_at` with what's
     stored, and ignore older payloads;
   - add a `noMockWebhooksInProd`-style guard (see `src/api/app.ts`) for every channel whose mock verifies
     with a constant.
6. **Polling backstop.** `fetchOrders` with a saved cursor, filtering on the channel's modified time only and
   deciding by status in code (Shopify's `financial_status:paid` filter drops partially refunded orders,
   research 10 §9 item 4). Both paths upsert by `(connection_id, channel_order_id)`. Spread polls with a
   stable delay per connection (`hash(connectionId) % interval`, research 11 §3.4).
7. **Rate limits (R7).** Use `takeToken(key, { capacity, perMs })` from
   `src/integrations/suppliers/ratelimit.ts`, keyed `<channel>:<connectionId>` (and the app key where the
   limit is per app). Feed it from the provider's headers. On 429: back off with jitter or wait for the
   replenish hint. Never a fixed tight loop.
8. **Tracking push (R8, R12).** Carrier codes from the channel's own list; per line and quantity
   (`TrackingPush.items`). Etsy `createReceiptShipment` emails the buyer on every call: push once, read back
   before any retry (`idempotent-side-effect`).
9. **Subscription re-check.** Shopify deletes API-created shop-scoped subscriptions after repeated failures
   within 24 h: re-list and recreate daily, or move to app-scoped `shopify.app.toml` subscriptions (B-06).
   Other channels: check the portal or API registration in the health job.
10. **Health.** Update `channel_connections.lastWebhookAt`, `lastPollAt`, `lastImportAt`, `lastError`,
    `lastErrorAt` so the `channels.health` procedure and the "sync broken 30+ minutes" alert are true.
11. **Mock and fixtures.** Keep or add a deterministic mock (pattern: `channels/shopify/mock.ts`). Record
    sandbox payloads, run `scrub-pii-fixture`, store under `src/integrations/channels/<channel>/fixtures/`,
    and replay them through parse → normalize → import: partial refund, split shipment, cancel after label,
    address change, multi-quantity, personalization, non-US characters, per-line cancel.
12. **Sandbox run** end to end with sandbox keys only: connect, webhook in, import, sheet, label (mock carrier
    is fine), tracking push, cancel. Record the steps in the report. Update the runbook's mock → real row with
    docs-writer: env vars, redirect URIs, scopes.

## Rules (MUST / MUST NOT)
- MUST NOT enqueue or parse an unverified body; MUST NOT use a production key when a sandbox exists.
- MUST NOT email or text Etsy buyers order, shipping or tracking info (Etsy API Terms).
- MUST NOT send marketplace data to model training (R15).
- MUST keep outbound HTTP to allowlisted hosts with a timeout, no blind redirects and a size cap (research 12
  §1.7).
- MUST map errors to `upstream()` / `rateLimited()` with a message a shop owner understands; raw errors in
  logs only, PII scrubbed.
- MUST keep the mock working with no key. App registrations and approvals go to the owner
  (`escalate-to-owner`).

## Done when
- Fixture replay tests, a bad-signature test (401, nothing enqueued), a duplicate-delivery test (one import),
  a stale-payload test and a rate-limit test pass.
- Token refresh is tested for rotation (new refresh token persisted) and the concurrent-refresh lock.
- The sandbox run passed with steps in the report; the mock still passes the API golden path.
- security-reviewer co-reviewed (webhooks, tokens, PII).

## References
- `channel-facts.md` (this folder)
- `invai-docs/research/10-marketplace-engineering-rules.md` §1 (R1–R16), §2–7, §9 items 1–12
- `invai-docs/research/12-security-quality-playbook.md` §1.7, §1.8, §2.1–2.3
- `invai-backend/src/integrations/channels/**`, `src/api/webhooks.ts`, `src/modules/channels/{sync,jobs}.ts`
- `invai-docs/waves/backlog.md` B-04–B-07, B-12, B-28
- Related: `idempotent-side-effect`, `provider-deprecation-watch`, `scrub-pii-fixture`,
  `marketplace-app-application`
