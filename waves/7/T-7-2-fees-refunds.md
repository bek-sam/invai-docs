# T-7-2: Fees and refunds in profit (B-13, B-70)
## Owned paths
- backend: `modules/finance/**`
- the refund parsing in `integrations/channels/{shopify,csv}/**`; T-7-1 touches `exports/` only
- backend: `db/schema/finance.ts` (new `refund_events` table only) and `invai-contracts` (`RefundEvent`, `finance.refunds.*` — grant, see `wave.md` clarifications)
- tests

## Clarifications from the plan review
- **Do not start until wave 6's T-6-3 is merged to `main`.** T-6-3 is currently uncommitted in `invai-backend-t63`, editing `modules/finance/router.ts` and `modules/finance/service.ts` — this card's files, in full. Check `git log` on `invai-backend`'s `main` for T-6-3's commit before touching `modules/finance/**`; if it hasn't landed, wait.
- **AC2's "refunds reduce profit on their date" doesn't fit the current `profit_lines` shape.** That table is one row per order item keyed on `(companyId, orderItemId)` with a single `placedAt`; writing a refund into its `refundsCents` in place attributes it to the order's period, not the refund's. Use the new `refund_events` ledger (exact shape in `wave.md` §2) as the source of truth for the `refunds` bucket, dated by `refundedAt`, and have `finance.profit`'s period grouping read from it rather than from `profit_lines.placedAt`.
- Shopify/CSV ingestion should upsert `refund_events` by `(companyId, channel, channelRefundId)` so re-sync doesn't double-count; the manual "record refund" path has no channel id and is idempotent by construction (each call is a distinct, real event).

## Acceptance criteria
1. **Fees:**
   - Amazon and Walmart referral fees use the tiered, category-based schedule.
   - Refunds recover the referral fee.
   - Shopify sales tax is excluded from revenue.
   - The TikTok fee rate is verified against current docs, with the source cited.
2. **Refunds after shipment:**
   - Shopify: refunds pulled from the order's refunds.
   - CSV: refund columns where the export has them, or a manual "record refund".
   Refunds reduce profit on their date.
3. **Correctness:** money in integer cents, with property tests for the fee math.
4. **UI:** profit shows refunds and fees as separate lines (the finance UI from T-6-3; small web hunk granted).

## Verify
Run tsc, lint, test and build. On a DB copy: a refunded Shopify order (mock), and a CSV refund row. Check the numbers on the profit screen.
