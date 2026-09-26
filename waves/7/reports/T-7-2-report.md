# T-7-2 report: fees and refunds in profit (B-13, B-70)

Status: **built and verified, ready for review.** Commits (not pushed):
- backend `2d4668f`: tiered fees, refund ledger, Shopify/CSV refund ingestion, profit reads, and a day-view fix
- web `d9c1e90`: Refunds column and total card, plus "Record refund" on the order profit panel (en and es)

Built on current main (T-6-3 finance `d5dacfe`, stubs `7bb2bb1`/`3feb9ff`, migration `0020` from `6f957fe`; no new migration).

## Fee rates checked against official sources (2026-09-25)
| Channel | What applies to a DTF shop | Source |
|---|---|---|
| Amazon | Clothing & Accessories: 5% up to $15, 10% over $15 up to $20, 17% over $20. Backpacks, Handbags & Luggage: 15%. Everything else: 15%. $0.30 minimum per item. On a refund, Amazon keeps a refund administration fee of $5.00 or 20% of the referral fee, whichever is less. | https://sell.amazon.com/pricing (fetched 2026-09-25). I confirmed the admin-fee rule through search results, including a Seller Central forum thread; I did not open an Amazon help page for it. |
| Walmart | Apparel & Accessories: 5% up to $15, 10% from $15 to $20, 15% over $20. Shoes, Handbags, Backpacks & Sunglasses: 15%. Everything else: 15%. No minimum is listed. | https://marketplace.walmart.com/referral-fees/ (fetched 2026-09-25) |
| TikTok Shop US | 6% for menswear, womenswear and kids' fashion (page updated 2026-05-14). The referral fee covers every TikTok Shop fee except shipping and tax. A refund returns the fee minus a 20% refund administration fee, capped at $5 per SKU since 2025-05-15. | https://seller-us.tiktok.com/university/essay?knowledge_id=5988482086864682 (fetched 2026-09-25). Admin fee: knowledge_id=5982454398175018 (search result, 2026-09-25) |

**Walmart refunds:** the fee page doesn't say what happens to the referral fee on a refund. The code assumes Walmart returns it in full, in proportion to the refunded amount, with no admin fee. This is flagged in `fees.ts` and should be checked against the Retailer Agreement.

## What was built
- **`modules/finance/fees.ts`:** the per-channel referral schedules and `referralFeeCents` (per unit, on the unit's total sales price, which includes its share of shipping).
  - `feeRecoveredCents` works out the fee returned on a refund: the refunded share of the referral fee, minus the admin fee.
  - The category comes from the blank's style name: tote, bag or backpack counts as bags; everything else counts as apparel.
  - The schedule applies only while the shop's saved `transactionPct` still equals the contracts default. Once the shop types its own rate, that flat rate wins.
- **`profit.ts` `orderFees`:** now charges the tiered referral fee per unit (the fee line reads e.g. "Referral 5/17%"), and `splitFees` gives each unit its own referral fee.
- **Sales tax:** Shopify revenue already excluded tax on tax-exclusive orders. Tax-inclusive Shopify orders (where total = subtotal + shipping) now have the tax taken out of revenue.
- **`modules/finance/refunds.ts`:** `recordRefund` (manual entry, one row per call, `INVALID_ORDER_ITEM`, audited), `listRefunds`, and `ingestChannelRefunds`.
  - Ingestion upserts by `(company, channel, channelRefundId)` and keeps the first `refundedAt`.
  - It skips unknown orders, and skips lines whose units were all cancelled, because `profit_lines` already books those in the order's period.
- **Profit reads:**
  - `getProfit` merges `refund_events` into each dimension key, dated by `refundedAt`: refunds go up and channel fees go down by the fee returned. A key that has only refunds gets its own row with 0 revenue and 0 orders.
  - `orderProfit` puts refunds on the item's line and order-level refunds on the totals, and adds a "Fee returned on refunds" line (a negative amount) to the fee breakdown.
- **Shopify (`integrations/channels/shopify/refunds.ts`):** for orders whose status is REFUNDED or PARTIALLY_REFUNDED, one small GraphQL query per order reads `refunds`.
  - Line refunds use `subtotalSet` (before tax); shipping refunds use `refundShippingLines.subtotalAmountSet`; `restockType: CANCEL` lines are skipped.
  - The fields were checked against the 2026-07 Admin GraphQL `Refund` and `RefundShippingLine` docs.
  - The mock refunds one unit of an earlier order on every third poll.
- **CSV (`csv/parse.ts`):** `ParsedCsv.refunds` gives one order-level refund per order.
  - Shopify "Refunded Amount" and TikTok "Order Refund Amount" include tax, so the order's tax share is taken out. These files carry no refund date, so the first import time is used.
  - The generic format reads `refund_amount` (before tax) and `refunded_at`.
  - Etsy, Amazon and Walmart exports have no refund column, so those use the manual record.
- **Web:** the Refunds column is split out of "Other", a Refunds card is added to the totals, and the order profit panel gets a "Record refund" form (amount and date, saved at noon local time).

## Verification
- **Backend:** `tsc` clean, `biome check .` clean, `tsup` builds, and `vitest` passes 77 files / 541 tests (test DB `invai_test_t72`).
  - New tests: `fees.test.ts` (schedule edges, admin fee, and three seeded property checks over 2,000 runs each: integer and non-negative fees within the minimum/20% bounds; the fee returned is monotone and never more than the fee charged; per-unit fee splits add up exactly), `refunds.test.ts` (DB), and `parse-refunds.test.ts`.
- **Web:** `tsc` clean, biome clean on the changed files, `vite build` succeeds, 76 unit tests pass.
- **On the DB copy `invai_t72_copy`** (API on :3172, web on :5172):
  - **Shopify mock:** 3 real `syncConnection` polls created one `shopify` refund event ($28.00, fee returned 0, since Shopify Payments keeps its fee).
  - **TikTok CSV** with "Order Refund Amount" $21.62, imported twice through `importCsv`: one row, $19.91 before tax. The fee returned is 96¢ (138¢ fee × refunded share = 120, minus 20%).
    - Order profit: revenue $22.99, fees $1.38 − $0.96 = $0.42, refunds $19.91.
  - **Manual refund through REST** on an Amazon order from Aug 26 ($80.97, Referral 17% = $13.77): $15.00 refunded, 204¢ fee returned (255 − 51). Net went from $39.96 to $27.00.
    - An amount of 0 is rejected with 400.
  - **Profit by day:**
    - Aug 26 shows no refund.
    - Sep 25 (the refund day in Phoenix time) shows refunds of $62.91 (= 28.00 + 19.91 + 15.00), with fees reduced by the $3.00 returned.
    - The screen matches the API. Screenshots: `waves/7/reports/T-7-2/profit-by-day-refunds.png` and `profit-by-day-columns.jpg`.

## Found and fixed
The profit **day view returned 500** on main. The query's `to_char(placed_at at time zone $1)` in the select list didn't match the `$n` in GROUP BY. Both queries now `GROUP BY 1`. `refunds.test.ts` covers the day view.

## Scope notes and cross-card flags
- **Outside my owned paths (small additive hunks, please confirm the grant):**
  - `modules/channels/sync.ts`: two `ingestChannelRefunds` calls, one after the poll import and one after each CSV chunk. This is the only way refunds reach finance; T-7-4 edits the same file for staleness.
  - `integrations/channels/types.ts`: the new `ChannelRefund` type and an optional `FetchOrdersResult.refunds`.
- **Contracts `CHANNEL_RULES` notes are stale** (the contracts grant covers only `RefundEvent`, so I didn't change them): TikTok `transactionPct: 8` should be 6; the Amazon note says "17% referral for clothing" and the Walmart note says "15% for apparel". Finance ignores these while the shop keeps the default, but the settings screen still shows 8% for TikTok.
- **Not covered:**
  - The Shopify webhook path (`orders/updated`) doesn't read refunds; the poll backstop picks them up.
  - Shopify refunds on tax-inclusive shops use `subtotalSet` as-is.
  - `feeBreakdown` labels ("Referral 17%", "Fee returned on refunds") are English strings from the backend, the same pattern as the existing "Transaction 6.5%" labels.
  - The "Record refund" form was typechecked and built but not clicked through in the browser; the same procedure was checked through REST.
- **Cleanup:** API and web stopped, `invai_t72_copy` and `invai_test_t72` dropped, Redis DB 8 flushed, scratch scripts removed. One test CSV object is left in MinIO under the demo company's `imports/`.

## Round 1 fix (review blocker: manual refund cap and correction)
Commits: contracts `00bd3b3`, backend `16ddc52` (with migration `0021_finance_refund_void`), web `f41f60b`. None are pushed.
- **Cap on manual refunds:** `recordRefund` locks the order row and refuses with `REFUND_EXCEEDS_ORDER { remainingCents }` when the refund would push the total past what the order sold for.
  - What's left is the order total minus tax, minus refunds that aren't voided, minus units cancelled before shipping.
  - When an item is given, the refund is also capped at that unit's sale.
- **Void:** `finance.refunds.void({ id, reason })` works on manual refunds only (`REFUND_NOT_MANUAL`, `REFUND_ALREADY_VOIDED`).
  - It sets `voidedAt`, `voidReason` and `voidedBy`, and writes a `refund.void` audit entry.
  - The row stays in the list, but profit, the order view and the left-to-refund amount all skip it.
- **Web:**
  - The order profit panel lists each refund with a Void button for manual ones (the reason is asked in a prompt).
  - It shows "Left to refund" and disables Record once the amount is over it.
  - The three error codes are translated (en and es).
- **Checks:**
  - Backend: tsc and biome clean; finance plus CSV refund tests pass, 29/29, including new cap, void and channel-refund tests.
  - Contracts: tsc, biome and tests pass, 31/31.
  - Web: tsc and biome clean, 76 tests pass, `vite build` succeeds.
  - Not checked: the full backend suite and a browser click-through of the form were not re-run for this round.
