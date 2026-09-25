# Review of T-4-3 (round 1)

- Reviewer: backend-engineer (inventory) on Opus
- Author: floor-engineer on Opus
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| Same setup as the primary review: `invai-backend` HEAD (`bdffe6f`, T-4-1 merged) on `:3192` against `invai_r43_copy` (`createdb -T invai` + `pnpm db:migrate`, "up to date"), `REDIS_URL=…/10`, floor on `:5192` | up |
| Read `invai-floor-r43-review/src/stations/receiving/{api.ts,logic.ts,PoReceive.tsx,SheetReceive.tsx,StockCount.tsx}` against the `inventory.*`/`production.sheets.*` contract (`invai-contracts/src/contract/inventory.ts`, `src/schemas/inventory.ts`) | request/response shapes match the contract exactly (`ReceiveInput`, `CountInput`, `PurchaseOrder`, `GangSheet`); no off-contract fields or endpoints |
| Created and submitted `PO-20260925-01` (owner API), received it partially then fully from the floor UI | `purchase_order_receipts`: exactly 2 rows total (1 partial + 1 complete), matching `lines[]`/`receivedQty` math; final PO status `received` |
| Over-receipt: `curl POST .../purchase-orders/{id}/receive` with `qty: 999` against a line with 5 outstanding | server independently refuses with `400 BAD_REQUEST` ("receiving 999 but only 5 outstanding") — confirms the client's "warn, cap, and let the server be the real gate" design in the report is not just an assumption |
| Vendor transfer: scanned a real `transfers.id` on printed sheet `2026-09-22 #23`, marked received | `gang_sheets.status` → `received`; `transfers`/`order_items` for that sheet: every non-cancelled, non-already-pressed/packed item moved `on_sheet → transfer_in` (SQL-verified), matching decision 0002's item-state model |
| `curl` a replay of `production.sheets.{id}.received` on the now-`received` sheet | `409 INVALID_TRANSITION` — the endpoint itself has no idempotency key; a retry is distinguishable only by this error code (pre-existing backend behavior, not introduced by this card) |
| Stock count: scanned a blank with `on_hand=17`, counted 1, saved | `StockCount.tsx` sends `{ locationId, lines: [{blankVariantId, counted}], note: null }` — exactly `CountInput`'s shape, no `idempotencyKey` field (there isn't one in the contract) |
| Checked `CountInput`/`ReceiveInput` schemas directly (`invai-contracts/src/schemas/inventory.ts`) | confirmed: `ReceiveInput` carries `idempotencyKey`; `CountInput` does not; `sheets.markReceived`'s input (`{id}`) has none either |
| True offline drop-and-replay (Vite proxy pointed at an unreachable port), partial PO receipt while unreachable, then reconnect | server had 0 receipt rows while queued, exactly 1 after the outbox's automatic replay — reused the same client-generated `idempotencyKey`, no duplicate `purchase_order_receipts` row and no double stock movement |

## Acceptance criteria (inventory-relevant subset)
| # | Met? | Evidence |
|---|---|---|
| 1. PO receiving, idempotent submission, over-receipt handling | Yes | Live partial/complete/double-tap/over-receipt tests above, all matching server-side enforcement independently confirmed by direct `curl` |
| 2. Vendor transfers, correct sheet-state gating | Yes | Only `printed`/`shipped` sheets offered (`ARRIVING_SHEET_STATES`), matches `SHEET_TRANSITIONS`; live receive + replay-returns-`INVALID_TRANSITION` check above |
| 3. Stock count via `inventory.count`, difference shown before submit | Yes | Live count above; payload shape matches contract; the UI's diff (`countRows`) is computed from the same `stock.get`/`list` data the server holds, so what the receiver sees before saving matches what will be compared server-side |

## Blocking findings
None.

## Judgment on the flagged `inventory.count` replay risk
The author's own report flags: *"A count replayed offline has no idempotency key on the server ... if stock moved between the count and the replay, the replay corrects to the old (stale) count."* I confirmed this is accurate and reproduced the underlying fact directly: `CountInput` (`invai-contracts/src/schemas/inventory.ts:91-95`) has no `idempotencyKey` field, and `inventory.count`/`sheets.markReceived` are not covered by `ReceiveInput`'s idempotency convention.

**Severity: low, non-blocking for this card.**
- `inventory.count` sets an *absolute* counted value per line, not a delta — so a true duplicate send (same request executed twice back-to-back) is naturally idempotent in the common case; the risk is narrower than "any replay double-counts." It only bites when a **second, independent** stock-affecting event (another receipt, another count, a press/scrap) lands on the *same blank variant* in the exact window between the original send and a **stale retry** of an already-applied-but-unacknowledged request — a genuinely rare interleaving for a manual floor count, which happens at most a few times a day per shop.
- This is a contract-level gap (`invai-contracts/src/schemas/inventory.ts`), not something `floor-engineer` can fix from inside `invai-floor`'s owned paths. The wave's own build log already tracks it as a to-do for the architect and the inventory module owner ("architect + inventory owner"), and the author correctly did not invent an off-contract field to route around it.
- The same is true for `sheets.markReceived`: no key, but a replay on an already-received sheet fails closed with `INVALID_TRANSITION` rather than silently re-applying — the outbox's pre-existing `isAlreadyApplied` heuristic (not part of this diff) treats that 409 as "done," which is the right call for a genuine replay and only mis-fires in the edge case the author already named (a sheet cancelled between the original send and the replay). That's a narrow, pre-existing gap in T-4-2's outbox code, not new to T-4-3.

**Recommendation (non-blocking, for the follow-up already logged):** add an optional `idempotencyKey` to `CountInput` and a required one to `sheets.markReceived`'s input, following the same convention as `ReceiveInput`. This is an `invai-contracts` change plus a small backend handler change — out of `invai-floor`'s owned paths, so it belongs to the architect/inventory-owner follow-up already recorded in `wave.md`, not a blocker for this card.

## Checks
- [x] Only owned paths changed (confirmed in the primary review's `diff --stat`)
- [x] Nothing outside scope; no off-contract inventory/production endpoints invented
- [x] Idempotency: `ReceiveInput`'s key verified live under a real dropped connection with zero duplication; the `inventory.count`/`sheets.markReceived` gaps are pre-existing, correctly flagged, and judged non-blocking above
- [x] Money/units: quantities only (no cents involved in this card); `Qty` types used consistently with the contract
- [x] Decisions recorded where needed — none new required for this card

## Optional notes (not blocking)
- Worth confirming with the architect whether `CountInput.idempotencyKey` and a `sheets.markReceived` key land in the same wave the offline queue gets audited again (T-4-2's Problems Sheet), since both touch the same outbox replay path.
