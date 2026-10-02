---
name: shopify-gdpr-webhooks-live
description: Shopify's three GDPR compliance webhooks (customers/data_request, customers/redact, shop/redact) are already implemented and tested, not just planned.
metadata:
  type: project
---

`customers/data_request`, `customers/redact` and `shop/redact` are all built, HMAC-verified, and covered by
tests: `invai-backend/src/integrations/channels/shopify/common.ts:265-267` (topic list),
`invai-backend/src/modules/privacy/service.ts:57-62` (handler logic — `customers/data_request` opens a
30-day-due request for the shop owner; `customers/redact` and `shop/redact` remove PII), tests at
`invai-backend/src/modules/privacy/service.test.ts:143-268`.

**Why this matters:** this is strong, citable evidence for the DPA, privacy policy, Shopify App Store
packet (protected customer data / GDPR webhooks requirement) and the `privacy-request-handling` playbook —
don't describe this as a future/planned item.

**How to apply:** for any Shopify-related compliance packet or DSAR-process doc, cite these three handlers
directly instead of writing a generic "we will build compliance webhooks" placeholder.

See also [[privacy-retention-code-built]].
