# T-1-2: Webhooks are verified first and deduplicated for real

| Field | Value |
|---|---|
| Wave | 1 |
| Scope ref | always-in-scope: security |
| Backlog | B-43, B-07, webhook part of B-63 (Shopify dedupe, missing-header fallback, OAuth state expiry) |
| Owner | integrations-engineer |
| Reviewer | reviewer |
| Co-reviewers | security-reviewer, backend-foundation (new table + migration) |
| Risk flags | webhooks, migration |
| Model | opus |

## Owned paths (edit)
- `invai-backend/src/api/webhooks.ts`
- `invai-backend/src/integrations/channels/**`
- New `invai-backend/src/db/schema/webhooks.ts` (export it from the schema index) and its generated migration
- `invai-backend/src/modules/channels/sync.ts` (only `verifyWebhook`, `processWebhook`, `completeShopifyOAuth`, and the OAuth-state helpers) and `invai-backend/src/modules/channels/jobs.ts` (only to register the Etsy webhook job), granted on this card — the acceptance criteria (Etsy fetch-by-ID, Shopify dedupe fix, OAuth state expiry) live here, not only in `integrations/channels/**`
- tests next to these files

## Read-only paths
- `src/lib/queues.ts`, the rest of `src/modules/**` (call existing functions; don't edit)

## Evidence
`build/audit-2026-09-24.md` §A-BE B-63; backlog B-07 and B-43; `research/10-marketplace-engineering-rules.md` (webhook rules).

## Acceptance criteria
1. Every webhook route verifies the signature **before** it enqueues or writes anything. An unsigned or badly signed request gets 401, and nothing is enqueued (tests prove both).
2. Etsy follows the Standard Webhooks shape:
   - dedupe on the `webhook-id` header;
   - verify `webhook-signature`, which can carry several signatures (accept if any one matches), with a timestamp tolerance;
   - after verifying, the handler fetches the resource by ID and doesn't trust the payload.
   - Note: `verifyWebhook`/`processWebhook` in `modules/channels/sync.ts` currently pick the mock vs. live adapter with `env.mocks.shopify` regardless of the `channel` argument. Fix this to key off the right per-channel mock flag as part of this card, or Etsy webhooks will verify (and process) against the wrong adapter.
3. There's a persisted `webhook_deliveries` table: channel, delivery id, received_at, status. It's unique on (channel, delivery id) and rows are kept at least 30 hours, with a purge job. A replay of the same delivery is acknowledged with 200 and does nothing. The table is global (no tenant data in it), or it has `company_id` and RLS if it stores tenant data. Explain the choice in the report.
4. Shopify dedupe uses `X-Shopify-Webhook-Id` through the same table. There's no fallback to a random UUID when the header is missing: such a request is rejected.
5. The Shopify OAuth `state` expires after at most 10 minutes and can be used only once.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test` in invai-backend, with your own test DB (see wave.md).
- Curl against a running API on your port:
  - a valid signed mock webhook → 200 and enqueued
  - the same delivery again → 200 and not enqueued again
  - a bad signature → 401 and nothing enqueued

## Out of scope
- Shopify polling and paid-status filtering (wave 3). Compliance webhooks (B-06, wave 3).
