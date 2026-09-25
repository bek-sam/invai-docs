# Report: T-3-1 Shopify adapter complete
Author: integrations-engineer on Opus 5.5

```
Card: T-3-1  Owner: integrations-engineer  Scope ref: scope.md#mvp-in item 2; always-in-scope: compliance
Owned (edit): integrations/channels/shopify/**, integrations/channels/{index,types}.ts, api/webhooks.ts,
  modules/channels/{sync,jobs,service}.ts (not importCsv), modules/privacy/** (+ schema/migration), shopify.app.toml, tests
Risk flags -> co-reviewers: webhooks, pii, marketplace-policy -> security-reviewer, compliance-officer
```

## Commits (invai-backend, `main`, not pushed)
| SHA | What |
|---|---|
| `563287b` | `setAvailability`: `changeFromQuantity` compare-and-set + `@idempotent` key, one retry on a stale read (B-04). **T-3-3 can start on this.** |
| `cc35a08` | Orders: paid-only import, `updated_at` poll, order and line pagination, `throttleStatus` waits, withheld PII stays null (B-28, B-63) |
| `f9140dd` | Webhook subscriptions: failures show as degraded in `channels.health`, daily re-check, disconnect unsubscribes and uninstalls (B-63) |
| `5a89ba8` | `privacy_requests` table + migration 0014 (system-only writes) (B-06) |
| `0bb1460` | Compliance webhooks handled inline (redact before the 200), data requests recorded, `shopify.app.toml` (B-06) |
| `50e045f` | Expiring offline tokens: refresh under a row lock, rotation stored, failure flags the connection (B-05) |
| `2a15725` | Poller skips pending-approval, backoff for failing connections, expired trials; `sync_failed` once per outage (B-99) |
| `00c35e4` | Formatting of `db/schema/privacy.ts` |

## Built
- **Interface for T-3-3** (`integrations/channels/types.ts`): `setAvailability(conn, [{ listingVariantId, channelSku, available }], { idempotencyKey? }) -> { updated, results: [{ listingVariantId, status: "set"|"not_found"|"failed", available, message }] }`. The adapter needs `channelSku` because it never touches the DB. The old `{ channelSku, quantity }` shape still compiles (marked deprecated), so `inventory/availability.ts` isn't broken. **T-3-3 should pass a stored key per push intent** as `idempotencyKey`, so a retry after a crash reuses it. Without one, the adapter makes a fresh UUID for each call.
- **Shopify inventory** (`shopify/inventory.ts`):
  - Batched SKU lookup (`sku:"a" OR sku:"b"`), filtered to exact SKU matches.
  - Reads the current `available` at the location, then writes `inventorySetQuantities` with `changeFromQuantity` set to that value, plus `@idempotent(key:)` and `referenceDocumentUri`. `ignoreCompareQuantity` is gone.
  - `CHANGE_FROM_QUANTITY_STALE`: re-read, then retry once with `<key>:retry`. A second mismatch fails the item.
  - Unchanged values aren't written. Batches hold at most 250 items.
- **GraphQL client** (`shopify/client.ts`):
  - Tracks `extensions.cost.throttleStatus` per shop and waits `(cost − available) / restoreRate` before a call and after a `THROTTLED` answer.
  - HTTP 429 and 5xx back off with jitter (honouring `Retry-After`). 5 attempts, 30 s cap per wait. No redirects.
  - 401/403 raises `ShopifyAuthError`, which the adapter maps to `UPSTREAM_FAILED`.
- **Orders** (`shopify/orders.ts`, `common.ts`):
  - `paymentDecision` is shared by webhooks and the poll. PAID, PARTIALLY_PAID and PARTIALLY_REFUNDED are imported. PENDING (this includes cash on delivery), AUTHORIZED and unknown statuses are skipped and logged, with the reason stored on `webhook_deliveries.detail`. REFUNDED, VOIDED and EXPIRED cancel the order.
  - The poll filters on `updated_at` only. It pages 10 orders at a time, up to 50 pages per run, and the watermark carries on in the next run.
  - Line items past the inline 25 are paged 100 at a time.
  - Quantities come from `currentQuantity` (`current_quantity` in REST).
  - Every query stays under the 1,000-point cap. The old `orders(first:50){lineItems(first:100)}` and fulfillment-orders queries were far over it; the latter now uses 5×50.
- **PII**:
  - When Shopify withholds the address (no Level 2), `shipTo` is null instead of empty strings. Email and phone are null.
  - `buyerName` falls back to the label "Shopify customer", because the contract and `buyer_pii.name` require a string.
- **Subscriptions** (`shopify/subscriptions.ts`):
  - `ensureWebhooks` lists our subscriptions by `uri` and creates only the missing topics. Refused topics are stored in `credentials.webhooks`.
  - `channels.health` then shows `ok:false` with the reason, and the status stays `connected`, so webhooks still route and the poll still runs.
  - A daily job at 05:15 UTC recreates dropped subscriptions.
  - OAuth (live and mock) subscribes through the adapter.
- **Disconnect** (`service.ts`):
  - The row is marked disconnected and its credentials are dropped in the transaction.
  - After commit, our subscriptions are deleted and `appUninstall` is called, which revokes the token.
  - The outcome is audited. If cleanup fails, it becomes the connection's last error, with the next step for the shop.
- **Compliance** (`modules/privacy/service.ts`, `api/webhooks.ts`, `shopify.app.toml`):
  - The three topics are HMAC-verified, deduped on `X-Shopify-Webhook-Id` and **handled inside the request**. A failure answers 500 and the delivery record is removed, so Shopify's retry runs again.
  - The shop comes from the signed body (`shop_domain`). A header naming a different shop is refused.
  - Redaction reaches only orders imported from that store's connections, disconnected ones included. It deletes `buyer_pii`, clears `buyer_note`, `buyer_ref`, personalization answers and file URLs, and deletes the raw payload object first, then the DB rows.
  - Every request is recorded in `privacy_requests`, which holds ids only. Redactions are `completed` with counts; `data_request` is `open` and due in 30 days. The daily job logs any request still open after 20 days.
- **Tokens** (`shopify/auth.ts`, `service.ts`):
  - The code exchange sends `expiring: 1` and stores the refresh token and both expiries.
  - `refreshConnectionToken` holds `SELECT … FOR UPDATE`, re-reads the row, refreshes (form-encoded `grant_type=refresh_token`) and stores the rotated pair in one update.
  - A refresh runs when a token has under 20 minutes left: in the 10-minute poll job, and before each sync and tracking push.
  - A failure keeps the old credentials, records `refreshError` (permanent when the token is refused), sets the last error and shows `ok:false`.
- **Poller** (`sync.ts`):
  - Skips pending-approval adapters, companies whose trial expired without a plan, and failing connections until one hour after their last error.
  - `connection.sync_failed` is emitted only when a connection starts failing.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Paid orders only; poll by `updated_at` catches refunds, voids and cancels | Yes | `orders.test.ts` "decides by financial status", "the poll filters on updated_at only…"; `modules/channels/shopify.test.ts` pending skipped, then paid imported, refunded cancels; real run below |
| 2 Line items beyond 100 | Yes | `orders.test.ts` "pages orders and pages line items beyond the inline 25" (130 lines, 2 extra pages) |
| 3 Throttle + PII null | Yes | `orders.test.ts` throttle wait math, pre-wait + THROTTLED retry, 429 give-up; null ship-to/email/phone tests |
| 4 Subscription failure degraded in health; disconnect unsubscribes and revokes | Yes | `subscriptions.test.ts` (fetch-mocked create/partial failure/delete/appUninstall/401); `shopify.test.ts` degraded health, daily re-check clears it, disconnect audit; real run below |
| 5 Compliance: verified, deduped, redact synchronous, data_request recorded, TOML | Yes | `modules/privacy/service.test.ts` (7 tests: 401, redact before 200 incl. S3 object gone, duplicate, cross-shop isolation, header spoof, data_request due 30 d, shop/redact after uninstall, unknown shop); `invai-backend/shopify.app.toml` |
| 6 `changeFromQuantity` + `@idempotent`, one retry on mismatch | Yes | `inventory.test.ts` (6 tests) |
| 7 Expiring tokens: refresh, rotate, flag on failure | Yes | `auth.test.ts` (4) + `shopify.test.ts` refresh/rotation, no early refresh, concurrent lock = 1 refresh, refused refresh flags health |
| 8 Poller skips; no sync_failed spam | Yes | `shopify.test.ts` "skips pending-approval…" and "sync_failed once per outage" |
| 9 Fetch-mocked tests | Yes | the files above |

## Checks I ran
| Where | Command | Result |
|---|---|---|
| committed HEAD `00c35e4` (clean worktree, so other agents' WIP isn't included) | `tsc --noEmit` | ok, no errors |
| same | `biome check .` | "Checked 232 files … No fixes applied." |
| same | `tsup` (pnpm build) | "Build success" |
| same | `vitest run` (test DB `invai_test_t31`) | **55 files, 397 tests passed** |
| shared working tree (includes T-3-2 and T-3-4 WIP) | `pnpm test` | 59 files, 414 tests passed |
| baseline before I started | `pnpm test` | 45 files, 318 passed |

In the shared tree, `pnpm typecheck` currently fails on `src/modules/shipping/jobs.ts:121` (`applyTrackerUpdate` not found). That is T-3-2's in-progress code, not mine. It was clean on committed HEAD.

## Exercised for real
The API and worker ran on port 3110 from a clean worktree at HEAD, against the DB copy `invai_t31_copy`, with mock Shopify and Redis db 1.
- Signed `orders/create` with `financial_status: pending` → 200. The delivery row is `ignored` with detail "order 7310000001 not paid (pending); skipped", the worker logged `webhook skipped`, and no order was created.
- Signed `orders/create`, paid → 200. Order `7310000002` was imported with its `buyer_pii` row and raw payload.
- Bad HMAC → 401 `invalid signature`.
- Signed `customers/redact` with `orders_to_redact: [7310000002]` → 200 `{"handled":true}`. Right after the answer, `buyer_note`, `buyer_ref` and `raw_payload_key` were null and there were 0 `buyer_pii` rows. `privacy_requests` held `customers/redact | completed | {7310000002} | {"orders":1,"buyerPii":1,"rawPayloads":1,"personalizedItems":0}`.
- `channels.disconnect` as presser → 403 FORBIDDEN (`channels.manage`).
- Reconnected via mock OAuth (302 back to web). The log showed `mock shopify webhooks subscribed … topics: 4`, and `channels.health` was ok.
- Simulated a subscription failure in the stored state. `channels.health` then gave `ok:false` with "Webhook subscription failed: ORDERS_UPDATED (simulated: Access denied). Orders still arrive by the 10-minute poll; reconnect the store if this persists."
- `channels.disconnect` as owner → 200. The log showed `mock shopify unsubscribed and uninstalled … unsubscribed: 4`, and the audit row reads "Shopify: 4 webhook subscription(s) removed; app uninstalled and access revoked".
- The seeded Shopify connection has no stored token, so its first disconnect correctly made no remote call.

## Decisions
- **"Degraded" is a health state, not a new connection status.** A new status would be a contract change (`CONNECTION_STATUSES` belongs to the architect), and webhook routing only goes to `connected` connections, so a degraded store would lose its webhooks. The reason lives in the encrypted `credentials.webhooks`, and `health.ok`/`lastError` show it.
- **PARTIALLY_REFUNDED is imported.** It was paid, and the rest still ships (research 10 §9 item 4). REFUNDED, VOIDED and EXPIRED cancel.
- **Compliance topics skip the queue** so the PII is gone before the 200, as the card requires. Everything else still goes through the queue.
- **The privacy shop comes from the signed body.** Shopify doesn't sign headers.
- **`privacy_requests` is system-write-only** (decision 0009's pattern). A future "mark answered" procedure will need a narrow grant.
- **Poll backoff is a fixed 1 hour** after the last error. There is no failure counter column, so it isn't exponential.
- **Order webhooks are still API-created shop-scoped subscriptions,** with a daily re-check. Only the compliance topics are app-scoped in TOML. Declaring the order topics in TOML as well would double deliveries.

## Known gaps and follow-ups
- **No reviews yet.** Reviewer, security-reviewer and compliance-officer still need to review before anything is pushed.
- **`appUninstall` arguments not confirmed.** Shopify's page confirms the mutation and its payload (`app`, `userErrors`) but its argument list didn't render, so I call it with no arguments. Confirm against a dev store (OI-2).
- **Throttle state is per process,** not the shared Redis bucket R7 asks for. The worker is the main caller. Follow-up: back it with `suppliers/ratelimit.ts`.
- **A 401 during a call doesn't force a refresh-and-retry.** The proactive 20-minute refresh covers normal expiry.
- **Refresh-token expiry alerts (30/7/1 days, R2) are not built.** `refreshTokenExpiresAt` is stored now. Adding an alert kind is a contracts change.
- **No in-app alert for data requests or overdue ones.** They are audit and log only, because there's no `privacy_request` alert kind in contracts `ALERT_KINDS` (architect). The owner currently learns of a data request from the audit log and the `privacy_requests` table. There's also no UI or procedure to answer or close one (out of scope).
- **Redaction limits:**
  - It covers the order ids Shopify sends. We store no Shopify customer id or searchable email, so a `customers/redact` with no order ids redacts nothing (it is still recorded).
  - Rendered artwork files that contain personalization text, and label PDFs, are not deleted. The 30-day `purgePiiObjects` sweep removes labels.
- **The unknown-buyer label "Shopify customer" is stored in `buyer_pii.name`** because the contract requires a string. Making `buyerName` nullable is an architect decision.
- **`shopify.app.toml` has placeholders** (`client_id`, `api.invai.example` / `app.invai.example`) until the app is registered (OI-2).
- **Order-edit line removals** only reach the importer through `currentQuantity`. `updateExisting` still updates only totals (B-99's import half belongs to backend-engineer, orders).
- **`channels.health` decrypts credentials for each API connection** to read the degraded state. That's fine at current sizes.

## Blocked by other owners
- None blocking.
- Process note: I once swept T-3-4's in-progress `sync.ts` hunks into my unpushed commit, because they landed between my diff check and the commit. I immediately amended my own unpushed commit (`cc35a08`) to hold only my 7-line hunk; their work stayed in the working tree untouched. After that, every `sync.ts`/`jobs.ts` commit was staged by replaying only my edits onto HEAD's blob. Worth a lesson: for shared files, stage from HEAD plus your own edits, never from the working tree.

## Processes and data
- Stopped: API (pid 54079, port 3110) and worker (pid for the copy). `lsof -iTCP:3110` is empty.
- Dropped: `invai_t31_copy` and `invai_test_t31`. Valkey db 1 flushed. Worktree `../invai-backend-t31` removed.
- Shared dev DB: untouched. It was already at migration 0014 when I copied it; I didn't migrate it.
