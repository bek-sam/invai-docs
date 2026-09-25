# Review of T-3-1 (round 1)

- Reviewer: security-reviewer on Opus 5.5
- Author: integrations-engineer on Opus 5.5
- Verdict: **approve**

## Evidence I re-ran

Same setup as the primary review: worktree `../invai-backend-r31` at `00c35e4`, test DB `invai_test_r31`, `REDIS_URL=redis://localhost:6379/10`.

| Command | Result |
|---|---|
| `node_modules/.bin/tsc --noEmit && node_modules/.bin/biome check . && node_modules/.bin/vitest run && node_modules/.bin/tsup` | all clean (55 files / 397 tests, build succeeds) |
| Live: API port 3191 + worker against DB copy `invai_r31_copy`, mock Shopify | bad-signature 401, header/body shop-mismatch ignored, redact/shop-redact verified end to end (see primary review for the transcript) |
| `grep -rn '\.for("update")' src/modules src/integrations` | every lock in the diff's area (`service.ts:77` token refresh, `service.ts:568` daily re-check, `sync.ts:665` OAuth state) locks exactly one `channelConnections` row by id, no multi-row or cross-table lock while held — no lock-ordering deadlock path found |
| `pnpm test src/db/rls-coverage.test.ts src/api/authz.test.ts` (via `vitest run` of the whole suite, which includes these) | green — `privacy_requests` is a `company_id` table with RLS, so RLS coverage picks it up automatically |

## Threat model (webhooks, pii, auth flags)

**Signature verification** (`api/webhooks.ts`): HMAC verified on the raw body (`verifyShopifyHmac`, `timingSafeEqual`) **before** any dedupe insert or parse. Bad signature → 401, nothing written. Confirmed live (401, no `webhook_deliveries` row, no order).

**Dedupe**: `webhook_deliveries` unique on `(channel, deliveryId)`, `X-Shopify-Webhook-Id` used as the id — matches R4. For compliance topics the delivery is recorded **before** processing and removed on failure (`processWebhookNow`'s catch, `sync.ts:507-520`), so a genuine failure gets Shopify's retry, but a successful-then-crashed response can't double-process past the removed record on the crash path — the DB writes inside `handlePrivacyRequest` are the actual idempotency boundary for the case that matters (partial completion), not just the delivery row. Confirmed live: sending the same `deliveryId` twice returned `duplicate:true` the second time without a second `handlePrivacyRequest` call (checked via log output).

**Shop from the signed body**: `parseCompliance` (`shopify/common.ts:285-306`) takes `shop_domain` from the JSON body, and explicitly refuses (returns `kind: "ignored"`) when a present `X-Shopify-Shop-Domain` header names a **different** shop than the body — defends against a header-spoofing attempt while still tolerating a missing header (mock/local doesn't always send it). Confirmed live: sending a mismatched header vs. body shop returned `handled:false`, reason "shop domain missing or mismatched," and nothing was touched.

**Redact scope and completeness**: `targetOrders` scopes strictly to the connections whose `externalShopId` matches the signed shop (`handlePrivacyRequest`, `service.ts`/`privacy/service.ts:58-68`), so a redact/data-request for shop A can't touch shop B's orders even if a channel order id collides numerically — this is enforced by the `connectionId` intersection, not by trusting the payload's ids alone. `redactOrders` deletes `buyer_pii` rows, nulls `buyer_note`/`buyer_ref`/`raw_payload_key`, and clears `answer`/`fileUrl` on every personalization entry that had one. Storage delete happens **before** the DB update (comment at `privacy/service.ts:144`: "if a delete fails the webhook is retried while the keys are still known") — correct ordering for retry-safety. Confirmed live for both a single-order `customers/redact` and a full `shop/redact` (100/100 orders, 98/98 `buyer_pii` rows cleared).

**Gap (non-blocking, pre-existing infrastructure, not introduced here):** label PDFs and rendered artwork containing the buyer's address are not part of the synchronous redact path; they're caught by the existing `purgePiiObjects` sweep, whose 30-day cutoff is measured from the S3 object's own age, not from when the redact/shop-redact request was received. In the common case (label bought within days of the order) this still lands well inside Shopify's 30-day window, but it isn't request-driven, so a pathological case — a label created the same day as the redact request, with the daily sweep's own offset — could in theory land a day or two past a strict 30-days-from-request reading. This predates T-3-1 (the sweep is `orders/jobs.ts`, not touched by this card) and the author's report discloses it explicitly as a known gap; I'd log it in `security/v1-review.md` as a Low finding (own it there rather than block this card) with the fix being "redact enqueues an immediate purge of that order's PII objects" as a small follow-up, not a redesign of the sweep.

**Token refresh and rotation**: `refreshConnectionToken` (`service.ts:67-120`) takes `SELECT … FOR UPDATE` inside `withTenant`, re-reads the row after acquiring the lock (so a second concurrent caller sees the already-refreshed token and returns early instead of spending the refresh token twice — R1's exact requirement), and stores the rotated `{accessToken, refreshToken, expiresAt, refreshTokenExpiresAt}` via `encryptJson` in the same update as the row that held the lock — atomic. The concurrency test (`shopify.test.ts` "two workers at once spend the refresh token once") exercises this against real Postgres transactions (not mocked), and passed. Deadlock surface: every `.for("update")` call I found in this diff's touched files locks a single row by primary key and does no further cross-table locking while holding it — no ordering conflict.

**`changeFromQuantity` retry**: reviewed `inventory.ts` line by line. `changeFromQuantity` is set to the `available` value read immediately before the write, `@idempotent(key:)` is present on every `inventorySetQuantities` call, `CHANGE_FROM_QUANTITY_STALE` triggers exactly one re-read-and-retry with a fresh key (`retryKey`), and a second mismatch is marked `failed` rather than looping. No infinite-retry or hot-loop risk.

## Blocking findings

None.

## Checks
- [x] Only owned paths changed (see primary review's `git diff --stat`)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; scan script (`scan-test-weakening.sh`) shows no weakening in T-3-1's own test files
- [x] Tenancy: `privacy_requests` RLS + `company_id` index + system-write-only revoke; redact/shop-redact tenant-scoped via `connectionId`; row locks single-row, no deadlock path found
- [x] Idempotency: webhook dedupe on `X-Shopify-Webhook-Id`, `@idempotent` key on inventory writes, unique `(company_id, channel, delivery_id)` on `privacy_requests`
- [x] Decisions recorded (shop-from-body, degraded-as-health-state, system-write-only privacy table)

## Optional notes (not blocking)
1. Log the label-PDF/rendered-artwork retention-timing gap above as a Low finding in `security/v1-review.md` with an owner and a follow-up card, rather than letting it live only in this review file and the author's report.
2. Throttle state being per-process (not the shared Redis bucket `suppliers/ratelimit.ts` uses) is fine for a single worker today; flag it again before running more than one Shopify-syncing worker process (author already tracked this as B-20).
