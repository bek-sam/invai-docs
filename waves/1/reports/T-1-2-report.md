# Report: T-1-2 Webhooks are verified first and deduplicated for real
Author: integrations-engineer on Opus 5.5 · 2026-09-24

```
Card: T-1-2  Owner: integrations-engineer  Scope ref: always-in-scope: security
Owned (edit): src/api/webhooks.ts, src/integrations/channels/**, new src/db/schema/webhooks.ts (+ index export)
  and its migration, src/modules/channels/sync.ts (verifyWebhook, processWebhook, completeShopifyOAuth,
  OAuth-state helpers), src/modules/channels/jobs.ts (Etsy job), tests next to these
Read-only: src/lib/queues.ts, rest of src/modules/**, src/env.ts (T-1-1), src/api/app.ts (T-1-1),
  src/db/rls-coverage.test.ts (security-reviewer)
Risk flags → co-reviewers: webhooks, migration → security-reviewer, backend-foundation
```

**Status: done, committed on `main`, not pushed.** Commit: `90657ac` (invai-backend) "Webhooks are verified first and deduplicated for real (T-1-2)".

## Built
- **One webhook route for every channel** (`POST /webhooks/:channel`) in this order: (1) verify the signature on the raw body, 401 on failure, with nothing written or enqueued; (2) read the channel's delivery id, 400 when missing or malformed, never a random UUID; (3) insert into `webhook_deliveries` with on-conflict-do-nothing, so a redelivery gets `200 {"ok":true,"duplicate":true}` and stops; (4) enqueue `channels.<channel>.webhook` with jobId `webhook-<channel>-<id>`, then 200. If the enqueue fails, the delivery row is deleted and the route returns 503, so the channel's retry is processed. Channels without webhooks (Amazon, TikTok, Walmart, eBay, CSV) never verify, so they get 401. Unknown channels get 404. (`invai-backend/src/api/webhooks.ts`)
- **Etsy Standard Webhooks** (`src/integrations/channels/etsy/webhooks.ts`):
  - dedupe on `webhook-id`;
  - `webhook-signature` can carry several space-separated `v1,<b64>` entries, and any match is accepted (every entry is checked, constant time);
  - the key is base64-decode of the secret without `whsec_`, over `id.timestamp.rawBody`;
  - ±5-minute timestamp tolerance, checked against when the delivery reached us, so a queued retry in the worker still verifies;
  - event types are matched in any case (`ORDER_PAID` / `order.paid`, `ORDER_CANCELED` / `order.canceled`);
  - the receipt in `resource_url` must belong to `shop_id`.
  Doc URLs are at the top of the file.
- **Fetch by ID:**
  - A new `order_ref` webhook event kind and an optional `fetchOrder(conn, id)` on `ChannelAdapter` (`types.ts`).
  - `processWebhook` routes by shop id to `connected` connections only, fetches the receipt outside any transaction, then imports it (or cancels it when the fetched receipt is cancelled). It never uses payload fields.
  - The Etsy mock store answers `fetchOrder` deterministically. The live Etsy `fetchOrder` throws `UPSTREAM_FAILED` ("pending marketplace approval") until the app is approved.
  - Etsy order sync and tracking stay "pending approval" in both modes. Only webhooks are mocked, so demo Etsy API connections don't start importing fake orders.
- **Latent bug fixed:** `verifyWebhook`/`processWebhook` now pick the adapter with `webhookAdapter(channel)`. That uses `channelMocked(channel)`: `env.mocks.shopify` for Shopify, and for Etsy whether `ETSY_WEBHOOK_SECRET` is set. Before, every channel used `env.mocks.shopify`. `getChannelAdapter("etsy", provider)` now selects live or mock the same way as Shopify. (`src/integrations/channels/index.ts`, `etsy/index.ts`, `modules/channels/sync.ts`)
- **Production guard:** `verifyWebhook` returns false for any channel on its mock in production. The Etsy mock's verify and fetch also refuse on their own when `env.isProd` is set. The mock secrets are public constants, so mock-signed webhooks are never accepted in prod, even with `ALLOW_MOCKS=true`.
- **`webhook_deliveries` table** (`src/db/schema/webhooks.ts`, migrations `drizzle/0006_webhooks_deliveries.sql` + `0007_webhooks_deliveries_system_writes.sql`):
  - columns: channel, delivery_id, received_at, status (`received|processed|ignored|failed`), processed_at, detail, and nullable company_id;
  - unique on `(channel, delivery_id)`;
  - tenant RLS policy, with `INSERT/UPDATE/DELETE` revoked from `invai_app`;
  - the worker marks each row processed, ignored or failed, with company_id once the delivery is routed;
  - retention is 7 days: `channels.webhookDeliveries.purge` runs nightly at 04:45 UTC (scheduler registered with the poll scheduler).
- **Shopify dedupe** uses `X-Shopify-Webhook-Id` through the same table. There's no fallback to `X-Shopify-Event-Id` or to a random UUID: a signed request without the header gets 400.
- **Shopify OAuth state:**
  - It expires after `OAUTH_STATE_TTL_MS` = 10 min, measured from the pending row's `updatedAt`, which `connect()` rewrites with every new state.
  - It's burned before anything else happens, under `SELECT … FOR UPDATE` (`consumeOAuthState`): the state is removed from the encrypted credentials and `pendingShop` is kept.
  - A second use or a racing callback is refused. A completion that fails after the burn (for example, the store is connected elsewhere) also leaves the state unusable. (`sync.ts`)

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Verify before enqueue/write; 401 for unsigned or bad signatures; nothing enqueued | yes | `src/api/webhooks.test.ts`: the enqueue spy is never called, there's no `webhook_deliveries` row and no BullMQ job, for Shopify and Etsy (unsigned, bad signature, wrong scheme). Curl cases 3, 4, 8, 9 below: 401 and no row/job |
| 2 Etsy Standard Webhooks: webhook-id dedupe, multi-signature, tolerance, fetch by ID; per-channel mock flag | yes | `etsy/webhooks.test.ts` (multi-signature any-match, rotation, stale ±301 s, receivedAt tolerance, parse, shop mismatch). `modules/channels/webhooks.test.ts`: import uses the fetched receipt (forged `grandtotal` $0.01 ignored); "with ETSY_WEBHOOK_SECRET set, Etsy goes live even while Shopify is on its mock". Curl case 1: order `9120003` imported with `total_cents 4509` from the fetch |
| 3 Persisted table, unique (channel, delivery id), ≥30 h retention + purge, replay → 200 no-op; tenancy choice explained | yes | Tests: unique per channel; purge deletes an 8-day-old row, keeps a 31-hour-old one, and that row still dedupes; app role reads only its own rows and INSERT/UPDATE/DELETE are denied. Curl cases 2 and 7: 200 duplicate. See "Decisions" |
| 4 Shopify dedupe via X-Shopify-Webhook-Id; missing header rejected | yes | Test: "a signed Shopify webhook without X-Shopify-Webhook-Id is rejected" (400, no enqueue). Curl case 5: 400 `missing delivery id` |
| 5 OAuth state ≤10 min and single use | yes | Tests: expired after TTL+1 min (BAD_REQUEST "expired"), then a fresh link works; two racing callbacks → exactly one fulfils; a failed completion burns the state |

## Checks I ran
Other cards had uncommitted work in the same tree (T-1-3's inventory schema had no migration yet, so its tests failed in the shared tree). So I ran the definition of done in a **clean git worktree at HEAD `34ed022` plus only my 17 files**. The binaries were called directly because `pnpm run` refuses a symlinked `node_modules`, and the test DB was `invai_test_t12`.

| Repo | Command | Result |
|---|---|---|
| invai-backend (clean worktree) | `tsc --noEmit` | exit 0 |
| invai-backend (clean worktree) | `biome check .` | `Checked 191 files … No fixes applied.` |
| invai-backend (clean worktree) | `TEST_DATABASE_URL=…/invai_test_t12 TEST_MIGRATION_DATABASE_URL=…/invai_test_t12 vitest run` | `Test Files 35 passed (35)` · `Tests 184 passed (184)` (includes `rls-coverage.test.ts`) |
| invai-backend (clean worktree) | `tsup` (`pnpm build`) | `Build success` |
| invai-backend (shared tree, with other cards' WIP) | `pnpm lint` | clean |
| invai-backend (shared tree) | `pnpm test` (t12 DB) | 194 passed, 1 failed: `modules/inventory/service.test.ts`, `column "submit_attempted_at" … does not exist` (T-1-3 WIP, not this card) |
| invai-backend | targeted: `vitest run src/api/webhooks.test.ts src/modules/channels src/integrations/channels src/db/rls-coverage.test.ts` | `6 passed`, `50 passed` |

## Exercised for real
API and worker ran from the clean worktree (`tsx src/api/server.ts`, `tsx src/worker/index.ts`) on `PORT=3120`, against `invai_test_t12`, with `REDIS_URL=redis://localhost:6379/12`, an isolated Redis DB. The shared dev DB and queues were not touched. I added one connected Etsy connection (shop `31200001`, provider mock) to the t12 DB and signed the requests with a small node script (mock secrets).

| # | Request | Result |
|---|---|---|
| 1 | Etsy, valid signature, `webhook-id: msg_curl_001`, ORDER_PAID receipt 9120003 with forged `grandtotal` 1¢ | `{"ok":true} HTTP 200`. Job `bull:sync:webhook-etsy-msg_curl_001` queued. The worker processed it: delivery `processed`, routed; order `etsy 9120003`, `total_cents 4509` (from the fetch, not the payload) |
| 2 | Same `webhook-id` again, fresh timestamp and signature (Etsy retry) | `{"ok":true,"duplicate":true} HTTP 200`, still one row and one job |
| 3 | Etsy, body changed after signing | `{"error":"invalid signature"} HTTP 401`, no row for `msg_curl_002` |
| 4 | Etsy, unsigned | 401, no row for `msg_curl_003` |
| 5 | Shopify, signed, only `x-shopify-event-id` | `{"error":"missing delivery id"} HTTP 400` |
| 6 | Shopify, signed, `x-shopify-webhook-id: curl-shop-010` | `{"ok":true} HTTP 200`, job queued; worker: `ignored`, "no connection for t12-none.myshopify.com" |
| 7 | Same Shopify id again | `{"ok":true,"duplicate":true} HTTP 200`, not enqueued again |
| 8 / 9 | Shopify, bad HMAC / unsigned | `{"error":"invalid signature"} HTTP 401`, no rows for `curl-shop-011/012` |
| 10 | Etsy body with a Shopify HMAC; `/webhooks/amazon` | 401 / 401 |

Final state: `webhook_deliveries` held exactly `msg_curl_001` (processed), `curl-shop-001` and `curl-shop-010`. Redis held exactly the three matching `webhook-*` jobs, plus the scheduler `bull:sync:repeat:channels-webhook-deliveries-purge`. (`curl-shop-001` came from a first curl attempt whose header quoting was broken. It was a valid delivery and was recorded normally.) No request was permissioned, so there is no role-refusal case. The refused cases are the signature and delivery-id rejections above.

## Decisions
- **Tenant table vs global table:** a tenant-shaped table, with nullable `company_id` + `tenantPolicy` + RLS, where only the system role writes.
  - The architect recommended a global table. But `src/db/rls-coverage.test.ts` (owned by security-reviewer) fails any table that has neither `company_id` nor an entry in `PUBLIC_READ_TABLES`. A deny-all global table would have needed another owner's test edited mid-wave.
  - The row does become tenant data once routed: which shop a delivery was for, and its outcome. That is useful for per-connection health.
  - Deliveries are recorded before routing, so `company_id` is null at insert and filled by the worker.
  - `INSERT/UPDATE/DELETE` are revoked from `invai_app` (migration 0007, same pattern as `plans`/`trademark_marks`). Without that, a tenant code path could pre-insert `(channel, delivery_id)` and suppress another shop's webhook. The app role can only read its own company's rows.
  - All writes go through `withSystem`, as for other pre-tenant or cross-tenant work (webhook routing, purge).
  - If security-reviewer prefers the pure global table, it is a small follow-up: add a `SYSTEM_ONLY_TABLES` set to the coverage test, then drop the column and policy.
- **Retention is 7 days**, not 30 h: research 10 R4 says a 7-day TTL, and the card's "at least 30 hours" is satisfied. The purge runs nightly on the `sync` queue.
- **Missing delivery id → 400**, after the signature check (a bad signature is still 401 first). For Etsy, `webhook-id` is part of the signed string, so it can't be missing without failing verification.
- **Enqueue failure → delete the row, 503**, so the channel retries. Without this, a Redis blip would leave the delivery recorded but never processed, and every retry would be dropped as a duplicate.
- **The worker re-verifies against the job's `receivedAt`,** not the current time. Otherwise the 5-minute Etsy tolerance would drop legitimate deliveries whose job retried later, and the dedupe row would then block Etsy's own retries.
- **Etsy mock/live flag reads `process.env.ETSY_WEBHOOK_SECRET` directly** (`etsyWebhookSecretFromEnv`), because `env.ts` belongs to T-1-1 and has no Etsy key. See the cross-card follow-ups.
- **OAuth state age uses `channel_connections.updatedAt`,** because `connect()` (in `service.ts`, which isn't mine) stores no issue time. That is exact today, since `connect()` rewrites the row for every new state. An unrelated update to a pending row would restart the clock, which only extends a link and never lets a burned state through.
- **Two migrations:** 0006 generated, 0007 a custom `--custom` REVOKE, per `add-tenant-table`. T-1-3 generated `0008_inventory_po_idempotency` on top of my 0007 snapshot: no journal collision. My commit carries the journal with entries 6–7 only. Entry 8 is left in the working tree for T-1-3 to commit with their SQL.
- **Commit mechanics:** I committed through a private index (`GIT_INDEX_FILE`, `read-tree HEAD`, only my 17 paths, `commit-tree`, `update-ref` with the old-value check), so other agents' staged work in the shared index was not swept in. Afterwards I ran `git reset -- <my paths>` so the shared index matches the new HEAD for my paths.

## Known gaps and follow-ups
- **Live Etsy `fetchOrder` isn't implemented.** With a real `ETSY_WEBHOOK_SECRET`, verified deliveries are recorded and enqueued, then the job fails with "pending marketplace approval" and the row ends up `failed`. It needs `GET /v3/application/shops/{shop_id}/receipts/{receipt_id}` once the app is approved (B-04). There are no Etsy API-mode connections in `connected` status today, so nothing routes yet.
- **Staleness check (`updated_at`)** isn't done. That is B-12 (backend-engineer), out of scope.
- **Owner-facing strings:** the OAuth errors ("link has expired", "already used. Connect the store again.") are English only. They travel as the `?error=` query param to the web app, which shows `message` as-is. A Spanish version needs web-side i18n keyed by an error code.
- **The runbook's mock → real row for Etsy** needs `ETSY_WEBHOOK_SECRET` (the portal's `whsec_…` signing secret; webhook URL `https://<api>/webhooks/etsy`), added with docs-writer.
- **No `webhook_deliveries` UI or health read yet.** The data is there, per company, for a later "last webhook" health view.

## Cross-card impacts
- **T-1-1 (backend-foundation), `src/env.ts`:** add `ETSY_WEBHOOK_SECRET` to the env schema and an `env.mocks.etsy`. Then `etsyWebhookSecretFromEnv()`/`etsyMocked()` in `integrations/channels/etsy/*` can read it (a one-line change for me). Don't add it to `PRODUCTION_KEYS` until Etsy is approved. Mock Etsy webhooks are already refused in prod by this card.
- **T-1-1, `src/api/app.ts` `noMockWebhooksInProd`:** still Shopify-only, but it's now redundant with the generic prod check in `verifyWebhook`. It can stay or be removed, and needs no change for this card.
- **security-reviewer:** please co-review the tenancy choice above and `rls-coverage.test.ts` (unchanged, still green).
- **Shared-index hazard (for the tech lead):** commit `7e2422d` "Production key guard … (T-1-1 r2)" includes the deletion of `src/db/seed/trademarks.ts` (510 lines). That deletion looks like T-1-5's work, which was staged in the shared index when T-1-1 committed. Please check with T-1-1 and T-1-5 that this was intended.

## Blocked by other owners
- None. I worked around `env.ts` (read the Etsy secret directly) and around `rls-coverage.test.ts` (tenant-shaped table, see Decisions).

## Processes and data
- Stopped: the API on :3120 and the worker (both `tsx`, started from `/private/tmp/t12-verify`). `lsof -iTCP:3120` is empty and no `t12-verify` processes remain. I flushed Redis DB 12 (mine only) and removed both temp worktrees (`git worktree prune`).
- Shared dev DB: untouched. All data went to `invai_test_t12`, which keeps one extra Etsy connection and an imported order from the curl run.
- The report is not committed. Nothing was pushed.
