# T-7-4: Orders: ship-by holidays, staleness, per-line cancel (B-26, B-12)
## Owned paths
- backend: `modules/orders/**`, the webhook staleness check in `modules/channels/sync.ts` (only its hunks)
- `invai-contracts`: `NormalizedOrder.sourceUpdatedAt` and one new `ITEM_FLAG_CODES` value, `channel_edit_after_press` (grant, see `wave.md` clarifications; exact shapes in §3–4)
- tests

## Clarifications from the plan review
- **Staleness (AC3) needs a new contract field first.** Nothing today carries the channel's own "last modified" time; add `NormalizedOrder.sourceUpdatedAt: Timestamp.nullable()` and skip `updateExisting`'s work when it's set and older than `o.updatedAt`. Getting every adapter to populate it is T-7-1's `integrations/channels/**` territory (it's already touching adapters for exports) — coordinate rather than doing it yourself.
- **The re-import fix (AC2, `import.ts:144,335`) isn't a one-line comparison change.** `updateExisting` currently compares the raw channel `shipBy` against the already-computed `o.shipBy` — that mismatch is the bug. Fixing it means recomputing ship-by inside `updateExisting` the way `createOrder` does, which means threading `timeZone`/`processingDays` into that call, not just changing the `!==` check.
- **AC5's "already pressed" flag needs the new `channel_edit_after_press` code** (contracts change above) — check state ∈ `{pressed, packed, shipped, delivered}` (existing `ORDER_ITEM_STATES`, no new state needed) to decide when a line edit gets flagged instead of applied.
- Written against current `main`: wave 6's T-6-5 (`5339a57`) already changed `modules/channels/sync.ts` call sites (`getChannelAdapter` now takes the company/scope) — base your staleness hunk on the current file.

## Acceptance criteria
1. **Postal holidays:** ship-by skips USPS postal holidays (a table for 2026–2027 with a source) and weekends per the shop's settings. The Etsy CSV processing time is respected.
2. **Re-import bug:** re-importing a CSV with a `ship_by` column no longer marks every order "updated" or overwrites the computed ship-by when the value hasn't changed (`import.ts:144,335`).
3. **Staleness:** channel updates older than the stored `updated_at` are ignored.
4. **Per-line cancel:** a cancelled line cancels only its units. A buyer's cancel request puts the order on hold. TikTok ON_HOLD maps to a hold.
5. **Line edits** from channels (quantity, SKU, personalization) update or cancel units safely, and never touch units already pressed. Units that are already pressed get a flag.
6. **Tests:** cover each case.

## Verify
Run tsc, lint and test. Replay webhooks on a DB copy.
