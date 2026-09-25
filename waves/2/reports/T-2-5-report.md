# Report: T-2-5 Crash-safe labels, tracking push outside transactions, cancel voids labels
Author: backend-engineer (shipping) on Opus 5.5

Commits on `main` in `invai-backend` (not pushed):
- **Part 1, `26cda9b`:** crash-safe `buyLabel`, lock-free `rateOrder`, carrier read-back, and migration `0012_shipping_crash_safe`.
- **Part 2, `e399249`:** `pushTracking` outside transactions; cancel and hold after a label; crash-safe void; CSV channels ship on the carrier scan; the paid-action gate on buys.

## Intake
- Card: T-2-5. Owner: backend-engineer (shipping). Scope: `product/scope.md#mvp-in` items 1 and 7, plus bug (money).
- Owned paths: `modules/shipping/**`, `integrations/carriers/**`, the cancel and hold functions in `modules/orders/service.ts`, `pushTrackingForShipment` in `modules/channels/service.ts`, and `db/schema/shipping.ts` with its migration.
- Risk flags and co-reviewers: payments and marketplace-policy (security-reviewer), migration (backend-foundation), golden path (qa-engineer).

## Built
### Part 1 (`26cda9b`)
**`buyLabel(ctx, input)`** (`modules/shipping/service.ts`) uses three steps, like wave 1's `submitPo`:
1. **Transaction 1** locks the shipment and writes the intent: status `buying`, `selectedRateId` and `buyAttemptedAt`. Then it commits.
2. **The carrier call** runs with no transaction open.
3. **Transaction 2** records the label, the shipment and the events.

**Idempotency key.** Our side is the shipment id, backed by a new partial unique index `labels_one_purchased_per_shipment` on `(company_id, shipment_id) WHERE status='purchased'`. The carrier side is the carrier shipment created at rating time; EasyPost gets our shipment id as `reference`.

**Retries:**
- A retry of a `buying` shipment calls `lookup` first (read-back) and only buys if the carrier has nothing.
- While a call may still be in flight (`BUY_IN_FLIGHT_MS` = 2 min), a retry gets CONFLICT.
- A retry with a different rate while a buy is pending gets CONFLICT.

**Failures:**
- A clear refusal returns the shipment to `rated`.
- An unknown outcome (timeout, 5xx or a non-carrier error) stays `buying` with `buyAttemptedAt = null`. The caller gets UPSTREAM_FAILED: "Buy again to check; you won't be charged twice."
- If transaction 2 fails after the carrier sold the label, the in-flight mark is cleared, so the next call reads back at once.

**`rateOrder(ctx, input)`** runs transaction 1 (lock the order, checks, pick or create the shipment), then the carrier call, then transaction 2 (store quotes only if the shipment is still `pending` or `rated`). No lock is held during the carrier call. It now refuses an order that already has a live label or a buy or void in flight. Before this change, re-rating a labeled order could lead to a second label.

**`batchBuy`** calls these directly and no longer wraps them in one transaction.

**Carriers** (`integrations/carriers`):
- New `CarrierAdapter.lookup` for read-back.
- `CarrierError.outcome` (`not_done` or `unknown`).
- `VoidResult.pending`.
- A fixed label key `labelObjectKey(companyId, carrierShipmentId)`, so repeats overwrite one object.
- EasyPost: `GET /shipments/{id}` read-back; 5xx and network errors are `unknown`; the label download moved into `storeLabel`.
- Mock: keeps its "carrier records" as a JSON file next to the PDF in the bucket, so a read-back after a process crash sees earlier purchases. Buying the same carrier shipment twice is refused, as at EasyPost.

**Schema** (`db/schema/shipping.ts`, migration `0012`):
- New columns `buy_attempted_at`, `void_attempted_at` and `push_attempted_at`.
- Partial unique index on `labels`.
- Internal states `buying` and `voiding` on shipments, and `pushing` on the tracking push. They are text enums with no DDL. The API shows them as `rated`, `labeled` and `pending` until the contract has them (same approach as `submitting` on POs).

### Part 2 (`e399249`)
**`pushTracking`** (shipping):
- Transaction 1 locks the shipment. It skips `pushed` and `not_required`, and returns `busy` while a push or a buy/void is in flight (`PUSH_IN_FLIGHT_MS` = 60 s).
- It checks the units at push time:
  - Cancelled units are left out.
  - If every unit is cancelled, the push becomes `not_required`.
  - Any unit `on_hold` returns `held`: the push stays `pending` with the error "On hold: …".
- Then it sets `pushing` and commits. The channel call runs with no transaction open, and transaction 2 records the result.
- Items move to `shipped` only on a real `pushed`.
- If transaction 2 fails, the result is `retry` and the in-flight mark is cleared.
- Repeating a push is safe. Shopify fulfills only lines that still have quantity remaining, so a retry doesn't notify the buyer again. A test covers a commit failure followed by a retry: the buyer is notified once.

**`pushTrackingForShipment(ctx, shipmentId, orderItemIds)`** (channels): does its reads in a short `withTenant`, calls the adapter with no transaction, then writes the audit. My only changes in that file are this function and adding `withTenant` to the `db/client` import. T-2-1 had already committed its `connect` hunks, so the diff held only mine.

**Cancel and hold** (`orders/service.ts` `cancelOrder` and `holdOrder`) call the new `shipping.guardShipmentsForItems(tx, ctx, itemIds, "cancel" | "channel_cancel" | "hold")` before the units move. It locks the shipments that carry those units.
- **Cancel:**
  - Refused when tracking was pushed, with "…already sent to the channel, so it can't be cancelled here. Cancel or refund it on the channel."
  - Refused while a push is in flight.
  - Otherwise it blocks the push (`not_required`, "Cancelled: the label is being voided") and drops stale quotes on `rated` shipments.
  - A cancel from the channel is never refused.
  - `cancelOrder` also refuses units that are already shipped or delivered, with a plain-language message. Before, it failed with a raw INVALID_TRANSITION.
- **Hold:** refused only while a push is in flight. The push itself waits for the release.

**New jobs** (`shipping/jobs.ts`):
- `shipping.voidCancelledLabels`, on `order.cancelled`: voids every not-yet-shipped label of the order.
  - It waits while a buy is in flight.
  - For a buy with an unknown outcome, it resolves it with `buyLabel(..., { readBackOnly: true })`, which never buys.
  - It retries on CONFLICT or UPSTREAM_FAILED, and writes a `label.void_failed` audit when the carrier refuses.
- `shipping.pushReleased`, on `order.released`: pushes the held-back tracking.

A buy that lands after a cancel records the label with the push blocked, and the job then voids it.

**`voidShipment(ctx, input)`** is crash-safe:
- Transaction 1 sets status `voiding`, then the carrier refund runs with no transaction open, then transaction 2 records the result.
- A retry reads `refundStatus` back first.
- It is allowed while the units are packed and no tracking was sent.
- EasyPost's `submitted` now leaves the label at `refund_pending` (the mock refunds at once).

**CSV-only channels** (Etsy, Amazon, TikTok and Walmart while pending approval, plus generic CSV):
- A `manual` or `not_required` push no longer ships the units.
- `buyLabel` no longer ships them either.
- Units ship on the carrier's first scan (`markInTransit`, and `markDelivered` as a fallback). So `voidShipment` works for them until the scan.

**Billing gate** (tech lead's request): `assertPaidActionAllowed` runs at the start of a new buy (not when resuming one the carrier may already have charged) and at the start of `batchBuy`. EMAIL_NOT_VERIFIED is already enforced by T-2-3's gate at the router.

**Functions other modules may call:** `guardShipmentsForItems`, `voidCancelledLabels`, `pushReleasedShipments`, `voidShipment(ctx, input)`, `buyLabel(ctx, input, opts)` and `rateOrder(ctx, input)`. The new signatures take no `tx`.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 `buyLabel` crash-safe | Yes | `label-safety.test.ts`: intent committed and row unlocked during the buy; buy twice = 1 call; commit failure after charge → retry reads back, `buy` calls = 1, 1 label; in flight → CONFLICT, then read-back with 0 buys; stale → bought once; clear refusal → `rated`; unknown → read back; different rate → CONFLICT. Real run below. |
| 2 no carrier call under a row lock | Yes | Test: during `rate()`, `FOR UPDATE NOWAIT` on the order and the shipment succeeds; a buy that starts meanwhile isn't overwritten. |
| 3 push outside the transaction, idempotent, checks state and holds | Yes | `push-void.test.ts`: `NOWAIT` lock during the push; second push skipped (1 call); commit failure → retry notifies once; busy while in flight; cancelled units left out; all cancelled → never pushed; hold → `held`, then release → pushed. |
| 4 cancel or hold after a label | Yes | Tests: cancel → push blocked, job voids (`refund_pending`), rerun is a no-op; refused after push ("already shipped") and during push ("being sent"); cancel during the buy → label recorded unpushed, then voided; hold refused while pushing. Real run below. |
| 5 CSV channels void | Yes | Test and real run: Etsy push → `not_required` with the manual message, units stay `packed`, void works; after the carrier scan, units are `shipped` and void → VOID_REJECTED. |
| 6 tests | Yes | 32 new tests across both files (buyLabel, rateOrder, voidShipment, pushTracking, batchBuy gate). |

## Checks I ran
| Repo | Command | Result |
|---|---|---|
| invai-backend | `pnpm typecheck` | clean |
| invai-backend | `pnpm lint` | "Checked 211 files … No fixes applied." |
| invai-backend | `pnpm test` (TEST_DATABASE_URL `…/invai_test_t25`, REDIS `/5`) | 45 files, 318 tests passed |
| invai-backend | `pnpm build` | "Build success" |
| invai-web | `E2E_API=1 E2E_API_URL=http://localhost:3250 pnpm e2e e2e/api-golden-path.spec.ts` | 13 passed, on a freshly seeded `invai_t25_copy` |

Part 1 was also checked on its own in a clean worktree of HEAD plus only the part 1 files (tsc, biome, vitest and tsup). All passed except `rls-coverage`, which then failed on T-2-3's `two_factors` table and was fixed in `240a19e`.

## Exercised for real
Setup: API on :3250 and a worker (not in watch mode) on `invai_t25_copy`, imaging on :8250, mock carrier, owner login.

**Crash after the carrier sold (Shopify #1549).** I added a DB trigger on the copy that raises on `buying → labeled`.
- Buy #1 → HTTP 500. Row: `buying | buy_attempted_at null | no tracking`, 0 label rows. The API shows `rated`. The log says "carrier sold the label but saving it failed", and imaging had made 1 label.
- I dropped the trigger. Buy #2 → `labeled 9400006503724885719651 694`. Buy #3 (double click) → same tracking.
- DB: 1 label (`purchased`). Carrier label calls in total: **1**.

**Push.** The worker pushed #1526 and #1549 once each ("mock shopify fulfillment" appears twice). Both are `pushed`, attempts 1, items `shipped`.

**Cancel after push.** Cancelling the unit on #1526 → 409 "This unit already shipped: its tracking was sent to the channel … Cancel or refund it on the channel."

**Cancel a labeled Amazon order (CSV-only).**
- After the buy, the push became `not_required` with the manual-upload message, and the items stayed `packed,packed`.
- Cancel → 200. The job voided the label: shipment `voided | not_required | "Cancelled: the label is being voided"`, items `cancelled,cancelled`, label `voided`.
- Audit: `label.purchased`, then `label.voided: order cancelled`. No push reached any channel.

**Etsy CSV void.**
- The label was bought and the push was `not_required`, with items `packed`.
- `POST /shipping/shipments/{id}/void` → 200 `voided`, and the unit is still `packed`. A repeat void → 200 (idempotent).
- A second Etsy label, after the mock carrier scan: `in_transit`, units `shipped`. Void → 409 VOID_REJECTED "a in_transit shipment can't be voided".

**Refused role.** `presser@` calling void → 403 FORBIDDEN (`shipping.buy`).

## Decisions
- **Internal states** (`buying`, `voiding`, `pushing`) are hidden behind API mapping instead of a contract change, the same approach as `submitting` on POs. The architect may add them to the contract later.
- **Partial cancel voids the whole label.** The package contents and weight change, so the remaining units go back to the ship queue to be re-rated.
- **Channel cancels are never refused**, because the channel is authoritative. If a push is in flight, the void job retries, and it writes an audit if it finally can't void.
- **Push retry-safety relies on the adapter.** Shopify is inherently safe (it fulfills only remaining quantity). A future Etsy API adapter must add a read-back before `createReceiptShipment`, because each call emails the buyer.

## Known gaps and follow-ups
- **Golden path step 9 (qa-engineer, `invai-web/e2e/api-golden-path.spec.ts`):** it checks that the Etsy item is `shipped` right after the push resolves. Etsy units now ship on the carrier's scan, so the step passes only when the mock scan is quick. I ran it with `MOCK_CARRIER_TRANSIT_HOURS=0`; with the default of 2 hours it would fail. Please make it poll the item state (or the shipment reaching `in_transit`), and consider `MOCK_CARRIER_TRANSIT_HOURS=0` for the E2E stack.
- **Real EasyPost with no tracker webhooks (B-66, wave 3):** CSV-channel units only ship when `markInTransit` is called. Until B-66, with a real key they stay `packed` after the label. The mock is unaffected. B-66 should call `markInTransit`, and a USPS SCAN form (manifest, B-25) could ship them too.
- **Stuck intents:** nothing sweeps a `buying` or `pushing` row that no one retries (a `raiseAlert` needs an alert kind in the contract). The UI shows them as `rated` and `pending`, and a retry resolves them safely.
- **Label download safety:** the EasyPost label download still follows redirects without a size cap (research 12 G8). Not in scope here.
- **Web:** the void confirmation dialog (B-67, web side) is not built.
- **Docs:** `src/modules/README.md:79` still shows the old `svc.pushTracking(tx, …)` example. That file isn't mine, so docs-writer should update it.

## Blocked by other owners
- None. Two notes:
  - Valkey has 16 DBs, so the assigned `REDIS_URL …/25` fails. I used `/5` (per the tech lead) and `/13` for one early test run.
  - `docker exec local-postgres-1 createdb …` stands in for `createdb`, which isn't installed on the host.

## Processes and data
- Stopped: my API (:3250), my worker, imaging on :8250, and the clean worktree `/tmp/t25wt`. I killed only PIDs I had started.
- Dropped the `invai_t25_copy` database.
- `invai-backend/seed-output.json` was restored from a backup after the copy seed.
- Shared dev DB untouched. Someone else had already migrated it to 0012.
