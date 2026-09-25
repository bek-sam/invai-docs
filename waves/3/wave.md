# Wave 3: integrations hardened

- Dates: 2026-09-25 →
- Goal (user outcome):
  - A shop connected to Shopify gets every paid order, refund and cancel, and never gets unpaid ones.
  - Real tracking updates flow in from EasyPost.
  - Stock levels push back to Shopify listings.
  - Big imports and batch label runs never hang a request.
- Plan reviewed by: product-manager (`reviews/plan-product-manager-r1.md`), architect (`reviews/plan-architect-r1.md`)

## Cards
| Card | Owner | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|
| T-3-1 Shopify adapter complete | integrations-engineer | reviewer + security-reviewer, compliance-officer | webhooks, pii, marketplace-policy | planned |
| T-3-2 EasyPost live tracking | integrations-engineer | reviewer + security-reviewer | webhooks | planned |
| T-3-3 Listings and availability push | backend-engineer (inventory) | reviewer + backend-foundation, architect | migration, marketplace-policy | planned (starts after T-3-1) |
| T-3-4 Heavy work to jobs | backend-foundation | reviewer + qa-engineer | floor-correctness | planned |

Only 3 builders run at once (lesson: usage limit). T-3-3 starts when T-3-1 lands, because it needs T-3-1's fixed `setAvailability`.

Removed from the roadmap's wave 3: generic B-05 (token refresh for Amazon, Walmart and TikTok). Those adapters are pending approval, so their refresh goes in with each adapter. Shopify's expiring tokens are in T-3-1.

## Contract stubs for async results (T-3-4), designed by the architect r1 review
Both changes must stay **additive** (contract rule: new optional fields, new enum values at the end). Web consumers checked: `invai-web/src/routes/_app/settings/channels.tsx:260` (`client.channels.importCsv`, reads the return value as the finished report) and `invai-web/src/routes/_app/shipping.tsx:127-136` (`client.shipping.batchBuy`, reads `res.results`/`res.labeled` synchronously to print labels). Neither file is in any wave-3 owned-paths list.

- **`ImportReport` (`invai-contracts/src/schemas/channels.ts`):** append `"queued"` and `"running"` to `status` (currently `"completed"|"failed"`); add `jobId: Id.nullable().optional()`. Backend behavior: files at or under a small inline threshold (**300 rows** — comfortably above typical small-shop exports, comfortably below the "3,000-row" and "5,000-row" cases the card verifies) still run to completion inside the request, in short chunked sub-transactions, and return `status: "completed"|"failed"` with `jobId: null` exactly as today — **this is the sync-compatible wrapper, and it means `settings/channels.tsx` needs no change.** Files over the threshold enqueue the job and return `status: "queued"`, `jobId` set, zero counts, immediately. `renderReport` in `channels.tsx` will show a queued report as all-zero rather than crash — acceptable for now; wire a poll (`channels.imports` or `jobs.get`) into that screen as part of wave 5's B-85, not this wave.
- **`BatchBuyResult` (`invai-contracts/src/schemas/shipping.ts`):** the card's own verification step — "kill the worker mid-batch, restart it, and check there are no duplicate labels" on a 20-label batch — only makes sense if 20 labels genuinely run as an async job (an inline synchronous handler can't be interrupted by killing the worker process). So **do not** add a size-based sync wrapper for `batchBuy` the way `importCsv` gets one; it must always enqueue. Add `status: z.enum(["completed", "queued"]).default("completed")` to `BatchBuyResult` (additive); on `queued`, `results: []`, `labeled: 0`, `failed: 0`, `totalPostage: 0`, `jobId` set. This **does** break `shipping.tsx`'s current assumption that `res.results` is final. T-3-4 has a narrow, named grant to edit exactly `invai-web/src/routes/_app/shipping.tsx` (the `batch` mutation only, lines ~127-145) the same day, to poll `job.progress` / re-fetch the queue instead of trusting the immediate response, per CLAUDE.md's "a breaking contract change must be fixed in every consumer the same day" rule. Get a web-engineer co-review on that one file's diff even though web-engineer isn't otherwise on this card.

## Parallel work rules (read all of them)
- **Test DB:** `invai_test_t3<k>` (`TEST_DATABASE_URL=postgres://invai_app:invai@localhost:5432/invai_test_t3<k>`, `TEST_MIGRATION_DATABASE_URL=postgres://invai:invai@localhost:5432/invai_test_t3<k>`). Drop it at the end.
- **API port, Redis and DB copy:**
  - API port `31<k>0` (web `51<k>0`).
  - `REDIS_URL=redis://localhost:6379/<k>` (Valkey has 16 DBs, 0–15).
  - Worker: `MOCK_CARRIER_TRANSIT_HOURS=0.001`.
  - DB copy: `docker exec local-postgres-1 createdb -U invai -T invai invai_t3<k>_copy`, dropped at the end.
- **Commits:** commit only your paths, with `git commit -m ... -- <paths>`, then `git show --stat HEAD`. For a shared file, commit only your hunks (`git apply --cached`). Never commit someone else's hunk.
- **Never:** run `pnpm install`, `db:reset` the shared dev DB, use `pkill`/`killall`, or push.
- **Worktrees:** place them next to the repos (`../<repo>-<card>`), not in `/tmp`. Run `node_modules/.bin` tools directly, and remove the worktree at the end.
- **Migrations:** `pnpm db:generate --name <module>_<change>`. On a journal collision, tell the tech lead; don't regenerate a migration someone else may have applied.
- **Disk:** keep logs small, and delete screenshots you don't keep.

## Agreed interfaces
- `ChannelAdapter.setAvailability(conn, items: { listingVariantId, available }[])`: T-3-1 fixes the Shopify implementation (`changeFromQuantity` plus `@idempotent`). T-3-3 calls it.
- **Corrected (r1 review):** the real signatures are `markInTransit(tx, ctx, shipmentId)` and `markDelivered(tx, ctx, shipmentId, at = new Date())` (`modules/shipping/service.ts:1690,1717`) — not `(shipmentId, at)` as first written. `markInTransit` has **no `at` param**. T-3-2: if the tracker event's own timestamp matters (out-of-order detection needs it), add `at` to `markInTransit` too (additive, default `new Date()`), don't invent a second entry point.
- Webhook routes: T-3-1 owns `api/webhooks.ts`. T-3-2 adds its carrier route in a new `api/webhooks-carriers.ts`, mounted with one line in `api/app.ts` (granted to T-3-2). Mount `/webhooks/easypost` as its own top-level `app.route()` (not nested under the existing `/webhooks` mount) so it can't be shadowed by `webhooks.post("/:channel")`; "easypost" is not a `Channel` enum value so the generic route 404s it anyway, but keep the routes visibly separate. Extend the existing `noMockWebhooksInProd` guard pattern (`api/app.ts:122-128`) to `/webhooks/easypost` too: EasyPost's mock provider will sign with a fixed dev secret exactly like mock Shopify does, and prod must reject it.
- **EasyPost HMAC (new, T-3-2):** no verification code or secret exists yet (checked `integrations/carriers/**`, `env.ts`). Follow the Shopify pattern (`integrations/channels/shopify/common.ts:24-43`): add `EASYPOST_WEBHOOK_SECRET: secret(z.string()).optional()` to `env.ts` (normally backend-foundation's path — T-3-2 has a narrow, named grant for this one line only, coordinate with the T-3-4 owner since they're also touching backend-foundation territory this wave); a `MOCK_EASYPOST_WEBHOOK_SECRET` constant and `easypostWebhookSecret()` fallback; `verifyEasypostSignature(headers, body, secret)` using `timingSafeEqual` over HMAC-SHA256 of the raw body, header `x-hmac-signature` (EasyPost sends `hmac-sha256-hex=<hex>`; compare the hex part).
- **Carrier webhook dedupe table (new, T-3-2), following decision 0009's pattern exactly:** `carrier_webhook_events` — `id`, nullable `companyId` (set once routed to a shipment's company; FK `companies.id` cascade), `provider` (enum, just `["easypost"]` for now), `eventId` (text, EasyPost's `id`, e.g. `evt_...`), `status` (`received|processed|ignored|failed`, default `received`), `receivedAt` (default now), `processedAt`, `detail` (text, no PII). Unique index on `(provider, eventId)`; index on `receivedAt`; index on `(companyId, receivedAt)`; RLS `tenantPolicy("carrier_webhook_events")`, `.enableRLS()`. Migration revokes insert/update/delete from `invai_app` (system-only writes), same as migration 0007 did for `webhook_deliveries`. Purge rows older than 7 days in the same daily job as `purgeWebhookDeliveries`, or a sibling one.

## Integration gate
- [ ] `df -h /` above 5 GB
- [ ] Fresh reset, migrate, seed (imaging up, worker stopped)
- [ ] `run-golden-path` passes (API, browser, floor)
- [ ] Builds pass
- [ ] Per-card test DBs and worktrees removed
- [ ] Pushed to `main`

## Retro
- What slipped:
- Lessons added:
