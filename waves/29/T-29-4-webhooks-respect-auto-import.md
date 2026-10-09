# T-29-4: Webhooks don't create new orders while auto-import is off

| Field | Value |
|---|---|
| Wave | 29 |
| Scope ref | `always-in-scope: bug` in `product/scope.md#mvp-in` item 2 (Shopify API adapter, import) |
| Spec | none; backlog B-292 (`waves/28/reviews/plan-architect.md` item 15); product-manager decision in the wave 29 plan review |
| Owner | backend-engineer (area: channels) |
| Reviewer | reviewer (opus) |
| Co-reviewers | none: the change is a skip rule after verification; signature checks, dedupe and the route (`src/api/webhooks.ts`) are untouched. If the build needs to touch verification or idempotency, stop and ask: that adds the security-reviewer |
| Risk flags | import correctness (never lose an order) |
| Model | sonnet |

## Owned paths (edit)
- `invai-backend/src/modules/channels/**` (`sync.ts` `handleWebhook` and its tests)

## Read-only paths
- `invai-backend/src/api/webhooks.ts`, `src/integrations/**`, everything outside `modules/channels`, `invai-contracts/**`, `invai-web/**`

## Depends on
- Decision 0030 (product, accepted 2026-10-09): with `autoImport === false`, a webhook for an order we don't have yet is acknowledged and skipped; updates and cancels for orders we already have still apply; a manual Sync now imports the skipped ones.

## Design (architect plan review item 9)
- `handleWebhook` loops over every connected row for the shop (`channels/sync.ts:873-952`) and already uses `return skip` inside the loop (`:895`). The `autoImport` check is per connection (`continue`, never `return`), placed before `store.fetchOrder`, with the existence check under that connection's `withTenant`.

## Acceptance criteria
1. Given a connection with `autoImport: false`, when a verified order-created webhook arrives for an order not in the DB, then no order is created, the delivery is acknowledged (2xx, no retry storm), and a log line (no PII) records the skip.
2. Given the same connection, when a cancel or update webhook arrives for an order already imported, then it applies as today (a cancel still stops production).
3. **No lost orders.** An order skipped this way is imported by the next manual "Sync now" (more than one page of backlog may need more than one Sync now; say so in the report). Live property proven by a unit test: a webhook never moves `channel_connections.cursor` (`channels/service.ts:604` sets only `lastWebhookAt`), and Shopify reads from `cursor - 60s` by `updated_at` (`shopify/orders.ts:215`); Etsy uses `min_last_modified` and gets the same test. If the cursor would miss it, stop and report before building more.
4. `autoImport` on (or unset) behaves exactly as today.
5. Webhook dedupe stays: a skipped delivery that is re-sent is skipped again, and after the shop turns auto-import back on, the same order arriving by webhook or poll imports once.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test` in `invai-backend` (channels tests while building, the full suite once at the end).
- Exercise for real on your own API (`PORT=3152`, `REDIS_URL=redis://localhost:6379/14`) with the mock Shopify connection: turn auto-import off as `owner@desertbloom.test`, post a signed mock webhook whose body is `mockShopifyOrder(seq+1)` for the connection's cursor (the mock's `fetchOrders` returns synthetic `mockShopifyOrder(seq+1..)`, `shopify/mock.ts:162-170`), show no order; run a manual sync, show it imported once; restore the setting. Record every PID you start and stop it; leave the dev DB's settings as you found them.

## Out of scope
- Poll-started syncs (done in T-28-5), UI copy, settings screen.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
