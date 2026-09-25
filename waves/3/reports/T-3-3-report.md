# Report: T-3-3 Listings are recorded, and stock pushes back to channels
Author: backend-engineer (inventory) on Opus 5.5

```
Card: T-3-3  Owner: backend-engineer (inventory)  Scope ref: scope.md#mvp-in items 2, 6; decision 0003
Owned (edit): invai-backend/src/modules/inventory/**, modules/channels/sku.ts (listing writes), tests
Outside owned paths (flagged): src/db/seed/index.ts, 1 import + 3 lines (AC 1 "the seed creates them")
Risk flags -> co-reviewers: migration (none written), marketplace-policy -> backend-foundation, architect
```

## Commit (invai-backend, `main`, not pushed)
| SHA | What |
|---|---|
| `b8ac9d0` | Listings recorded and stock pushed to opted-in channels (7 files, all mine; `git show --stat HEAD` checked) |

**No migration.** The existing `listings` / `listing_variants` columns (RLS already on) hold everything. The idempotency key lives in the push job's data (see Decisions), so it needs no column.

## Built
- **Recording listings** (`channels/sku.ts`):
  - `recordListingsForItems(tx, companyId, itemIds)` upserts one `listings` row per (connection, `channelListingId`) and one `listing_variants` row per SKU on it, with the design, product, blank and price.
    - Order lines carry no variant id, so `channelVariantId` = the SKU.
    - Unmapped SKUs are recorded too, with a null blank; they are never pushed.
    - An existing mapping is only replaced by a non-null one (`coalesce`).
  - This runs from a new job `inventory.recordListings`, subscribed to `order.imported` and `item.mapped`. That covers import-time rule maps, manual maps, bulk apply and remaps, **without touching `orders/import.ts` or `orders/mapping.ts`** (T-3-4's files).
  - `createRule` / `updateRule` call `refreshListingMappings`: listing variants the saved rule matches move to its design and blank. Exact rules scan only their SKU.
  - A new or re-mapped variant emits `stock.availability_changed`, so it gets pushed.
  - `recordListingsForCompany` backfills from all of a company's orders; per SKU, the latest mapped unit wins. The seed calls it.
  - Read and write helpers for the push: `listPushTargets`, `lastPushedQuantities`, `markAvailabilityPushed`. Inventory never writes the channels tables directly any more.
- **Availability** (`inventory/availability.ts`):
  - The quantity is `pushQuantity(sum(stock_levels.available) over every location, quantityCap)`, where `available` = on hand minus reserved.
  - `planAvailability` keeps only connections that pass `canPushAvailability`: `status = connected`, `mode = api`, not csv, `pushAvailability` on, and the adapter not pending approval (decision 0003).
  - It keeps only variants whose quantity differs from `lastPushedQty`. A never-pushed variant goes once.
- **Pushing:**
  - `inventory.syncAvailability` (debounced) plans in a transaction. It then enqueues one `inventory.pushAvailability` job per connection, with a fresh `idempotencyKey` and the frozen updates, under job id `availability-push-<bucket>-<connectionId>`. A planner retry re-adds the same id, which BullMQ ignores.
  - `pushAvailability`:
    1. Short transaction: re-check the opt-in, and drop variants whose `lastPushedQty` changed since the plan.
    2. **No transaction:** call `adapter.setAvailability(conn, [{ listingVariantId, channelSku, available }], { idempotencyKey })`.
    3. Short transaction: store `lastPushedQty` for results with status `set`.
  - A thrown channel error fails the job, and the BullMQ retry sends the same frozen push under the same key.
  - `not_found` and `failed` variants stay unpushed and are logged, with ids only.
- **Debounce:** a fixed **30 s** wall-clock window per company. `availabilityBucket(now)` gives `bucket = floor(now/30000)+1` and `delay = bucket*30000 - now`, so every change in a window lands in one delayed job, which reads stock when it runs. Worst-case latency is 30 s.
- **Realtime:** `recordMovement` queues `stock.changed { blankVariantId, locationId, available }` and publishes it **after commit**. It sends one event per blank and location per transaction, with the last count. A rollback publishes nothing. This closes the `stock.changed` half of B-104.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Listings recorded on import and SKU map; seed creates them; RLS | Yes | `channels/listings.test.ts` (7 tests: import via `order.imported`, idempotent replay, manual map via `item.mapped`, rule save re-maps and queues a push, backfill, cross-tenant sees nothing). Fresh seed printed `[seed] listings {"listings":149,"variants":536}` |
| 2 Availability math + concrete debounce | Yes | `availability.test.ts`: on hand 10 + 5 (two locations) - 3 reserved = 12, capped 4; the 30 s window test uses fixed times (+5 s and +20 s give the same job id, delays 25 000 and 10 000; +30 s gives the next bucket) |
| 3 Opt-in only; idempotent; last value stored | Yes | Tests: off, csv, disconnected and on connections give pushes only for "on"; a toggle turned off after planning means no call; one push stores the value; the next window plans nothing; replaying a finished push makes no call; a failed call retried reuses the **same key**; `not_found` stays unpushed |
| 4 Realtime `stock.changed` | Yes | Tests: 2 events for 3 movements over 2 locations, only after commit, none on rollback. Seen live over SSE (below) |
| 5 Tests | Yes | 17 new tests |

## Checks I ran (HEAD `97651a0` + my changes, which is exactly `b8ac9d0`)
| Command | Result |
|---|---|
| `pnpm typecheck` | `tsc --noEmit`, no errors |
| `pnpm lint` | `Checked 240 files ... No fixes applied.` |
| `pnpm build` | `Build success` |
| `vitest run` (`invai_test_t33`, Redis db 3) | **61 files, 431 tests passed** |

## Exercised for real
The DB copy was `invai_t33_copy`, migrated, with the listings backfilled: 150 listings and 529 variants. The API and worker ran on :3130 with Redis db 3 and mock Shopify.
- `PATCH /api/v1/channels/{shopify}` as owner with `{"settings":{"pushAvailability":true}}` → 200, `pushAvailability: true`.
- **One push with the right number.** `POST /api/v1/inventory/adjust` +3 on G64000-SND-M (45 available) at 04:41:02 as owner:
  - The SSE stream received `stock.changed {"blankVariantId":"3aa37732…","locationId":"8652eaf3…","available":48}`.
  - The 04:41:30 window logged `availability planned {"bucket":59677043,"connections":1,"variants":7,"skippedConnections":3}`.
  - Then **one** `mock shopify availability` call carried the 7 SND-M listing SKUs, each `"available":48`, followed by `availability pushed {"pushed":7,"skipped":0,"notFound":0,"failed":0}`.
  - In the DB, `last_pushed_qty = 48` on those variants, and `sum(stock_levels.available) = 48`.
  - The 3 skipped connections are the csv-only Etsy, Amazon and TikTok ones.
  - When the worker started, the copy's older events had already triggered the first-ever push of all 139 mapped Shopify variants. That is expected, since none had been pushed before.
- **No push when nothing changed.** After a restart, I adjusted +1 then -1 inside one window at 12:38:44. The window logged `availability planned {"bucket":59677998,"connections":0,"variants":0,"skippedConnections":3}` with no `setAvailability` call and 0 SND-M pushes.
- Unrelated pushes also came through during the run, from reservations when the mock Shopify poll imported orders, for example `DB030-CC1717-IVY-S` → 1. That is the import → reserve → debounce → push path working.
- Refused case: `PATCH /api/v1/channels/{id}` as presser → 403 `FORBIDDEN` "Missing permission channels.manage for channels.update".
- Seed path: on a fresh `invai_t33_seed`, `migrate` then `db:seed` exited 0 and logged `listings {"listings":149,"variants":536}`.

## Decisions
- **The idempotency key is stored in the push job's data, not in a new column.** Each push is frozen: key, quantities and `fromQty`. A retry resends identical input under the same key, and a push whose variants were pushed since is dropped before the call. Shopify's compare-and-set covers the rest. This met "store the key with each push" without a migration.
- A key derived from the quantities was rejected: a later identical move (5→4, 4→5, 5→4) would reuse the key and be deduped by Shopify.
- **Listings are recorded by jobs on `order.imported` and `item.mapped`**, not inside the import transaction. This keeps my hands out of T-3-4's `orders/*` files and catches every mapping path. Recording is asynchronous but reliable, because it goes through the outbox. SKU-rule saves re-map synchronously inside `sku.ts`.
- **A whole-company plan per window**, not a per-variant queue. Only variants whose quantity differs from `lastPushedQty` are sent, so the effect is "affected variants only". The plan is also self-healing after a missed event.
- **Only `status = connected` connections push.** `error` and `pending` are skipped.

## Known gaps and follow-ups
- **Turning the opt-in on doesn't push right away.** The first push happens at the next stock change. `channels.updateConnection` (T-3-1's `service.ts`) could emit `stock.availability_changed` when `pushAvailability` flips on. The alternative is an hourly reconcile job. Owner: integrations-engineer, or a future inventory card.
- **`not_found` variants are re-sent in every window** until they exist on the channel. They are logged as warnings with no alert kind.
- There is no UI for `quantityCap` (B-86).
- Two concurrent pushes to one connection (only possible with retries overlapping a new window) could land out of order. The next change corrects it.
- The 139-variant first push is sent in one call; the adapter batches it by 250.

## Outside owned paths
- `src/db/seed/index.ts`: 1 import and a 3-line call to `recordListingsForCompany`, needed for AC 1 ("The seed creates them"). This belongs to backend-foundation, so please review that hunk.
- **Shared `invai-backend/seed-output.json` was overwritten.** It is gitignored, and my seed run on the throwaway `invai_t33_seed` DB rewrote it. It now names that DB's shop id, channel ids and station token, not the shared dev DB's. The dev DB's token is stored hashed, so the old value can't be restored. I didn't issue a new one, because that means writing to the shared dev DB. The integration gate's fresh reset and seed rewrites the file. Until then, anyone needing the dev station token should re-seed or issue one. Lesson for the log: run `db:seed` for a throwaway DB from a worktree, or back up `seed-output.json` first.

## Blocked by other owners
- None.

## Processes and data
- Stopped: my API and worker on :3130 (PIDs 58776/58777, then 65226/65227/65243/65244). `lsof -iTCP:3130` is empty. The api and worker on :3194 (`invai_r34_copy`, Redis db 11) belong to another agent; I left them running.
- Dropped: `invai_t33_copy`, `invai_t33_seed` and `invai_test_t33`. Redis db 3 flushed. Scratch folder `.t33/` removed. No worktree was used.
- Shared dev DB: untouched (read only as the copy template).
