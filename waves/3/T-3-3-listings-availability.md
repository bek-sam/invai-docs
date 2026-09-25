# T-3-3: Listings are recorded, and stock pushes back to channels

| Field | Value |
|---|---|
| Wave | 3 |
| Scope ref | `product/scope.md#mvp-in` items 2 and 6; decision 0003 (stock push is opt-in) |
| Backlog | B-65, B-04 (sync side) |
| Owner | backend-engineer (inventory), with `modules/channels/sku.ts` listing writes granted |
| Reviewer | reviewer |
| Co-reviewers | backend-foundation (migration), architect |
| Risk flags | migration, marketplace-policy |
| Model | opus |

## Depends on
- T-3-1's `setAvailability` fix (committed first).

## Owned paths (edit)
- `invai-backend/src/modules/inventory/**`
- `invai-backend/src/modules/channels/sku.ts` (write `listings` and `listing_variants` when orders import or SKUs map)
- The listings schema and its migration, if columns are needed
- tests next to these files

## r1 review note (architect): the schema is already there
`db/schema/channels.ts:84-138` already has `listings` and `listingVariants`, both `companyId` + `tenantPolicy(...)` + `.enableRLS()`, with `designId`/`productId`/`blankVariantId`/`channelSku`/`quantityCap`/`lastPushedQty` all present. **No migration is expected** for this card — confirm that before writing one. (Minor, non-blocking: `blankVariantId`/`designId`/`productId` are plain `uuid()` with no FK reference, unlike `connectionId`/`listingId`; leave as-is unless it's in your way, it's a pre-existing pattern choice, not new debt from this card.) `channels/sku.ts` and `channels/service.ts` currently have zero references to either table — that's the real gap (matches audit B-65).

## Acceptance criteria
1. **Recording listings:** importing an order, or mapping a SKU rule, upserts `listings` and `listing_variants` (channel, external ids, SKU, the mapped blank variant or product), tenant-scoped with RLS. The seed creates them for the demo shop.
2. **Computing availability:** from blank stock minus reservations, capped per the setting. When stock or reservations change, affected variants are queued and debounced (pick a concrete window, e.g. 30-60s, so QA can write a deterministic test — "debounced" alone isn't testable).
3. **Pushing:** `syncAvailability` pushes through `adapter.setAvailability` only for connections that opted in (decision 0003). Pushes are idempotent (the last pushed value is stored, so an unchanged value isn't re-pushed).
4. **Realtime:** publish `stock.changed` on stock changes (the web already subscribes; contract drift B-104).
5. **Tests:** listing writes, the availability math, opt-in gating, debounce and idempotency.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build`.
- For real on a DB copy: adjust stock, see the mock Shopify adapter receive one `setAvailability` with the right number, then adjust again with no change and see no push.

## Out of scope
- UI for the opt-in toggle (it exists in settings already, if not: B-86).
