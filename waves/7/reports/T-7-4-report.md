# T-7-4 report: Orders: ship-by holidays, staleness, per-line cancel (B-26, B-12)

**Status:** built and committed. It is not pushed and still needs review (architect and qa-engineer).
**Commit:** `invai-backend` `6caf8db`. No `invai-contracts` change was needed: `sourceUpdatedAt` and `channel_edit_after_press` were already in `7bb2bb1`.

## What changed
| File | Change |
|---|---|
| `modules/orders/shipby.ts` | Adds `USPS_HOLIDAYS` for 2026–2027, with sources. Business days skip Sundays, Saturdays (unless `shipsSaturday`) and postal holidays. A day that isn't a business day counts from the next one. A ship-by the channel sends is kept as is. |
| `modules/orders/import.ts` | `Run` passes `timeZone`, `processingDays`, `shipDays`, the matcher and the source through the import. Changes: the re-import ship-by fix, the staleness check, `applyLineEdits`, `holdFromChannel`, and `routeUnits`, which is taken out of `createOrder`. `ImportResult` gains `stale`, `held` and `staleOrderIds`. `Options` gains `holds`. |
| `modules/orders/service.ts` | `holdOrder` takes an optional `channelSignal`, which is stored on the transitions. `FLAG_SEVERITY` gains `channel_edit_after_press: "warn"`. |
| `modules/channels/sync.ts` (only my hunk, on top of T-7-2's) | When a webhook delivery is stale, the raw payload archive is no longer overwritten (`staleOrderIds`). |
| Tests | Adds `orders/import-edits.test.ts` (10 cases). `orders/shipby.test.ts` gains 3 cases. |

## Acceptance criteria
1. **Postal holidays: done.** Holiday dates:
   - 2026: 1/1, 1/19, 2/16, 5/25, 6/19, 7/4 (Sat), 9/7, 10/12, 11/11, 11/26, 12/25.
   - 2027: 1/1, 1/18, 2/15, 5/31, 6/19 (Sat), 7/5 (Mon, for Sun 7/4), 9/6, 10/11, 11/11, 11/25, 12/25 (Sat).

   Sources:
   - USPS ELM 518.1 (https://about.usps.com/manuals/elm/html/elmc5_008.htm) lists the 11 holidays. It also says a Sunday holiday is observed on Monday, and a Saturday holiday moves to Friday.
   - The USPS 2026 list is at https://about.usps.com/newsroom/events/.
   - USPS's July 4, 2026 release (https://about.usps.com/newsroom/national-releases/2026/0626-usps-will-be-closed-in-observance-of-independence-day-july-4.htm) says: "Post Offices will be open, and deliveries will occur as normal on Friday, July 3", and closed Saturday. So the ELM's Friday rule is for employee pay only. The table closes the Saturday itself.

   USPS hasn't published a 2027 list yet, so 2027 is worked out from those rules. A code comment says to extend the table before 2028.

   For weekends, the company setting `settings.shipsSaturday` defaults to off. Nothing sets it yet (see gaps).

   The Etsy CSV has no ship-by column, so the connection's `processingDays` applies. A test covers 5 processing days that span Thanksgiving.
2. **Re-import bug: done.** `updateExisting` now recomputes the channel's ship-by through `computeShipBy`: a date-only value becomes the end of that day in the shop's time zone. It then compares that result with the stored one. Re-importing the same `ship_by` is now a skip. A changed date still updates the order and its units.
3. **Staleness: done, with one deliberate difference from the card's wording.** A payload whose `sourceUpdatedAt` is older than **the newest channel timestamp already applied** is ignored. That timestamp is stored in `data.sourceUpdatedAt` on the `order.imported` and `order.synced` audit rows.
   - I didn't compare against `orders.updated_at`, because that column changes on every floor scan (the status recompute uses `$onUpdate`). Comparing against it would permanently drop a real channel edit that arrived after a scan, and the poller would re-read it and drop it again.
   - A test shows this: a later local change doesn't block a channel edit that is newer than the last one applied.
   - Payloads with a null `sourceUpdatedAt` (CSV) skip the check.
4. **Per-line cancel: done on the orders side.**
   - When a line's quantity drops, or an API/webhook payload no longer lists a line, only those units are cancelled. The cheapest go first: unrouted, then ready, then on a sheet (the transfer is scrapped), and pressed units never.
   - Units the shop cancelled itself count toward the channel's quantity, so they are never re-added or cancelled twice.
   - A line missing from a **CSV** cancels nothing, because a bad row can drop a line.
   - `holdFromChannel` does two things: a buyer cancel request becomes a `buyer_request` hold, and `channel_on_hold` becomes an `other` hold with the note "TikTok has this order on hold…". Each signal holds an order once, so a hold the shop released isn't put back.
   - **Blocked on a grant:** nothing produces the `holds` signal yet. See the cross-card section.
5. **Line edits: done.**
   - A quantity increase or a new line adds units, routes them through the SKU rules, and holds them if the order is on hold.
   - A SKU or personalization change is applied in place on unrouted units (`imported`/`needs_mapping`), which then map again. A routed unit is replaced: the new unit is inserted first, then the old one is cancelled, so the order is never all-cancelled in between. The exception is a SKU-only change that resolves to the same design and blank, which is applied in place.
   - Pressed, packed, shipped and delivered units (including held units whose held-from state is one of those) are never changed. They get the flag `channel_edit_after_press` instead. This happens once per channel edit (keyed through the audit row), so a flag the shop cleared isn't raised again.
6. **Tests: done.** Every case above has a test.

## Verification
- `tsc --noEmit` passes. `biome check .` is clean.
- The full backend suite ran on `invai_test_t74`: **79 files, 564 tests passed**. `orders` alone: 5 files and 27 tests, plus the 2 new or extended files with 15 tests.
- **Webhook replay** on the DB copy `invai_t74_copy` (migrated). A script sent signed Shopify deliveries through `processWebhook` for the seeded shop:
  1. `orders/create` (updated 17:05, 3+1 units): 4 units `ready`.
  2. `orders/updated` (updated 17:01, note changed): ignored. The note stayed null and the raw archive key didn't change.
  3. `orders/updated` (17:10, `current_quantity` 3→1): units 1.2 and 1.3 `cancelled`; 1.1 and 2.1 still `ready`; the order is still `new`.
  4. The same delivery replayed: no change to the units.
- Cleanup: the test DB and the copy are dropped, Redis /14 is flushed, and the temporary replay script is deleted. No API or worker was left running.
- Docker (OrbStack) was down when I started. I opened OrbStack and the tech lead restarted it. All my runs were after the restart.

## Cross-card notes and grant requests
- **Needs a grant (integrations-engineer / T-7-1 area) to finish the holds part of AC4:** add `holds?: ChannelHold[]` to `ParsedCsv` and `FetchOrdersResult`. The TikTok parser (`csv/parse.ts` `parseTiktok`) should push `{channelOrderId, signal: "channel_on_hold"}` when `Order Status` matches `/on.?hold/`. Shopify or other adapters should push `buyer_cancel_request` wherever the channel exposes one. Then `sync.ts` passes `holds` into `importNormalizedOrders` (about 3 lines at the CSV, poll and webhook call sites). The orders side is done and tested.
- **Walmart CSV (integrations):** one cancelled line (`Status`) still cancels the whole PO and drops it from `orders`. It should instead leave the line out, or send it with a lower quantity. Then the new per-line logic handles it. For CSV, a lower quantity is the safe path, since a missing line is ignored.
- **`sourceUpdatedAt` per adapter (T-7-1):** only Shopify sets it today. CSV sources are null, which is correct: no check.
- **Unstable CSV line ids:** TikTok and Shopify-CSV line ids include the row number. Matching falls back to SKU, so reordered exports don't look like edits.

## Known gaps
- `settings.shipsSaturday` is read but no UI or contract sets it yet (web or settings owner). The default is Mon–Fri, which matches the old behavior.
- The staleness timestamp only moves when a sync applies a change. If a newer payload with no changes arrives before an older one that differs, the older one would still apply. That needs a state to go X→Y→X, so it's rare. A proper `orders.channel_updated_at` column (it needs a `db/schema` grant) would remove this and replace the audit lookup.
- The holiday table covers 2026–2027 only.
- The import does more work per existing order now: one extra units query, plus the audit and transition lookups only when relevant. That's fine at current CSV sizes.

## Round 1 (grants from the tech lead): `invai-backend` `0e16314`
- **Staleness moved to a column.** Added `orders.channel_updated_at`, with migration `0022_orders_channel_updated_at` in the same commit.
  - Import sets it from `sourceUpdatedAt`. `updateExisting` ignores an older payload.
  - The column advances even when a re-read changes nothing, which closes the X→Y→X gap from "Known gaps".
  - The audit-row lookup is gone.
- **Channel signals.** `ParsedCsv` and `FetchOrdersResult` gain `holds` and `cancelledLines`. `sync.ts` passes both into the import, for the CSV path (its final step) and the poll path.
  - TikTok: an `Order Status` of "On hold" becomes a `channel_on_hold` hold, and the order still imports.
  - Amazon: `is-buyer-requested-cancellation` = true becomes a `buyer_cancel_request` hold. The report includes this column; our fixture doesn't, so the test adds it.
  - Shopify: no buyer-cancel-request signal is wired. I didn't find one in the order data the adapter reads, and I'm not certain the Admin API has none. Etsy, Walmart and the generic CSV have none.
- **Walmart line cancels.** A cancelled line now becomes a `cancelledLines` entry, and the rest of the PO imports. The PO is cancelled only when no line is left. The orders-side `cancelLineFromChannel` cancels that line's open units and flags pressed ones. It is idempotent.
- **Tests.**
  - New parser tests: the Walmart line cancel and the all-lines case; TikTok On hold and the Amazon buyer cancel.
  - An orders test for line cancels.
  - An assertion on `channel_updated_at`.
  - Full backend suite: **79 files, 567 tests passed**. Lint is clean.
- **Not mine:** `tsc` currently fails only in `modules/shipping/service.ts:1841` (`isNull` is not imported). That file has another agent's uncommitted work in progress. None of my files have type errors.
- `shipsSaturday` still has no UI (a logged follow-up). The test DB is dropped and Redis /14 is flushed.
