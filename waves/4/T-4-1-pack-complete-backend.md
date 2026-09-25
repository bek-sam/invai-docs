# T-4-1: Pack-complete, wrong_style, idempotent QC and bin calls (backend)

| Field | Value |
|---|---|
| Scope ref | `product/scope.md#mvp-in` item 5; decision 0002 |
| Backlog | B-94 (backend), B-33 (backend part), B-27 |
| Owner | backend-engineer (production) |
| Reviewer | reviewer; co-reviewers architect, qa-engineer |
| Risk flags | floor-correctness |
| Model | opus |

## Owned paths
- `invai-backend/src/modules/production/**`
- The auth role permissions for `receiver` in `invai-backend/src/api/context.ts` (the `permissionsFor` map only). Coordinate with the stub commit. `permissionsFor` itself just reads `ROLE_PERMISSIONS`, so this is really "confirm `receiver`/`office` land correctly once the architect's `roles.ts` stub is committed" — there's nothing to hand-edit in `context.ts` beyond that.
- **Named grant (r1, outside the usual module boundary):** `invai-backend/src/db/schema/orders.ts` (new nullable `packOverride` jsonb column + its migration) and `invai-backend/src/modules/orders/state-machine.ts` (`recomputeOrderStatus`, made override-aware — see `waves/4/wave.md` "Contract stubs (exact)" §4). Co-reviewed by backend-foundation.
- **Named grant:** `invai-backend/src/db/schema/tenancy.ts:228`, one line (`STATION_KINDS` gains `"receiving"`). Check whether `enumText` needs a migration for a new value before assuming it doesn't.
- tests next to these files

## Acceptance criteria
1. **`packOrder`:** refuses with `PACK_INCOMPLETE` / `missing[]` when any non-cancelled unit isn't packed. It succeeds and marks the order packed when all are. Replays with the same `idempotencyKey` return the same result (field renamed from the card's earlier `clientKey` — see wave.md). It's safe for an order with no tote.
2. **Override:** needs `production.override` (checked in the handler, not the procedure's own permission — see wave.md §3), records an audit entry (who, why, missing units), sets `orders.packOverride` (jsonb: reason/by/byName/at/missingItemIds) and forces `status` to the existing `ready_to_ship` value rather than a new `packed_partial` enum value (exact rule in wave.md §4 — this keeps `today/service.ts` and `ai/assistant-tools.ts`'s hardcoded status lists correct without touching them). Never silently drops units: `missing[]` is always returned alongside `override`. `packOverride` clears itself once every unit is genuinely packed.
3. **`wrong_style`:** already shipped end to end (`schemas/production.ts` `MISMATCH_REASONS`, `matcher.ts:100`, `matcher.test.ts:71`, floor i18n en/es). This criterion is now "confirm no regression while touching `matcher.ts`/`floor.ts`," not new work — don't spend build time re-implementing it.
4. **QC and bins:** QC pass/fail and bin assign/release are idempotent on an explicit `idempotencyKey` (B-27) — not the current heuristic in the floor client that guesses "already applied" from `INVALID_TRANSITION`/`CONFLICT` error codes (`invai-floor/src/outbox/outbox.ts:126-129`). A double tap never double-records. Once real idempotency lands here, flag to floor-engineer (T-4-2) that the client-side heuristic can be narrowed or removed in a later wave — out of scope to change this wave.
5. **Receiver:** can mark vendor sheets received via `production.receive` (not `production.build`), and nothing broader. Confirm `office` still can too (it loses `production.build`-based access to `sheets.markReceived` unless it separately gets `production.receive` — architect's stub grants this).
6. **Tests:** cover every item above.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build` in backend.
- Curl on a DB copy: a partial order is refused, then packed after the rest; a replay; an override as packer (refused) and as admin (allowed); a `wrong_style` scan (regression check); `sheets.markReceived` as `receiver` and as `office`.
