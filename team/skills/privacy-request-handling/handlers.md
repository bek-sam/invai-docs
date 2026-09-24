# Shopify compliance webhooks and data scope

Spec input for backlog item B-06 (integrations-engineer, with compliance-officer). The compliance officer
writes the requirements; the engineer designs and builds. Source:
https://shopify.dev/docs/apps/build/compliance/privacy-law-compliance (re-check before the card starts).

## The three webhooks
| Topic | When Shopify sends it | What we must do | Deadline |
|---|---|---|---|
| `customers/data_request` | A customer asks the store owner for their data | Collect everything we hold about that customer for that shop and give it **to the store owner** (not to the customer) | 30 days |
| `customers/redact` | The store owner asks to delete a customer's data (Shopify holds it 10 days if the customer had recent orders [verify]) | Delete or redact that customer's PII for that shop, unless law requires keeping it | 30 days |
| `shop/redact` | 48 hours after the store uninstalls the app | Delete that shop's data held because of the Shopify connection | 30 days |

**Requirements for the handler**
1. Declared in `shopify.app.toml` as compliance topics (app-scoped), not created per shop.
2. HMAC verified on the raw body before any work (`X-Shopify-Hmac-SHA256`, constant-time); **401** on a bad
   signature; 200 fast, then enqueue.
3. Idempotent on `X-Shopify-Webhook-Id` (persisted, not only a BullMQ job id: research 10 R4).
4. The job matches the shop to a `connected` channel connection (S-04 rule), enters the tenant with
   `withTenant`, and never trusts a company id from the body.
5. A privacy-request row is written (a new tenant table needs `company_id` + RLS) with the request id, topic,
   received and completed timestamps and counts, and no PII beyond the Shopify customer id needed to act.
6. An alert fires if any request is still open after 20 days.
7. Tests: bad HMAC → 401; duplicate delivery → one action; unknown shop → logged and 200; redaction removes
   the PII listed below and leaves non-PII order facts.

## Data scope: where one buyer's data can live
| Place | Path / key | Holds |
|---|---|---|
| `buyer_pii` table | `invai-backend/src/db/schema/orders.ts` | name, email, phone, company, street (encrypted), city/state/zip (plaintext, S-29) |
| `orders` | same file | `buyer_note`, `buyerName` exposure (S-29), channel order id |
| Personalization | `src/modules/personalization/` | buyer-typed text on the item |
| S3 objects | `{company}/raw/`, `{company}/csv/`, `{company}/label/` | raw payloads, imported CSVs, label PDFs (30-day sweep `purgePiiObjects`) |
| Outbox / events | `src/lib/outbox.ts` | event payloads (verify ids only) |
| Job queue | `src/lib/queues.ts` (BullMQ in Valkey) | webhook bodies until the job is removed |
| AI logs | `src/ai/gateway.ts` | should hold ids and token counts only (`stripPiiDeep`, `scrubAssistantRun`); verify |
| EasyPost | outside our DB | addresses on shipments: a sub-processor; note it in the reply |
| Backups | RDS snapshots | age out on the retention window (state it) |

Keep for the shop's accounting unless full deletion is asked: order id, SKUs, quantities, amounts, fees,
dates, tracking number.
