# Idempotent side-effect patterns

## 1. Three-transaction pattern (label buy, tracking push, supplier order)

The target shape for `buyLabel` (backlog B-11). Names like `buying` and `buyStartedAt` are proposals; the shipment state list is `SHIPMENT_STATES` in `src/db/schema/shipping.ts` and in contracts `states.ts`, so a new state is a contract change (`add-contract-procedure`) and a migration.

```ts
export async function buyLabel(companyId: string, ctx: TenantContext, input: BuyInput) {
  // Tx 1: decide and record intent.
  const plan = await withTenant(companyId, async (tx) => {
    const [s] = await tx.select().from(shipments).where(eq(shipments.id, input.shipmentId)).for("update");
    if (!s) throw notFound("shipment", input.shipmentId);
    if (LIVE_LABEL.includes(s.status)) return { done: true as const };          // stored result
    if (s.status === "buying") return { resume: true as const, s };              // crashed earlier
    if (s.pendingRateId && s.pendingRateId !== input.rateId) throw conflict("A different rate is being bought");
    await tx.update(shipments).set({ status: "buying", pendingRateId: input.rateId, buyStartedAt: new Date() })
      .where(eq(shipments.id, s.id));
    return { s };
  });
  if ("done" in plan) return withTenant(companyId, (tx) => getShipment(tx, ctx, input.shipmentId));

  // No transaction: read back first when resuming, then buy.
  let label = plan.resume ? await carrierAdapter().lookup?.(plan.s.carrierShipmentId) : null; // lookup: to be created
  if (!label) label = await carrierAdapter().buy(buyRequest(plan.s, input));                  // has its own timeout

  // Tx 2: persist the result.
  return withTenant(companyId, async (tx) => {
    const [s] = await tx.select().from(shipments).where(eq(shipments.id, input.shipmentId)).for("update");
    if (s && LIVE_LABEL.includes(s.status)) return getShipment(tx, ctx, s.id);   // another worker finished it
    await tx.insert(labels).values({ /* ... */ }).onConflictDoNothing();         // needs a unique key, see note
    await tx.update(shipments).set({ status: "labeled" /* ... */ }).where(eq(shipments.id, input.shipmentId));
    await emit(tx, companyId, "shipment.labeled", { /* ids only */ });
    return getShipment(tx, ctx, input.shipmentId);
  });
}
```

Notes:
- `labels` today has only non-unique indexes on `(company_id, shipment_id)` and `(company_id, tracking_code)`; `shipments` has a unique `(company_id, tracking_code)`. A void-then-rebuy keeps old label rows, so the guard is a partial unique index such as `(company_id, shipment_id) where status = 'purchased'` (to be created, via `add-tenant-table` / `zero-downtime-migration`), or the carrier's label id.
- The label PDF download and S3 upload happen after the buy and before Tx 2; they are retryable because the S3 key is deterministic (`objectKey` with a fixed id) and EasyPost keeps the label URL.
- A `buying` row older than N minutes with no label is surfaced to a person (an alert through `raiseAlert` in `modules/today`), never auto-bought again.
- The same shape fits tracking push (`pushing` → pushed, read back with the channel's list-shipments/fulfillments call) and S&S `POST /v2/orders` (send `rejectLineErrors: true`; read back the PO before retrying).

## 2. Webhook intake

```
POST /webhooks/<channel>
  raw = await c.req.text()                 // raw bytes before any JSON parse
  verify(raw, headers) or 401              // constant time; timestamp tolerance where signed
  id = header(<delivery-id header>)        // table below; never crypto.randomUUID() for a real channel
  insert webhook_deliveries(channel, id) on conflict do nothing   // to be created; 7-day TTL purge
  if inserted: enqueue job (jobId = webhook-<channel>-<id>)
  return 2xx fast
job: route by shop id to a `connected` connection only (S-04), refetch the resource, compare channel updated_at, upsert
```

| Channel | Signature | Delivery id to dedupe on | Retry window |
|---|---|---|---|
| Shopify | `X-Shopify-Hmac-SHA256` (base64 HMAC of raw body) | `X-Shopify-Webhook-Id` (`X-Shopify-Event-Id` groups one merchant action) | 8 retries in 4 h |
| Etsy | Standard Webhooks: `webhook-signature` may hold several space-separated `v1,<b64>`; key = base64-decode(secret minus `whsec_`); signed `webhook-id.webhook-timestamp.body`; reject > 5 min skew | `webhook-id` | about 30 h |
| Amazon | SQS / EventBridge notifications (no HTTP signature to us) | `NotificationId` | duplicates expected |
| TikTok Shop [3P] | `Authorization` = hex HMAC-SHA256(secret, app_key + body), no timestamp | `tts_notification_id` | about 15 h |
| Walmart [U] | BASIC, HMAC or OAUTH destination auth | `eventId` | about 3 retries |
| EasyPost | `X-Hmac-Signature: hmac-sha256-hex=<hex>`; secret NFKD-normalized, UTF-8 | event `id` | 6 retries; failing endpoints auto-disabled |
| Stripe | `stripe.webhooks.constructEvent(raw, sig, secret)`, 5-min tolerance | `event.id` | refetch the object before changing `companies.plan` |

Source: `invai-docs/research/10-marketplace-engineering-rules.md` §2, §3, §8; `12-security-quality-playbook.md` §1.8. [3P] and [U] facts must be confirmed against the provider's docs before depending on them.

## 3. Floor scan (already correct; keep it)

- The tablet creates `clientScanId` once, stores the command in the Dexie outbox (`invai-floor/src/outbox/outbox.ts`), and replays with the same id.
- The server checks `storedResult(tx, clientScanId)` before and after the work, and inserts with `onConflictDoNothing()` on `(company_id, client_scan_id)`; a raced duplicate returns the stored result.
