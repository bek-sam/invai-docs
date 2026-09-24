---
name: add-carrier-or-supplier-adapter
description: Add or change a carrier adapter (EasyPost, a future Amazon Buy Shipping or UPS) or a blank supplier adapter (S&S Activewear, SanMar PromoStandards) in invai-backend/src/integrations - interface, mock, crash-safe buy, rate limit, timeouts, refunds, address checks, fixtures and a sandbox run. Use for "carrier", "label", "EasyPost", "supplier", "S&S", "SanMar", "purchase order to supplier".
---

# Add a carrier or supplier adapter

A carrier or supplier adapter that normalizes to our types, never buys or orders twice, respects the
provider's limits, and keeps a deterministic mock for keyless runs.

## When to use
- A new carrier (Amazon Buy Shipping for OTDR protection, research 10 §4, is backlog) or supplier (SanMar for
  Bella+Canvas, backlog B-36).
- Changing `src/integrations/carriers/easypost/index.ts` or
  `src/integrations/suppliers/ssactivewear/index.ts`.
- Owner: integrations-engineer. The shipping and inventory services that call you belong to backend-engineer.

## Steps
1. **Docs first.** Put the official doc URL and API version at the top of the file (as `easypost/index.ts`
   does). List endpoints, auth, limits, error shapes, test mode. Re-check research 10 §8 facts against the
   docs.
2. **Implement the interface:**
   - carriers: `CarrierAdapter` in `src/integrations/carriers/types.ts` (`rate`, `buy`, `void`), errors as
     `CarrierError(provider, "address_invalid" | "rate_expired" | "upstream", msg)`, money in cents,
     dimensions in inches and ounces;
   - suppliers: `SupplierAdapter` in `src/integrations/suppliers/types.ts` (`stock`, `products`,
     `placeOrder`), errors as `SupplierError(msg, status)`. Adapters never touch the DB; credentials are
     passed in.
   - Selection: `carrierAdapter()` in `carriers/index.ts` (mock when `env.mocks.carrier`),
     `getSupplierAdapter()` in `suppliers/index.ts` (company credentials first, then env keys, else mock). A
     new provider adds its key to `src/env.ts` `mocks` through backend-foundation.
3. **Crash-safe buy and order (R8).** The adapter must support read-back so the service can retry safely
   (`idempotent-side-effect`):
   - carrier: expose a lookup by our reference or the carrier shipment id (EasyPost `GET /shipments/{id}`,
     check `postage_label`) (to be created). EasyPost has no documented idempotency on `/buy`.
   - supplier: send our PO number, set S&S `rejectLineErrors: true` so a partial acceptance doesn't silently
     drop lines (not sent today, research 10 §9 item 29), and support looking the PO up before any retry. Use
     `testOrder` (`SupplierOrderInput.test`) in sandbox runs.
4. **Rate limits and 429.** `takeToken(key, { capacity, perMs })` from `suppliers/ratelimit.ts`, keyed per
   account (S&S uses `ssactivewear:${account}`, 60/min). On 429: S&S → wait 60 s (no documented hint);
   EasyPost → exponential backoff with jitter (no `Retry-After`; index endpoints 5 rps). Never hot-loop.
5. **Timeouts and outbound safety.** `AbortSignal.timeout(...)` on every fetch (EasyPost 30 s, S&S 20 s
   today). URLs taken from responses (EasyPost `label_pdf_url`) are fetched only from an allowlisted host,
   with `redirect: "manual"` and a size cap; `easypost/index.ts:145` follows any redirect with no cap today
   (research 12 G8).
6. **Carrier specifics:**
   - Parcel length, width and height are required on USPS commercial manifests since 2026-07-12; never send 0
     (EasyPost rejects zeros since 2025-09-27). Check fallbacks and presets.
   - Refunds are async: `submitted` means pending until `refund.successful`; label status `refund_pending`
     exists in `LABEL_STATUSES`. USPS refunds within 30 days and before any scan; UPS/FedEx 90.
   - Consume EasyPost webhooks (`tracker.updated` for delivered, `refund.successful`, `scan_form.*`,
     `shipment.invoice.updated`) through a verified route (`X-Hmac-Signature`, NFKD secret), backlog B-11.
   - Address `verify` (non-blocking, `verifications.delivery`) at rate time (B-25).
   - A rate must not be bought across a USPS price-change midnight (Central); profit uses the bought label's
     cost, never a cached rate (peak surcharges run Oct 4 2026 – Jan 17 2027 USPS, Sep 27 2026 – Jan 16 2027
     UPS).
   - Daily USPS SCAN form (`scan_form`) so marketplace dispatch clocks count at manifest time (R11, B-25).
7. **Supplier specifics:** one blank SKU may have several suppliers (Bella+Canvas moved to SanMar on
   2026-06-29; S&S sells it only until stock runs out). SanMar is SOAP PromoStandards (`ws.sanmar.com:8080`,
   UAT `uat-ws.sanmar.com`); `suppliers/sanmar/index.ts` is an empty stub. S&S invoices are PDF only, so
   landed cost comes from the order response.
8. **Mock.** Keep it deterministic and schema-valid: `carriers/mock/index.ts` (labels via imaging `POST /labels/mock`), `suppliers/mock/index.ts`. Add mock behavior for every new method, including read-back and
   refund pending.
9. **Fixtures and tests.** Record sandbox responses, `scrub-pii-fixture` them (addresses are PII), and test:
   normalization to cents and inches, 429 handling, timeout mapped to `upstream`, error mapping, and the
   double-buy/double-order test (mock succeeds, persist fails, retry does not call buy again).
10. **Sandbox run** with test keys only (EasyPost test labels are free; S&S `testOrder`). Record the steps and
    update the runbook's mock → real row (env vars) with docs-writer.

## Rules (MUST / MUST NOT)
- MUST NOT call buy or place-order without a stored intent and a read-back path.
- MUST NOT use production keys when a test mode exists; real keys are the owner's (`escalate-to-owner`).
- MUST store carrier API keys encrypted (`encryptJson` in `src/lib/crypto.ts`); EasyPost referral-customer
  keys are returned only once, at creation.
- MUST keep addresses out of logs; label PDFs are PII (`label` kind, served as attachments, short presigned
  GETs).
- MUST keep the mock working with no key.

## Done when
- Interface implemented with mock parity; fixture, 429, timeout and double-buy tests pass.
- Sandbox run steps in the report; runbook row updated.
- `pnpm typecheck && pnpm lint && pnpm test` pass; the API golden path still buys a (mock) label.
- security-reviewer co-reviewed any key, webhook or PII handling.

## References
- `invai-docs/research/10-marketplace-engineering-rules.md` R7, R8, R11, §8, §9 items 13–17, 29
- `invai-docs/research/12-security-quality-playbook.md` §1.7
- `invai-backend/src/integrations/{carriers,suppliers}/**`, `src/modules/shipping/service.ts`,
  `src/modules/inventory/service.ts`
- Related: `idempotent-side-effect`, `provider-deprecation-watch`, `scrub-pii-fixture`
