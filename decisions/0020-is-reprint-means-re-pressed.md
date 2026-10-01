# 0020: `isReprint` means "this unit was re-pressed"; a re-pressed unit is still a sale unit

- Status: accepted (2026-10-01)
- Type: architecture

## Context
Three columns share the name: `order_items.is_reprint`, `profit_lines.is_reprint` (copied from the item by `recomputeProfit`) and `transfers.is_reprint` (per transfer). The only writer of the item flag, `openReprint` (`production/floor.ts:642`), sets it on the **same** item row; no code path (backend or seed) ever inserts a sibling "reprint" item. Production reads it as "re-pressed" (`sheets.ts:193,230` put reprints first; `floor.ts:775` QC-fail replay), and the UI shows it as a badge (`OrderItem.isReprint`, `OrderProfitLine.isReprint` in contracts; web `order-detail.tsx:275`, `order-profit.tsx:230`). But finance, refunds, re-import, analytics, market and the AI analyst filter `isReprint` out as "an extra, non-sale unit", a model that never existed. Effects found in T-P3-4 / plan review of T-P4-1 (B-242): reprinted orders show $0 revenue and a false loss (44 seed orders); re-importing an unshipped order whose only unit on a line was reprinted adds a second unit ("line added", `orders/import.ts:533,595`), and a channel line-cancel skips the reprinted unit (`import.ts:872`), so it can ship cancelled.

## Decision
1. `isReprint` (all three columns, and the contract fields) means "re-pressed at least once"; it is informational. It never decides whether a unit is a sale.
2. A sale unit is any non-cancelled order item (analytics may further exclude refunded lines, as today). No reader filters `isReprint = false` to count units, revenue, fees, refund scope, demand or re-import matching.
3. The cost of a reprint lives in transfer cost (every transfer printed for the item, already summed) and blank scrap; the count of reprints comes from the `reprints` table or `transfers.is_reprint`.
4. If a real extra non-sale unit is ever needed (a free replacement shirt), it gets a new, separately named marker, never this flag.

## Consequences
- No migration, no schema or contract change, no seed change: the seed already writes the flag with this meaning. `profit_lines` is derived and upserted per item, so the gate's reseed, the nightly 45-day recompute and the existing `finance.recompute` procedure correct old rows; no backfill job.
- T-P4-1 (backend-engineer) drops the filter in finance, refunds, orders re-import, analytics and market, with a re-import-after-reprint test. The two AI analyst reads (`ai/analyst-queries.ts:385`, `ai/assistant-tools.ts:601`) go to ai-engineer. Test fixtures that model a sibling revenue-0 reprint line (`analytics/finance-testkit.ts:356`, `digest.test.ts:350`, `market.acceptance.test.ts:666`, `digest.acceptance.test.ts:501`) are rewritten to the real model by their owners.
- Follow-up (backend-foundation, low): a doc comment on the three schema columns pointing here.
