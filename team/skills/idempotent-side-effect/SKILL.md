---
name: idempotent-side-effect
description: Make an outward side effect happen exactly once in effect - webhook intake, label buys (the EasyPost double-charge), payments, tracking pushes, floor scans, supplier orders - with a stored key, intent committed before the call, the call outside the DB transaction, read-back before retry, and a conflict on changed params. Use for "idempotency", "double charge", "duplicate", "retry safe".
---

# Idempotent side effect

Every call that costs money, emails a buyer, changes a marketplace or records a scan has a key, a stored first
result and a crash-safe retry, so a double click, a retry or a replay never repeats the effect.

## When to use
Owner rule 8: webhooks, payments, label purchases, tracking pushes and scans. Also supplier `POST /orders`,
Etsy `createReceiptShipment`, Shopify `fulfillmentCreate` with notify, Shopify inventory and refund mutations,
refunds and label voids. Use together with `idempotent-job` when the effect runs in a job.

## The known gaps (read before touching these areas)
- **Label buy can double-charge** (research 10 §9 item 13, backlog B-11). `buyLabel` in
  `src/modules/shipping/service.ts` takes `select ... for("update")`, calls `carrierAdapter().buy(...)`
  (EasyPost buy, then label PDF download and S3 upload) and inserts `labels`, **all inside one DB
  transaction**. If S3, the insert or a timeout fails after EasyPost charged, the transaction rolls back, the
  postage is paid but unrecorded, and a retry buys a **second** label. EasyPost documents no idempotency on
  `/buy`.
- **Tracking push runs inside the transaction too** (`pushTracking` in the same file calls
  `pushTrackingForShipment` under the row lock). For Etsy, each `createReceiptShipment` call **emails the
  buyer**, so a retry after a timeout sends a second email.
- **Webhook dedupe window is too short** (research 10 §9 items 7–8, B-07). `src/api/webhooks.ts` dedupes on
  the BullMQ `jobId` only (kept 24 h); Etsy retries for about 30 h. The generic route reads
  `x-etsy-delivery-id`, which Etsy doesn't send (it sends `webhook-id`), and enqueues **before** verifying the
  signature.
- **What's right today:** floor scans (`scans` unique `(company_id, client_scan_id)`, `storedResult()` in
  `src/modules/production/floor.ts` returns the first result verbatim) and inventory movements
  (`idempotency_key` in `modules/inventory/ledger.ts`). Copy these.

## Steps
1. **Pick the key.** It must identify the business intent, not the attempt:
   - scan: `clientScanId` from the tablet (never regenerated on retry);
   - label buy: our `shipmentId` (one live label per shipment);
   - tracking push: `shipmentId` plus the channel line set;
   - webhook: the channel's delivery id header (table in `patterns.md`);
   - Shopify inventory/refund mutation: a UUID stored per push, sent as `@idempotent(key: ...)`;
   - Stripe (when billing goes live): `event.id` for webhooks, an `Idempotency-Key` per charge intent.
2. **Store the first result.** A unique index on `(company_id, key)` and the result (or a pointer to it) on
   the row. A repeat returns the stored result. A repeat with **different parameters** under the same key is a
   `conflict()` (from `src/lib/errors.ts`), never a silent second effect (Stripe's model).
3. **Record intent, commit, then call** (research 10 R8). Use the three-transaction pattern in `patterns.md`:
   1. Tx 1: lock the row, check state, set an in-flight state (`buying`, `pushing`) with the attempt time,
      commit.
   2. No transaction: call the provider with a timeout.
   3. Tx 2: lock the row again, write the result and the provider's id (`carrierShipmentId`, `carrierLabelId`,
      fulfillment id), move state, `emit(...)` the outbox event, commit.
4. **On retry, read back before calling again.** If the row is in-flight or the call timed out: EasyPost `GET /shipments/{id}` and check `postage_label`; Etsy list the receipt's shipments; Shopify list fulfillments;
   S&S look up the PO. Only call again when the read-back proves nothing happened.
5. **Verify webhooks before any work**: raw body bytes, constant-time compare (`safeEqual`, `hmacHex` in
   `src/lib/crypto.ts`), reject stale timestamps where the provider signs them, then persist the delivery id
   and enqueue, then return 2xx within the provider's budget (Shopify 5 s, EasyPost 7 s, TikTok 3 s). Persist
   dedupe in a table `webhook_deliveries(channel, delivery_id)` with a unique key and a 7-day TTL (to be
   created, B-07), not only in BullMQ.
6. **Out-of-order safety:** store the channel's `updated_at` on the entity (`channelUpdatedAt`, to be created,
   B-12) and ignore payloads older than what is stored.
7. **Tests** (against `invai_test`, mocks for providers):
   - same key twice → one effect, same result;
   - same key, changed params → `CONFLICT`;
   - crash after the provider call but before Tx 2 (make the mock succeed, then throw in the persist step) →
     the retry reads back and does **not** call buy again (assert the mock's call count);
   - for webhooks: bad signature → 401 and nothing enqueued; duplicate delivery id → one import.

## Rules (MUST / MUST NOT)
- MUST NOT call a money-costing or buyer-emailing API inside a DB transaction or while holding a row lock.
- MUST NOT retry a POST that costs money or emails a buyer without a read-back first.
- MUST NOT enqueue or parse an unverified webhook body.
- MUST NOT let the client generate a new idempotency key on retry (floor: same `clientScanId`).
- MUST keep scans returning `ScanResult` for business outcomes, never throwing.
- MUST keep the mock providers deterministic so these tests run without keys.
- Risk flags: webhooks and payments need `security-reviewer` as co-reviewer.

## Done when
- The key, its unique index and the stored result are named in the report.
- The provider call happens outside any transaction, with intent committed first and read-back on retry.
- The four tests above (as applicable) pass, and the double-buy test asserts one provider call.
- Exercised for real: the action run twice (double click, curl twice, replayed webhook) with one effect seen
  in the DB.

## References
- `patterns.md` (this folder): the three-transaction pattern and webhook headers
- `invai-docs/research/10-marketplace-engineering-rules.md` R3–R5, R8, §8 EasyPost, §9 items 7–8, 13–14
- `invai-docs/research/12-security-quality-playbook.md` §1.8; `11-platform-scale-playbook.md` §3.1
- `invai-backend/src/modules/production/floor.ts` (scan replay), `src/modules/inventory/ledger.ts`
- Related: `idempotent-job`, `add-marketplace-integration`, `add-carrier-or-supplier-adapter`
