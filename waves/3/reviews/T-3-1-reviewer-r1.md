# Review of T-3-1 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: integrations-engineer on Opus 5.5
- Verdict: **approve**

## Evidence I re-ran

Setup: worktree `../invai-backend-r31` at `00c35e4` (HEAD of the 8-commit range `563287b..00c35e4`), `node_modules` symlinked from `invai-backend`, test DB `invai_test_r31`, `REDIS_URL=redis://localhost:6379/10`.

| Command | Result |
|---|---|
| `node_modules/.bin/tsc --noEmit` | clean, no errors |
| `node_modules/.bin/biome check .` | "Checked 232 files … No fixes applied." |
| `node_modules/.bin/tsup` (build) | "Build success" (server.js, index.js) |
| `node_modules/.bin/vitest run` (test DB `invai_test_r31`) | **55 files, 397 tests passed** — matches the author's report exactly |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend-r31 e399249` (base = parent of `563287b`) | hits found, all in T-3-2's files (`easypost/*`, `webhooks-carriers.test.ts`, `shipping/jobs.ts`/`.test.ts`) — none in T-3-1's own test files (`shopify/{auth,inventory,orders,subscriptions}.test.ts`, `modules/channels/shopify.test.ts`, `modules/privacy/service.test.ts`). `removed=0 added=305` assertions. |
| Live exercise: API port 3191 + worker, DB copy `invai_r31_copy` (migrated to 0014), mock Shopify, Redis db 10 | see below |

**Live run results** (own script signing `x-shopify-hmac-sha256` with the mock secret):
- `orders/create`, `financial_status: pending` → 200, `webhook_deliveries` row `ignored`, detail `"order … not paid (pending); skipped"`, no order created.
- `orders/create`, `financial_status: paid` (async, via the queue) → order imported by the worker with `buyer_pii` and `raw_payload_key` set.
- Bad HMAC → 401 `invalid signature`.
- `customers/redact` for that order (sent **after** waiting for the worker to finish the import — see note below) → 200 `handled:true`; DB shows `buyer_note`/`buyer_ref`/`raw_payload_key` null, 0 `buyer_pii` rows, `privacy_requests` row `completed` with `{"orders":1,"buyerPii":1,"rawPayloads":1,"personalizedItems":0}`.
- `shop/redact` on the seeded connection (100 orders, 98 with PII) → all 100 orders' PII cleared, `privacy_requests` counts `{"orders":100,"buyerPii":98,...}`.
- `disconnect` (called directly against the seeded mock connection) → status `disconnected`, credentials cleared, audited.

**Investigation note (not a bug):** my first pass at exercising `customers/redact` fired the redact webhook immediately after the `orders/create` webhook, without waiting for the worker to process the queued import job, and found 0 matching orders both times. I traced this all the way through `parseShopifyWebhook`, `handlePrivacyRequest`, and direct DB queries under both `withSystem` and `withTenant` before realizing the order simply didn't exist yet when the redact call ran — a race in my test script, not the product. Re-run with a 3s wait behaved correctly (see above). Worth remembering for whoever runs T-3-1's own "for real" verification bullet: `orders/create` is queued, so a redact test needs to wait for the worker.

## Acceptance criteria

| # | Met? | Evidence |
|---|---|---|
| 1 Paid orders only; poll by `updated_at` | Yes | `paymentDecision()` (`shopify/common.ts:73-86`) shared by both REST webhooks and GraphQL poll (`orders.ts:231`); live run above; `orders.test.ts` |
| 2 Line items beyond 100 | Yes | `orders.test.ts` pagination test; code review of `orders.ts` |
| 3 Throttle + PII null | Yes | `client.ts` throttle wait; `shipToOf()` returns null on any missing address field (`common.ts:108-127`), never empty strings |
| 4 Subscription failure degraded; disconnect unsubscribes/revokes | Yes | `subscriptions.ts`, `service.ts:475-528`; live disconnect run above |
| 5 Compliance webhooks verified/deduped/synchronous/TOML | Yes | `api/webhooks.ts` (verify → dedupe → inline handle, delivery removed on failure so Shopify retries); `shopify.app.toml`; live runs above |
| 6 `changeFromQuantity` + `@idempotent`, one retry | Yes | `inventory.ts` `isStale`/retry logic reviewed line by line; 6 tests pass |
| 7 Expiring tokens: refresh, rotate, flag | Yes | `service.ts:67-120` row lock (`FOR UPDATE`), rotated pair stored via `encryptJson`; concurrent-refresh test (`shopify.test.ts`) passes for real against Postgres |
| 8 Poller skips; no spam | Yes | `pollableConnections`/`pollFailing` (`sync.ts`) code review; `sync_failed` emitted only when `!pollFailing(conn)` using the **pre-failure** row state |
| 9 Fetch-mocked tests | Yes | present and green |

## Blocking findings

None.

## Checks
- [x] Only owned paths changed — `git diff --stat` across all 8 commits touches only `integrations/channels/shopify/**`, `integrations/channels/{index,types}.ts`, `api/webhooks.ts`, `modules/channels/{sync,jobs,service}.ts`, `modules/privacy/**` (+ `db/schema/{index,privacy}.ts` + migration 0014), `shopify.app.toml`, and tests next to these files. Nothing else.
- [x] Nothing outside scope
- [x] Tests exercise the behavior; scan script found no weakening in T-3-1's files; `removed=0` assertions
- [x] Tenancy: `privacy_requests` has `company_id`, RLS tenant policy, `company_id`-leading indexes, and `REVOKE INSERT/UPDATE/DELETE FROM invai_app` (system-write-only, decision 0009's pattern). Redact/shop-redact scoped by `connectionId` (tenant-safe). Idempotency: `@idempotent` key on inventory writes, unique `(company_id, channel, delivery_id)` on `privacy_requests`, `webhook_deliveries` dedupe on `X-Shopify-Webhook-Id`. Money/i18n: n/a to this card.
- [x] Decisions recorded where needed (author's report: "degraded" as health state not status, PARTIALLY_REFUNDED import, poll backoff fixed at 1h, shop from signed body, `privacy_requests` system-write-only)

## The `cc35a08` amend incident
Verified directly: `git show cc35a08 -- src/modules/channels/sync.ts` is a single 7-line hunk at `handleWebhook`'s `ignored`-event branch (adds a log line and passes through `event.reason`), nowhere near `importCsv` (line 78 onward in the current file). Checked every other T-3-1 commit that also touches `sync.ts` (`f9140dd`, `2a15725`) the same way — none touch the `importCsv` range. The incident described in the author's report (an accidental sweep of T-3-4's in-progress hunks, caught and fixed before commit) left no trace in the final history.

## Optional notes (not blocking)
1. **Label PDFs / rendered artwork are not part of the synchronous redact.** Confirmed: `redactOrders()` clears `buyer_pii`, `buyer_note`, `buyer_ref`, personalization answers, and the raw payload object, but label PDFs live under `{company}/label/` and are only removed by the general `purgePiiObjects` sweep (`orders/jobs.ts`), whose cutoff is 30 days from **the object's own age**, not from when the redact request arrived. In the realistic case (label bought within days of the order) this still lands inside Shopify's 30-day compliance window, but it's a shared clock with the routine retention sweep, not a redact-triggered deletion — already flagged by the author as a known gap. Worth a follow-up card to have redact purge PII objects for the affected orders immediately, same as it does for the raw payload.
2. **PARTIALLY_REFUNDED imports** (`paymentDecision`), beyond the card's literal "paid or partially_paid." Reasonable and documented ("it was paid, and the rest still ships"), but is a product-scope call, not just an engineering one — worth a one-line confirmation from the PM if it hasn't already happened at plan review.
3. Known, disclosed, non-blocking gaps from the author's report (throttle state per-process not shared Redis; no forced refresh on a mid-call 401; no alert kinds for privacy requests or expiring tokens) are all accurately described and appropriately deferred as follow-ups, not silent omissions.
