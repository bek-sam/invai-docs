# T-29-1 architect co-review, round 1 (sonnet). Design consistency only.
Verdict: **approve**

Checked backend 63682ed, 2529441, report T-29-1.md, my plan review items 1-6.

- `purged` set on both rows: `redactBuyerText` writes `order_items.artworkStatus = purged`, nulls both keys and drops artwork flags; `item_artwork` goes to `purged` in the same plan. `counts.purged` is present (personalization/service.ts:810).
- Single guard: production/sheets.ts:169 is untouched. A personalized item with no `artworkKey` or a `purged` status returns `needs_artwork`. No second guard was added, and production/** has tests only.
- approve -> CONFLICT: service.ts:841 (`purged || !fileKey`). `update` is the re-entry path and is tested.
- Interface `redactBuyerText(tx, orderIds, {scope})` matches plan item 6. Departure 1 (extra `failedFiles: string[]`) is acceptable. It lets `redactOrders` throw and roll back so the delivery retries, and the 30-day job counts it. It is additive to the promised shape.
- Departure 2 is acceptable. Item art keys are deleted only under `{company}/artwork/` and only if no other item row points at them. A manual override outside that prefix, or a shared one, is nulled and the object kept (a stated gap). This is the safer failure than deleting a shared object.
- Storage first: deletes run before any DB write. An item whose key failed is skipped (`continue`), keeps keys and status, and the next night finds it again. Retry semantics match plan item 6 and no table was added.
- Idempotence: `art` is false once status is `purged` and there are no answers, so a second run is a no-op. Orders purged before T-29-1 are picked up from the order clocks (plan item 4).
- 18-month sweep walks by order id, so a left-over order whose delete failed cannot loop. Shopify redact throws on `failedFiles`, which rolls back and lets the webhook retry.
- Contract: no new contract change in this card; the T-29-5 status is consumed as designed. Type mirrors in db/schema are type-only (no migration).

Quick check: `pnpm typecheck` in invai-backend fails with one error at `src/modules/channels/webhook-auto-import.test.ts:205` (TS2322, `null` not assignable). That file belongs to T-29-4, not to this card. No T-29-1 file has a type error.

Optional: decision 0027 should list the manual-override/shared-key case as a known gap.
Blocking findings: none.
