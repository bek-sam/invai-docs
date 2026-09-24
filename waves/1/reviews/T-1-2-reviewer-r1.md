# Review of T-1-2 (round 1)

- Reviewer: reviewer on Opus
- Author: integrations-engineer on Opus 5.5
- Verdict: **approve**

Commit reviewed: `90657ac` (invai-backend) only. Evidence re-run in a clean worktree at `90657ac` (parent
`34ed022`), test DB `invai_test_r12`, Redis DB 12, API/worker on port 3192. Worktree, DB and Redis DB cleaned up
afterward; no processes left running.

## Evidence I re-ran
| Command | Result |
|---|---|
| `tsc --noEmit` (clean worktree) | exit 0, no output |
| `biome check .` | `Checked 191 files in 137ms. No fixes applied.` |
| `TEST_DATABASE_URL=…/invai_test_r12 TEST_MIGRATION_DATABASE_URL=…/invai_test_r12 vitest run` | `Test Files 35 passed (35)`, `Tests 184 passed (184)` |
| `tsup` (`pnpm build`) | `ESM ⚡️ Build success` |
| `tsx src/db/migrate.ts` against `invai_test_r12` | `up to date` (both 0006 and 0007 applied cleanly) |
| `git -C invai-backend show --stat 90657ac` | 17 files, all inside T-1-2's owned paths |
| `.claude/skills/independent-review/scan-test-weakening.sh /tmp/r12 34ed022` (correct parent, not `293047b` which is a *later* commit) | 0 deleted test files, **0 assertions removed / 104 added**, no `.skip`/`.only`/loosened config; one "test-only branch" heuristic hit is a real prod-safety guard (see Checks) |
| API + worker on `PORT=3192`, `REDIS_URL=redis://localhost:6379/12`, against `invai_test_r12` | see "Exercised for real" |

## Exercised for real
Seeded one company with a `connected` Etsy connection (mock, shop `31920001`) and a `connected` Shopify
connection (mock, shop `r12-review.myshopify.com`) directly via `withSystem`.

| # | Request | Result |
|---|---|---|
| 1 | Etsy, valid signature, fresh `webhook-id` | `200 {"ok":true}`; worker processed it, order `9192001` imported with `total_cents` from the **fetched** receipt (payload carried no financial fields to trust in the first place — matches the "fetch by id" design; the module's own test proves a forged `grandtotal` is ignored) |
| 2 | Same `webhook-id`, fresh timestamp/signature (replay) | `200 {"ok":true,"duplicate":true}`, not re-enqueued |
| 3 | Etsy, garbage signature | `401 {"error":"invalid signature"}`, no row |
| 4 | Etsy, unsigned | `401`, no row |
| 5 | Shopify, signed, only `x-shopify-event-id` (no webhook id) | `400 {"error":"missing delivery id"}` |
| 6 | **5 concurrent** identical Etsy requests, same `webhook-id` | exactly 1× `{"ok":true}`, 4× `{"ok":true,"duplicate":true}`; DB shows exactly one row; the unique `(channel, delivery_id)` index serializes the race correctly (no double-import) |
| 7 | 3 concurrent Shopify OAuth callbacks, same `state` | exactly 1 succeeded (`connected=shopify`), 2 got "already used. Connect the store again." — the `SELECT … FOR UPDATE` burn in `consumeOAuthState` correctly serializes the race |
| 8 | Mock-signed Etsy webhook, `NODE_ENV=production`, `ALLOW_MOCKS=true` | `verifyWebhook` returned `false` — mock secrets are never accepted in prod |
| 9 | Cross-tenant read of `webhook_deliveries` (session `app.company_id` set to an unrelated id) | 0 rows returned; the owning tenant's session sees its own row; a direct `INSERT` as `invai_app` fails with `permission denied for table webhook_deliveries` (the revoke from migration 0007, confirmed live) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Verify before enqueue/write; 401 for bad/missing signature, nothing enqueued | yes | curl cases 3–4 above; `webhooks.test.ts` (enqueue spy never called, no row/job) |
| 2. Etsy: webhook-id dedupe, multi-signature, tolerance, fetch by id; per-channel mock flag | yes | curl case 1–2; `etsy/webhooks.test.ts`; `verifyEtsyWebhook` checks every `v1,` entry in constant time; `webhookAdapter()` now keys off `channelMocked(channel)` instead of always `env.mocks.shopify` |
| 3. Persisted `webhook_deliveries`, unique per channel+id, ≥30h retention + purge, replay → 200 no-op; tenancy explained | yes | schema + migrations read; curl case 2, 6; purge tests pass; see backend-foundation's file for the tenancy-design judgment |
| 4. Shopify dedupe via `X-Shopify-Webhook-Id`, missing header rejected (no random UUID fallback) | yes | curl case 5; code has no `randomUUID()` fallback anywhere in `webhookDeliveryId` |
| 5. OAuth state ≤10 min, single use | yes | curl case 7 (live race); `OAUTH_STATE_TTL_MS` = 10 min measured from `updatedAt`; unit tests for expiry pass |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git show --stat 90657ac`: `webhooks.ts`, `integrations/channels/**`,
  `db/schema/{index,webhooks}.ts`, the two migrations, `modules/channels/{sync,jobs}.ts`, tests — all listed
  in the card)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened — scan tool found 0 removed assertions and no skip/mock of
  the unit under test. Its one "test-only branch" hit
  (`src/integrations/channels/etsy/index.ts`: `if (env.isProd) throw upstream(...)`) is a genuine defense-in-depth
  production guard, not a test hack — read the surrounding code, it fires for real traffic too.
- [x] Tenancy (`withTenant`, RLS on new table), idempotency, money in cents (n/a here), en/es text (n/a,
  no user-facing strings added)
- [x] Decisions recorded — the tenancy-choice deviation from the architect's recommendation is written up in
  the author's report under "Decisions"; see backend-foundation's co-review for the judgment call

## Optional notes (not blocking)
1. **Shopify's mock adapter has no per-adapter `env.isProd` guard** (unlike Etsy's, which checks it twice —
   once in `verifyWebhook`/`fetchOrder`). Today this is safe because `sync.ts`'s `verifyWebhook()` is the only
   call site (`grep -rn "\.verifyWebhook(" src` outside tests confirms one hit), but a future direct caller of
   `webhookAdapter(channel).verifyWebhook()` would lose the guard. Cheap to add for consistency.
2. **A resend after a wrongly-"forgotten" delivery can leave a `webhook_deliveries` row stuck at `received`
   forever.** I reproduced this: after a delivery was fully processed, I deleted its row (simulating the
   `forgetWebhookDelivery` path firing on a false-negative enqueue failure) and resent the same delivery.
   The route accepted it as fresh (`200`, not `duplicate`) and called `job.enqueue()` again with the same
   deterministic `jobId`; BullMQ silently returned the pre-existing **completed** job without re-running the
   handler (`attemptsMade` and `processedOn` unchanged), so no double order-processing happened in this test.
   But the new row is never updated to `processed` (the worker never actually re-ran `finishWebhookDelivery`
   for it), so it sits at `received` until the 7-day purge — a minor, non-tenant-crossing data-quality gap in
   the per-connection health signal the table is meant to provide. See security-reviewer's file for the
   severity call on the theoretical double-processing edge this same mechanism guards against only as long as
   BullMQ still holds the original completed job (`removeOnComplete: {age: 24h, count: 5000}` in the
   read-only `lib/queues.ts`).
