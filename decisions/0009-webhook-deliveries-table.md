# 0009: Webhook deliveries are a tenant table with system-only writes

- Status: accepted (2026-09-24)
- Type: architecture / security
- Card: T-1-2 (wave 1). Reviewed by reviewer, security-reviewer and backend-foundation (all approve).

## Context
Webhook dedupe needs a persisted record of each delivery (channel + delivery id), kept at least 30 hours. The plan review suggested a plain global table. However, `rls-coverage.test.ts` fails any table that has neither `company_id` nor a public-read entry. Also, once a delivery is routed to a shop, it's tenant data.

## Decision
`webhook_deliveries` has a nullable `company_id`, set once a delivery is routed, and an RLS tenant policy. The app role `invai_app` can only read its own company's rows. Migration 0007 revokes insert, update and delete, so only system code (`withSystem`) writes. That way no tenant can block or forge another shop's delivery. The table is unique on (channel, delivery id). Rows are kept 7 days and purged nightly.

## Consequences
- A redelivery is acknowledged and does nothing.
- If enqueueing fails, the row is deleted and the route answers 503 so the channel retries. The remaining risk: a genuine double run is possible only if the completed BullMQ job has aged out of Redis (24 h / 5,000) before a legitimate retry lands. That's accepted as low.
- New system-only tables follow the same pattern until the coverage test gains a system-table list.
