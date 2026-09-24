---
name: privacy-request-handling
description: Handle a privacy request about buyer or user data in InvAI - Shopify's customers/data_request, customers/redact and shop/redact webhooks, a GDPR or CCPA/CPRA data-subject request (DSAR) from a shop or a buyer, and early buyer PII purge - with the legal clocks, a PII-free log and owner drafts. Use for "DSAR", "delete my data", "GDPR request", "redact", "data export", "right to know".
---

# Privacy request handling

Every privacy request is logged without PII, routed to the right controller, completed inside the strictest
clock, and proven done.

## When to use
- A Shopify compliance webhook arrives, or you are specifying its handler (B-06).
- A shop asks us to export or delete one buyer's data, or all its data (offboarding).
- A buyer contacts InvAI directly about their data.
- A user of InvAI (a shop's staff member) asks about their own account data.

## Who we are for each kind of data
- **Buyer data (marketplace orders):** InvAI is a **processor** (GDPR) / **service provider** (CCPA). The shop
  is the controller. We act on the shop's instruction and help it answer (GDPR Art. 28(3)(e), 11 CCR §7051).
- **Shop staff account data:** InvAI is the **controller**. We answer the person directly (through the owner).

## Clocks (the strictest one wins)
| Source | Clock | Rule |
|---|---|---|
| Shopify `customers/data_request`, `customers/redact`, `shop/redact` | complete within **30 days** of receipt; `shop/redact` arrives **48 h after uninstall** | https://shopify.dev/docs/apps/build/compliance/privacy-law-compliance |
| GDPR (controller's duty) | **1 month**, extendable by 2 months with notice in the first month | https://gdpr-info.eu/art-12-gdpr/ |
| CCPA/CPRA (business's duty) | confirm receipt in **10 business days**; respond in **45 days**, extendable once by 45 | Cal. Civ. Code §1798.130; 11 CCR §7021 |
| Our target as processor | acknowledge to the shop in **2 business days**; finish our part in **15 days** | leaves the shop room inside its own clock |
| Routine purge | buyer PII deleted **30 days after delivery** (fallback shipped or cancelled + 30 d) | `PII_RETENTION_DAYS` in `invai-backend/src/modules/orders/jobs.ts`; Amazon DPP |

## Steps
1. **Log it first** in `invai-docs/compliance/privacy-requests/log.md` (created on first use) with
   [log-template.md](log-template.md). The log holds a request id, the shop's company id, channel, type,
   received date, due dates and status. **No names, emails or addresses**; refer to the buyer as "buyer of
   order <channel order id>" at most.
2. **Classify:** access/export, deletion/redaction, correction, opt-out of sale/sharing (we don't sell or
   share: say so), or shop offboarding (`shop/redact`, cancellation).
3. **Route it:**
   - From Shopify webhooks: the handler acts automatically once B-06 is built. Until then no Shopify listing
     exists, so no webhook can arrive; the handler spec is in [handlers.md](handlers.md).
   - From a shop: confirm it is the account owner (the owner checks through the account email on file).
     Proceed on the shop's instruction.
   - From a buyer directly: we don't decide. Draft a reply for the owner (`send-owner-draft`) saying InvAI
     processes data for the shop, naming the shop, and that we have passed the request on. Draft a second note
     to the shop with the request and the clock. Do not confirm or deny what data we hold to the buyer.
4. **Find the data** (the scope list in [handlers.md](handlers.md)): `buyer_pii` rows by order, raw channel
   payloads and CSVs and labels in S3 (`{company}/raw|csv|label/`), outbox and event payloads, BullMQ job
   data, AI logs, `orders.buyer_note`, personalization text. The finding and export tool does not exist yet
   (G13, B-23, "to be created"): until it does, an engineer runs it on a card, never by hand-editing a
   production database.
5. **Act:**
   - Export: a machine-readable file for the shop (never to the buyer directly), delivered by the owner.
   - Delete/redact: remove or null PII fields, keep non-PII order facts needed for the shop's accounting
     (order id, SKU, amounts, dates) unless the shop asks for full deletion. Backups age out on the RDS
     retention window; say so in the reply.
   - Shop offboarding: export window, then delete the company's data within 30 days (research 12 §2.4).
6. **Prove it:** record the counts (rows, objects) and the command or job run id in the log. The engineer's
   card report is the evidence.
7. **Close it:** status `done`, the completion date, and the owner draft id for the confirmation to the shop.
8. **Escalate** with `escalate-to-owner` if a clock is at risk, the requester's identity is doubtful, a legal
   hold or law-enforcement request is involved, or the request suggests a breach (then `incident-response`
   with the 24-hour shop and Amazon clocks).

## Rules (MUST / MUST NOT)
- MUST NOT put buyer or user PII in the log, the inbox, reports, tests or commits.
- MUST NOT delete, export or change production data yourself. Engineers do it on a card with review.
- MUST NOT reply to a buyer, shop or marketplace directly. All replies go through `send-owner-draft`.
- MUST verify Shopify compliance webhooks by HMAC on the raw body and return 401 on a bad signature (research
  12 §1.8).
- MUST keep marketplace data out of model training (research 10 R15) and say so if asked.
- MUST treat a missed clock as an incident for the retro (`log-lesson`).

## Done when
- The request is in the log with type, dates, due date and status, and no PII.
- The data was found, exported or deleted by a reviewed card, with counts recorded.
- The confirmation draft to the shop (and the buyer note, if any) is queued for the owner.
- Closed before the strictest clock, or escalated before it ran out.

## References
- [handlers.md](handlers.md): Shopify webhook handler spec and the data scope
- [log-template.md](log-template.md)
- `invai-docs/research/12-security-quality-playbook.md` §1.8, §2.2, §2.4, §2.7;
  `research/10-marketplace-engineering-rules.md` R14, R15, §5
- `invai-docs/waves/backlog.md` B-06 (webhooks), B-23 (export and deletion)
- Related playbooks: `legal-doc-draft` (DPA terms), `incident-response`, `send-owner-draft`,
  `scrub-pii-fixture`
