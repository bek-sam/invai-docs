# Wave 4: the floor app is complete

- Goal (user outcome):
  - Packers can't ship an order with units missing.
  - A tablet that loses Wi-Fi never jams, loses or misattributes scans.
  - Receivers can check in blank POs and vendor transfers on the floor.
  - The Spanish floor UI has no English leaks.
- Plan reviewed by: product-manager (`reviews/plan-product-manager-r1.md`), architect (`reviews/plan-architect-r1.md`)

## Cards
| Card | Owner | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|
| T-4-1 Pack-complete, `wrong_style` and idempotent QC/bin (backend) | backend-engineer (production) | reviewer + architect, qa-engineer | floor-correctness | done |
| T-4-2 Offline queue that never jams | floor-engineer | reviewer + qa-engineer, security-reviewer | floor-correctness | done |
| T-4-3 Receiving station | floor-engineer | reviewer + product-designer, backend-engineer (inventory) | ui, floor-correctness | done |
| T-4-4 Pack station and floor polish | floor-engineer | reviewer + product-designer, qa-engineer | ui, floor-correctness | done |

Only 3 builders at once. T-4-4 starts after T-4-1 lands, because it uses T-4-1's procedure.

## Agreed interfaces (architect commits the stubs first)
- `production.packOrder({ orderId, idempotencyKey, override? })` — field renamed from the earlier `clientKey` to match the codebase's existing convention (`ReceiveInput.idempotencyKey`, `AvailabilityPush.idempotencyKey`). Exact shape in "Contract stubs (exact)" below.
- `STATIONS` gains `receiving`, and the floor role `receiver` gains a new `production.receive` permission (not a full `production.build`) to mark vendor sheets received. **Correction:** the backend's `STATION_KINDS` enum (`invai-backend/src/db/schema/tenancy.ts:228`, backend-foundation's file, currently `["pick","press","qc","pack"]`) must gain `"receiving"` too — it does not follow automatically from the contract's `STATIONS`. Grant below.
- **Correction: `wrong_style` is already shipped end to end**, not new work. Confirmed present in `MISMATCH_REASONS` (`invai-contracts/src/schemas/production.ts:199`), `matcher.ts:100` (`compareBlank`, distinguishes style from color/size), `matcher.test.ts:71` (passing test), and both `i18n/en.ts:118` / `i18n/es.ts:120`. B-33 should be marked done, not open. T-4-1 and T-4-4 keep a "no regression" check, not new scope — see card edits.
- Offline queue (floor-only): **correction** — `attempts` and `lastError` already exist on `OutboxEntry` (`invai-floor/src/outbox/db.ts:24-25`). Only `parkedAt: string | null` and a new `"parked"` value on `OutboxStatus` are new. After 5 failed attempts, or any 4xx other than 408/429, an entry is parked. Parked entries don't block the queue. **No Dexie version bump is required** — Dexie doesn't need an upgrade for a new unindexed property or a new value in an already-indexed field (`status` is already indexed). Code must treat `entry.parkedAt === undefined` (pre-existing rows) the same as `null`. If T-4-2 wants `parkedAt` indexed for the Problems Sheet query, bump to `version(3)` with `outbox: "++seq, &id, status, parkedAt"`; Dexie back-fills existing rows with an `undefined` index key, which is safe to query around (no upgrade function needed, no data loss).

## Hidden dependencies and grants (architect r1)
- **`orders.status` is stored, not purely derived at read time.** `deriveOrderStatus` (contracts) is pure over item states, but `recomputeOrderStatus` (`invai-backend/src/modules/orders/state-machine.ts:197`) writes it to the DB after *every* item transition. A `packOrder` override that sets `orders.status` directly would be silently overwritten the next time any unit on that order changes state. `state-machine.ts` and `invai-backend/src/db/schema/orders.ts` are outside T-4-1's owned paths (`invai-backend/src/modules/production/**`). **Grant:** T-4-1 gets a narrow, named grant to add a nullable `packOverride` jsonb column to `orders` (with migration) and to make `recomputeOrderStatus` override-aware (see stub below). Co-review by backend-foundation, same as the wave-3 pattern for one-off grants.
- **No PM/architect record exists for "ship an order with missing units."** Research and `scope.md` say nothing about partial shipment; decision 0002 is silent on it. This is new product semantics, not just a bug fix — see the PM review.
- **`invai-floor/src/screens/StationShell.tsx`** (the station router: imports each `*Station.tsx`, iterates `STATIONS` for tabs) is not in any card's owned paths, but T-4-3 needs one import + one case line there for `ReceivingStation`. **Grant:** T-4-3 may edit exactly those two lines in `StationShell.tsx`, committing only its own hunk.
- **`invai-floor/src/app/db.ts` does not exist.** The real file is `invai-floor/src/outbox/db.ts` (already inside T-4-2's owned `src/outbox/**`). The wave.md file-ownership table and T-4-2's card both had the wrong path; fixed below — no grant needed, just a path correction.
- **`today/service.ts:28`** hardcodes the open-order status list in raw SQL (`('new','needs_attention','in_production','ready_to_ship','partially_shipped')`), and `ai/assistant-tools.ts:112` lists `ready_to_ship` too. Neither file's owner is on this wave. This is the concrete reason the packOrder stub below avoids adding a new `ORDER_STATUSES` value this wave (see "Contract stubs (exact)").

## Parallel work rules
Same as wave 3 (`waves/3/wave.md`, "Parallel work rules"), with these numbers:
- Test DB `invai_test_t4<k>`.
- API port `31<k>0`, floor dev server `51<k>4`.
- `REDIS_URL=redis://localhost:6379/<k>`.
- DB copy `invai_t4<k>_copy`.

File ownership in invai-floor, which has three floor cards:
- **T-4-2 owns** `src/outbox/**` (including `src/outbox/db.ts` — corrected; there is no `src/app/db.ts`), `src/app/actions.ts`, `src/components/SyncStatus.tsx` and `LoginScreen.tsx` (the forget-station warning).
- **T-4-3 owns** new files under `src/stations/receiving/**`, plus a named grant for exactly two lines in `src/screens/StationShell.tsx` (one import, one `active === "receiving"` case — that file isn't owned by any card otherwise).
- **T-4-4 owns** `src/stations/{Pack,Press,Qc,Pick}Station.tsx`, `src/components/ProblemDialog.tsx`, `src/scan/result.ts`, `vite.config.ts`, `index.html` and `src/i18n/**` (T-4-2 and T-4-3 add their keys through a hand edit, committing only their own hunks).
- The floor i18n catalogs are shared, so every card commits only its own keys.
- **T-4-1 (backend)** gets a named grant, outside its normal `invai-backend/src/modules/production/**`, for: `invai-backend/src/db/schema/tenancy.ts` (`STATION_KINDS` gains `"receiving"`, one line), `invai-backend/src/db/schema/orders.ts` (new nullable `packOverride` jsonb column + migration) and `invai-backend/src/modules/orders/state-machine.ts` (`recomputeOrderStatus` becomes override-aware). Co-reviewed by backend-foundation.

## Contract stubs (exact)
The architect commits these to `invai-contracts` after wave 3 is pushed and the gate on the dev DB clears. All additive: new procedures, one new optional field on `Order`, one appended `STATIONS`/`ORDER_ITEM_STATES`-adjacent enum value, two new permissions. **No `ORDER_STATUSES` value is added** (see "Hidden dependencies" above) — `packed_partial` is represented as metadata, not a new order status, so `today/service.ts`, `ai/assistant-tools.ts` and `invai-web/src/components/badges.tsx` need no same-day fix this wave.

### 1. `production.packOrder` — `invai-contracts/src/schemas/production.ts`
```ts
export const PackOrderInput = z.object({
  orderId: Id,
  /** Idempotency key, same convention as ReceiveInput.idempotencyKey. A retry with the same
   * key returns the original result rather than re-evaluating completeness. */
  idempotencyKey: z.string().min(8).max(128),
  /** Present only on the "pack anyway" path. */
  override: z.object({ reason: z.string().min(1).max(500) }).optional(),
});
export type PackOrderInput = z.infer<typeof PackOrderInput>;

export const PackOverride = z.object({
  reason: z.string(),
  by: Id,
  byName: z.string(),
  at: Timestamp,
  missingItemIds: z.array(Id),
});
export type PackOverride = z.infer<typeof PackOverride>;

export const PackOrderResult = z.object({
  orderId: Id,
  packed: z.boolean(),
  /** Present (non-empty) whenever `packed` is false, or when packed was reached via override. */
  missing: z.array(z.object({ orderItemId: Id, state: z.enum(ORDER_ITEM_STATES) })),
  /** Non-null only when this call (or an earlier replay under the same order) used the override. */
  override: PackOverride.nullable(),
});
export type PackOrderResult = z.infer<typeof PackOrderResult>;
```

### 2. `production.packOrder` — `invai-contracts/src/contract/production.ts`
```ts
/** Marks an order packed once every non-cancelled unit is `packed` (decision 0002). Idempotent
 * on `idempotencyKey`: a replay returns the stored result. Refuses with `missing[]` when units
 * are outstanding, unless `override` is set (needs `production.override`; checked in the
 * handler, not the procedure's own permission, so packers keep calling this without it). */
production.packOrder: proc("production.scan", { auth: "floor" })
  .route({ method: "POST", path: "/pack-order" })
  .input(PackOrderInput)
  .output(PackOrderResult)
  .errors({
    PACK_INCOMPLETE: {
      status: 409,
      message: "Units are still missing",
      data: z.object({
        missing: z.array(z.object({ orderItemId: Id, state: z.enum(ORDER_ITEM_STATES) })),
      }),
    },
  }),
```
Add this as a sibling of `scan`/`qc` inside the `production` router (`invai-contracts/src/contract/production.ts`), not nested under `sheets` or `bins`.

### 3. Permission `production.override` — `invai-contracts/src/roles.ts`
- Append `"production.override"` to `PERMISSIONS` (production section, after `production.qc`).
- Do **not** add it to `PRESSER`, `PACKER`, `DESIGNER`, `OFFICE` or `RECEIVER`. `owner`/`admin` get it automatically through `SHOP_ALL`, matching the card's "a role with a `production.override` permission, or the owner or admin."
- Handler-level check (backend, not the procedure's declared permission): `if (input.override && !ctx.permissions.has("production.override")) throw FORBIDDEN`.

### 4. Order-level partial-pack marker — `invai-contracts/src/schemas/orders.ts`
```ts
// On Order, alongside the existing `hold`/`cancel` nullable objects:
packOverride: PackOverride.nullable(),
```
Backing column: `orders.packOverride jsonb` (nullable), migration in `invai-backend/src/db/schema/orders.ts` (T-4-1's named grant). `recomputeOrderStatus` (`invai-backend/src/modules/orders/state-machine.ts:197`) becomes: compute `status = deriveOrderStatus(states)` as today; if `packOverride` is set and the derived status is still "pre-ready" (i.e. not `ready_to_ship`/`partially_shipped`/`shipped`/`delivered`/`cancelled`/`on_hold` — meaning at least one non-cancelled unit is genuinely short), force `status = "ready_to_ship"` instead (an existing enum value, so every current `ready_to_ship` consumer keeps working unchanged) and leave `packOverride` populated so the order detail screen can show "packed partial: 2 missing — <reason>" once a web card picks it up. Once every non-cancelled unit reaches `packed`/`shipped`/`delivered` for real, clear `packOverride` (`null`) on the next recompute — the order then reads as a normal, non-partial `ready_to_ship`/`shipped` order. `on_hold`/`cancelled` still win over the override, since `deriveOrderStatus`'s own precedence already checks those first.

### 5. Receiving station — `invai-contracts/src/states.ts` and `roles.ts`
```ts
// states.ts
export const STATIONS = ["pick", "press", "qc", "pack", "receiving"] as const;
```
```ts
// roles.ts, PERMISSIONS (production section, after production.qc / production.override)
"production.receive",
```
- `RECEIVER` gains `"production.receive"`.
- `OFFICE` gains `"production.receive"` (it already reaches `sheets.markReceived` today via `production.build`; without this it would lose access when the procedure's permission changes below). `owner`/`admin` keep access via `SHOP_ALL`.
- `sheets.markReceived` (`invai-contracts/src/contract/production.ts`) changes its declared permission from `"production.build"` to `"production.receive"`. This is a deliberate permission reassignment, not a pure addition — `contract.test.ts`/`roles.test.ts` (`PROCEDURE_PERMISSIONS`) must be updated in the same commit, and the architect's report must state it explicitly so `reviewer` checks nobody else lost access (only `presser`/`packer`/`designer`/`vendor` never had `production.build` here, so nobody does).
- Backend-only, matching addition: `STATION_KINDS` in `invai-backend/src/db/schema/tenancy.ts:228` gains `"receiving"` (T-4-1's named grant; no new DB migration needed if `enumText` is an application-level check rather than a native Postgres enum — T-4-1 confirms which before assuming no migration).

### 6. `wrong_style` — no stub needed
Already shipped (see "Hidden dependencies" above). No contract change.

## Integration gate
- [x] `df -h /` 12 GB free
- [x] Fresh reset, migrate (to 0016), seed
- [x] API 13/13, browser 15/15, floor 3/3 (floor, offline, press); wave 4 smoke all pass (`gate.md`)
- [x] Builds pass
- [x] Per-card DBs and worktrees removed
- [x] Pushed to `main`

## Retro
- First-pass approvals: 2 of 4 (T-4-3, T-4-4). T-4-1 needed a comment fix and T-4-2 an alert fix.
- Decision 0010 (hand to lead; no partial shipments) came out of a real model limit found during the build.
- The permission check blocked one builder's commit; the tech lead committed it with the owner's approval.
- Lessons: never `git stash` in a shared tree; cross-owner hunks go through explicit grants.

## Build log
- Contract stubs are committed: contracts `c181abf`, backend `e427b8f` (the `packOrder` NOT_IMPLEMENTED stub). They make the backend typecheck red until T-4-1's first commit, and the floor typecheck red (`api/demo.ts`, `StationShell.tsx`) until T-4-3's first commit; both are granted. The stubs are reviewed with T-4-1 by a different model.
- Decision 0010: "pack anyway" becomes "hand to lead" and there are no partial shipments. The architect updates the stale contract comments on `PackOrderResult.override` and `Order.packOverride`.
- T-4-3:
  - `inventory.count` and `sheets.markReceived` have no idempotency key; a count replayed late could restore a stale number (architect + inventory owner).
  - The sync badge calls receipts "scans" (T-4-2).
  - The Receiving tile sits alone on the last row of the grid (designer).
  - Lazy-loading the receiving station would save about 10 KB (floor).
- T-4-1 review notes:
  - Today's pack count uses `count(*)` and can exceed the unit count (pre-existing).
  - Migrations have no `lock_timeout`; add it to the `zero-downtime-migration` playbook.
  - `floor_requests` needs a retention purge (e.g. 30 days) (backend-foundation).
- T-4-2 review: a pre-migration `pending` row with no `stationId` that hits a 401 can only be discarded, with no resend path (floor, optional). The product-designer should confirm the "lead" copy.
- T-4-4: the permission check blocked the builder's `git commit`. With the owner's approval, the tech lead committed it (floor `df18e53`, ui `178c829`). Other notes: the live update-prompt flow wasn't triggered in a browser; a short pack replayed from offline uses T-4-2's "offline scan was rejected" title (copy follow-up); the `BIN_OCCUPIED` text is generic.
