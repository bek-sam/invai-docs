# Report: T-4-1 Pack-complete, `wrong_style`, idempotent QC/bin (backend)
Author: backend-engineer (production), Claude Opus 5.5

## Summary
- **Commits** (invai-backend, on `main`, not pushed):
  - `c839e93`: the typecheck fix. The backend is green against the contract stubs `c181abf` / `e427b8f`.
  - `d45e155`: `production.packOrder`, the override, and the override-aware `recomputeOrderStatus`.
- **AC 4 (explicit `idempotencyKey` on QC and bins) is not built.** The contract doesn't have the field; details under "Blocked by other owners".
- **The "pack anyway" path shipped, but its orders can't get a label yet.** The shipping module only queues and labels orders whose units are *all* packed. The PM's review requires that I state explicitly that a `packed_partial`-equivalent path shipped.

## Round 2: tech lead decisions (commit `bdffe6f`)
- **AC 4 is accepted as met by state-based idempotency.** No contract change:
  - A replayed QC pass returns success; a replayed QC fail returns the same reprint (`production.test.ts:287,342`).
  - A double bin assign or release leaves one row and one state (pack.test.ts).
- **Split shipment: not feasible, so I took the "no" path.** `shipments.order_item_ids` does link a shipment to specific units. A second shipment for the remaining units doesn't work, for three reasons:
  - `buyLabel` allows one live label per order (`shipping/service.ts:549-560`, "This order already has a label. Void it first").
  - `shippableOrderIds` drops any order that has a live shipment (`:414`).
  - `orderPacks.itemIds` also includes already-shipped units (`:239`), so a second label would cover them again.
  Fixing this goes beyond the three granted hunks, so I didn't touch shipping.
- **What changed in `bdffe6f`:** "pack anyway" now means "hand to lead".
  - The override (still `production.override`, owner or admin) records who, why and the missing units in `orders.pack_override`, and writes the audit entries `order.pack_override` and `order.handed_to_lead`.
  - It releases the tote and returns `packed: false` with `missing[]` and `override`.
  - It adds no pack scans and **doesn't force `ready_to_ship`**: the status stays what the units say.
  - `recomputeOrderStatus` goes back to plain `deriveOrderStatus`. It only clears `pack_override` once every open unit is packed or later. A normal `packOrder` then packs the order.
- **Checks at `bdffe6f`:**
  - typecheck and lint pass; full suite: 63 files, 447 tests passed.
  - curl on a fresh `invai_t41_copy` (port 3110):
    - As admin, the hand-off returned `200 packed:false` with `missing[]` and reason "Transfer lost".
    - Tote `L41` was released; the status stayed `in_production`; the order is not in the ship queue.
    - Audit entries: `order.pack_override` and `order.handed_to_lead`.
- **Superseded:** the round-1 text below about forcing `ready_to_ship`, and "Blocked by other owners" items 1 and 2, are replaced by this section.
- **Contract comments are now stale.** They still describe the forced `ready_to_ship` (`PackOrderResult.override`, `Order.packOverride`, wave.md §4). The architect should update the wording; the shape is unchanged. The floor (T-4-4) should label the button "Hand to lead" and treat `packed:false` + `override` as handed over.

## Intake
Card: T-4-1. Owner: backend-engineer (production). Scope: `scope.md#mvp-in` item 5, plus decision 0002.

Owned paths:
- `invai-backend/src/modules/production/**` (includes the module's schema file `src/db/schema/production.ts`, per the role file)
- Named grants: `src/db/schema/orders.ts` (`packOverride`), `src/modules/orders/state-machine.ts` (`recomputeOrderStatus`), and `src/db/schema/tenancy.ts:228`
- The user named `orders/service.ts:137` as inside the typecheck fix.

Risk flag: floor-correctness. Co-reviewers: architect and qa-engineer, plus **backend-foundation for migrations 0015 and 0016 and the grants**.

## Built
- **Typecheck fix (`c839e93`):**
  - `STATION_KINDS` gains `receiving`. `stations.kind` is `enumText`: a plain `text` column with no CHECK or pg enum. `db:generate` produced no SQL for the new value, so it needs no migration.
  - New nullable column `orders.pack_override jsonb`. Migration `0015_orders_pack_override.sql` is one `ALTER TABLE … ADD COLUMN` with no default, so it doesn't rewrite the table. It maps to `Order.packOverride` in `toOrder`.
  - The receiving station has no unit queue: `queue` returns empty. A transfer scan there with no explicit action returns `wrong_station` and records nothing.
- **`production.packOrder` (`d45e155`, `modules/production/floor.ts`):**
  - Locks the order row. A non-cancelled unit counts as done if it is `packed`, `shipped` or `delivered`. Otherwise the call throws `PACK_INCOMPLETE` (409) with `data.missing[]` (unit id and state).
  - On success it:
    - adds a `pack` scan for any packed unit that doesn't have one, so the order leaves the pack queue;
    - releases the order's tote (with no tote it's a no-op);
    - writes an `order.packed` audit entry;
    - publishes `queue.changed` and `order.updated`.
  - It refuses (`CONFLICT`) an order that is `on_hold` or fully cancelled.
- **Override ("pack anyway"):**
  - `input.override` without `production.override` gets `FORBIDDEN`. The check is in the handler, per wave.md §3; owner and admin have it via `SHOP_ALL`.
  - With units missing, it:
    - sets `orders.pack_override` to `{reason, by, byName, at, missingItemIds}`;
    - writes an `order.pack_override` audit entry with who, why and the missing units;
    - forces the status to `ready_to_ship`.
  - `missing[]` is always returned alongside `override`.
  - An override sent when nothing is missing is ignored (`override: null`).
- **`recomputeOrderStatus` (`orders/state-machine.ts`)** now goes through the pure function `orderStatusWithOverride(states, hasOverride)`:
  - `deriveOrderStatus` still decides.
  - With an override, the pre-ready statuses (`new`, `needs_attention`, `in_production`) become `ready_to_ship`. `on_hold`, `cancelled` and the shipping statuses still win.
  - The override clears to `null` once every open unit is `packed`, `shipped` or `delivered`, or once none is left open.
- **Idempotency:**
  - New tenant table `floor_requests`: RLS, index `company_id`-first, unique `(company_id, kind, idempotency_key)`. Migration `0016_production_floor_requests.sql`.
  - It stores the first *effective* result, which a replay returns verbatim.
  - The same key with a different `orderId` or override reason is `CONFLICT`. A concurrent insert collision rolls the whole call back.
- **`sheets.markReceived`:** no backend change was needed. `permissionsFor` reads the contract's `ROLE_PERMISSIONS`, so `receiver` and `office` get `production.receive` from the architect's stub.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 packOrder refuse / pack / replay / no tote | Yes | pack.test.ts "packs a complete order…" and "refuses a partial order…"; curl below |
| 2 Override: permission, audit, `packOverride`, `ready_to_ship`, `missing[]` kept, self-clearing | Yes (backend). **Order can't be shipped yet**, see Blocked | pack.test.ts "override: …"; curl below |
| 3 `wrong_style` regression | Yes | `matcher.test.ts` still passes; curl press scan → `wrong_style` |
| 4 QC/bin idempotent on explicit `idempotencyKey` | **No, blocked by the contract** | The existing state-based replay is tested (QC: `production.test.ts:287,342`; bins double tap: pack.test.ts). No explicit key is possible. |
| 5 Receiver marks sheets received via `production.receive`; office still can; nothing broader | Yes | pack.test.ts router test; curl below |
| 6 Tests cover the above | Yes (except 4) | 12 new tests |

## Checks I ran
All checks ran in the main tree. Nobody else had uncommitted backend work, and the tree was clean at each commit.

| Repo | Command | Result |
|---|---|---|
| backend @ `c839e93` | `pnpm typecheck` / `pnpm lint` / `vitest run` (`invai_test_t41`) | clean / 242 files clean / 62 files, 435 tests passed |
| backend @ `d45e155` | `pnpm typecheck` / `biome check .` / `vitest run` / `pnpm build` | clean / 243 files clean / 63 files, 447 tests passed / build success |
| backend | `pnpm db:generate` for 0015 | only `ALTER TABLE "orders" ADD COLUMN "pack_override" jsonb;` (nothing for `STATION_KINDS`) |

## Exercised for real
Setup:
- API on :3110 via `tsx src/api/server.ts` against `invai_t41_copy` (migrated to 0016), Redis db 1.
- User sessions for `packer@`, `admin@`, `presser@`, `receiver@` and `office@desertbloom.test`.

Results:
- **Partial order refused, then packed:**
  - Order `113-2268745-1003835` had 3 pressed units. After QC passing 1 of them, `POST /production/pack-order` as packer returned `409 PACK_INCOMPLETE` (`defined: true`), with `missing` = the 2 pressed units.
  - I QC-passed the other 2 and assigned tote `T41`. The same call and key then returned `200 {packed:true, missing:[], override:null}`.
  - The replay returned the identical body.
  - DB after: status `ready_to_ship`; tote `T41` released (`order_id` null); 1 `floor_requests` row; 3 pack scans; 1 `order.packed` audit row.
- **Override:**
  - Order `3104010545` had 1 unit packed and 2 pressed.
  - As packer: `403 FORBIDDEN` "Only an owner or admin can pack an order anyway".
  - As admin: `200` with `missing` = 2 units and `override` = `{reason:"Transfer lost, ship the rest", byName:"Alex Admin", …}`.
  - The replay returned the same body. The same key with a different reason returned `409 CONFLICT`.
  - `GET /orders/:id` shows `status: ready_to_ship` and `packOverride`.
  - After that I QC-*failed* one missing unit (it moved to `ready`). The status is still `ready_to_ship` and the override is kept, so it isn't clobbered.
  - Audit: `order.pack_override` and `order.packed`.
- **Shipping gap, confirmed:** `GET /shipping/queue` as admin lists the normally packed order but **not** the override order.
- **`wrong_style`:** a press scan as presser with a Bella+Canvas 3001 label on a Comfort Colors 1717 transfer returned `ok:false`, `mismatch:"wrong_style"`, "Wrong style: needs Comfort Colors 1717 Crimson M, scanned Bella+Canvas 3001 Black S".
- **Receiving station:** `queue?station=receiving` returns `items: []`. A scan with `station:"receiving"` returns `wrong_station`, and the item stays `transfer_in`.
- **`sheets.markReceived`:**
  - `receiver` on a printed sheet: `200`, status `received`, items moved to `transfer_in`.
  - `office` on another printed sheet: `200`.
  - `presser`: `403` "Missing permission production.receive".
  - `receiver` on `sheets.cancel`: `403`.

## Decisions
- **Idempotency lives in a new `floor_requests` table, not in `scans`.** `today/service.ts:114-117` counts `scans` rows with `count(*)`, so an order-level scan row would inflate "pack done today". The table is generic (`kind`) so B-27's QC/bin keys can use it once the contract carries them. backend-foundation please co-review. I read it as within my role's "module schema file + migration", but it is a new table rather than the named `packOverride` column.
- **Only effective calls are stored.** A refused `PACK_INCOMPLETE` has no effect, so a retry with the same key re-evaluates. The tablet can therefore keep one key per "Mark packed" intent and succeed once the last unit is packed. The contract comment ("a retry returns the original result") is honored for every call that changed anything.
- **`packOrder` adds a `pack` scan** for packed units the packer didn't scan one by one. The pack queue treats an order as finished when every packed unit has a pack scan, so without these rows a packed order stayed in the queue.
- **The override check runs whenever `override` is sent,** even if nothing turns out missing (wave.md §3's literal rule). An override is also refused on an order `on_hold`, because hold would win the status anyway.
- A decision addendum for "ship short" (0002 consequences, or a new 0010) is for the tech lead/PM to file, per the PM review.

## Known gaps and follow-ups
- **Override-packed orders can't be shipped** (see Blocked, item 1). Until that's fixed, "pack anyway" marks the order and releases the tote, but no label can be bought.
- **Replaying `sheets.markReceived` returns `409 INVALID_TRANSITION`,** not the sheet. The floor's `isAlreadyApplied` heuristic treats that as already done, which is fine for now. A real key belongs with B-27.
- **For floor-engineer (T-4-2/T-4-4):** once QC and bins get real keys (after the contract change), the client heuristic at `invai-floor/src/outbox/outbox.ts:126-129` can be narrowed. That is not this wave.

## Blocked by other owners
1. **Shipping, owned by backend-engineer (shipping):**
   - `invai-backend/src/modules/shipping/service.ts:425` (`shippableOrderIds`: `bool_and(state in ('packed','cancelled'))`) and `:562` / `:743` (`if (!pack?.allPacked) throw orderNotPacked()`) exclude and refuse orders with an override.
   - Suggested change: also accept `orders.pack_override is not null and bool_or(state = 'packed')`, and label only the packed units, which `orderPacks.itemIds` already lists.
   - This contradicts the PM review's "override-packed orders still enter the normal shipping/label queue", so it needs a card, or the tech lead decides.
2. **Contracts, owned by the architect (AC 4, B-27):**
   - `QcInput` (`invai-contracts/src/schemas/production.ts:280`) and `bins.assign` / `bins.release` (`src/contract/production.ts:141,152`) have no `idempotencyKey`.
   - oRPC strips unknown fields, so the backend can't accept one.
   - Suggested change: `idempotencyKey: z.string().min(8).max(128).optional()` on all three. The backend then stores results in `floor_requests` (kinds `qc`, `bin_assign`, `bin_release`).
   - Today's behavior is already safe for double taps without it:
     - A replayed QC pass returns success.
     - A replayed QC fail returns the same reprint.
     - A double assign or release leaves one bin row and one state.
3. **DB copies made before `c839e93`** (for example `invai_t42_copy` and `invai_t43_copy`) need `pnpm db:migrate`. Otherwise every orders query fails on the missing `pack_override` column.

## Functions other modules may call
- `packOrder` (production service).
- `orderStatusWithOverride(states, hasOverride)` (orders/state-machine, pure).

## Processes and data
- **Stopped:** my API on :3110 (the port is free). No worker was started.
- **Dropped:** `invai_t41_copy` and `invai_test_t41`. Valkey db 1 flushed. Scratch folder `.t41/` removed.
- **No worktree was used.** I was the only one editing the backend, and the checks ran on the tree at each commit.
- **Shared dev DB `invai`:** I applied migrations 0015 and 0016 with `pnpm db:migrate`. Both are additive, and the main tree's code needs `pack_override`. No reset or seed. `seed-output.json` is untouched.
