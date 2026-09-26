# Wave 7: multi-channel shops and correct money

- Goal (user outcome):
  - An Etsy-first shop can upload tracking back to Etsy (and Amazon, TikTok and Walmart) with one file.
  - Profit counts real fees and refunds.
  - The label fee follows the plan.
  - Ship-by dates respect postal holidays.
  - Channel updates never go backwards.
  - The web app is keyboard and screen-reader friendly, with no English leaks.
- Rules: `team/agent-brief.md` (decision 0011). Waves 10 and 11 are deferred.

## Cards
| Card | Owner | Co-reviewers | Flags | Model |
|---|---|---|---|---|
| T-7-1 Tracking export files for CSV channels (B-68) | integrations-engineer + web-engineer | product-designer, compliance-officer | marketplace-policy | sonnet |
| T-7-2 Fees and refunds in profit (B-13, B-70) | backend-engineer (finance) + integrations-engineer | data-analyst | payments | opus |
| T-7-3 Label fee from the plan (B-69, B-40) | backend-engineer (billing, shipping) | data-analyst | payments | sonnet |
| T-7-4 Orders: ship-by holidays, staleness, per-line cancel (B-26, B-12, `ship_by` re-import bug) | backend-engineer (orders) | architect, qa-engineer | floor-correctness | opus |
| T-7-5 Accessibility and i18n sweep (B-93, B-42) | web-engineer | product-designer | ui | sonnet |

Start T-7-1, T-7-3 and T-7-5 first, then T-7-2 and T-7-4 (they touch money and state).

## Contract stubs (exact)

Additive only (new tables / new procedures / one new enum value); nothing existing renamed or removed. Read-only review — not committed to `invai-contracts` or migrated; written here verbatim for each card's owner to implement.

### 1. Tracking export procedure + `shipments.exportedAt` (T-7-1)
```ts
// db/schema/shipping.ts: shipments gains (new nullable column, needs a grant — see clarifications)
exportedAt: timestamp({ withTimezone: true }),

// contract/shipping.ts, inside shipping router
exportTracking: proc("shipping.manage")
  .route({ method: "POST", path: "/exports/tracking" })
  .input(z.object({
    channel: z.enum(CHANNELS),      // must be a CSV-only channel (pendingApproval adapter)
    since: Timestamp.nullable(),     // null = since this channel's last export
    until: Timestamp.optional(),
  }))
  .output(z.object({ key: z.string(), count: z.number().int().nonnegative() }))
  .errors({
    NOT_CSV_CHANNEL: { status: 400, message: "This channel is not CSV-only" },
  }),
```
Do not reuse `trackingPushStatus`/`trackingPushedAt` for this — B-67 already shows `manual` being conflated with "pushed" in void logic (`shipping/service.ts:1040`). `exportedAt` is a separate, re-settable timestamp; the export query is `trackingPushStatus = 'manual' AND labeledAt >= (since ?? lastExportedAt)`. Re-export just re-runs the query and overwrites `exportedAt`.

### 2. Refund ledger + procedures (T-7-2)
`profitLines` is one row per order item, uniquely keyed on `(companyId, orderItemId)`, holding a single `placedAt` used for period bucketing. Writing a refund into that row's `refundsCents` in place attributes it to the **order's** period, not the **refund's** date — directly contradicting AC2 ("refunds reduce profit on their date"). This needs its own dated ledger, not a field bolted onto `profit_lines`:
```ts
// db/schema/finance.ts (new table, needs a grant — see clarifications)
export const refundEvents = pgTable(
  "refund_events",
  {
    id: id(),
    companyId: companyId(),
    orderId: uuid().notNull().references(() => orders.id, { onDelete: "cascade" }),
    orderItemId: uuid().references(() => orderItems.id, { onDelete: "cascade" }), // null = order-level (e.g. shipping refund)
    channel: text(enumText(CHANNELS)).notNull(),
    source: text(enumText(["shopify", "csv", "manual"] as const)).notNull(),
    amountCents: integer().notNull(),
    feeRecoveredCents: integer().notNull().default(0),
    channelRefundId: text(), // Shopify refund id / CSV row ref; null for manual entries
    refundedAt: timestamp({ withTimezone: true }).notNull(),
    note: text(),
    ...timestamps,
  },
  (t) => [
    uniqueIndex().on(t.companyId, t.channel, t.channelRefundId), // idempotent re-ingest (nulls excluded, so manual rows never collide)
    index().on(t.companyId, t.orderId),
    index().on(t.companyId, t.refundedAt),
    tenantPolicy("refund_events"),
  ],
).enableRLS();

// schemas/finance.ts
export const RefundEvent = z.object({
  id: Id,
  orderId: Id,
  orderItemId: Id.nullable(),
  channel: z.enum(CHANNELS),
  source: z.enum(["shopify", "csv", "manual"]),
  amountCents: Cents,
  feeRecoveredCents: Cents,
  refundedAt: Timestamp,
  note: z.string().nullable(),
});

// contract/finance.ts, new `refunds` sub-router
refunds: router({
  record: proc("finance.manage") // manual CSV path
    .route({ method: "POST", path: "/refunds" })
    .input(z.object({
      orderId: Id,
      orderItemId: Id.nullable(),
      amountCents: Cents,
      refundedAt: Timestamp,
      note: z.string().max(500).nullable().default(null),
    }))
    .output(RefundEvent)
    .errors({ INVALID_ORDER_ITEM: { status: 400, message: "Order item does not belong to this order" } }),
  list: proc("finance.read")
    .route({ method: "GET", path: "/refunds" })
    .input(z.object({ orderId: Id }))
    .output(z.object({ items: z.array(RefundEvent) })),
}),
```
`finance.profit`'s "day" (and any period) dimension must read the `refunds` bucket for a period from `refund_events.refundedAt`, not from `profit_lines.placedAt` — otherwise a refund in period 2 for an order placed in period 1 either double-counts or lands in the wrong bucket. Shopify/CSV ingestion upserts by `(companyId, channel, channelRefundId)`; the manual `record` procedure is idempotent by construction (a new row per call is correct — retries are the UI's job, not the server's, since there's no client-supplied key).

### 3. `NormalizedOrder.sourceUpdatedAt` for staleness (T-7-4)
No field carries the channel's own "last changed" timestamp today; `updateExisting` has nothing to compare against. This must land in `invai-contracts` (outside `modules/orders/**`) and be populated by **every** channel adapter (Shopify plus the Etsy/Amazon/TikTok/Walmart CSV parsers) — outside T-7-4's owned paths too. See clarifications.
```ts
// schemas/orders.ts: NormalizedOrder gains
sourceUpdatedAt: Timestamp.nullable(), // null = channel has no separate "last modified"; staleness check is skipped
```
`updateExisting` (`orders/import.ts`) skips the update entirely when `n.sourceUpdatedAt` is set and is older than `o.updatedAt`, before computing `changed`.

### 4. New item flag for post-press channel edits (T-7-4)
AC5 needs a way to surface "the channel tried to change this unit but it was already pressed." No existing `ITEM_FLAG_CODES` value fits; this is a one-line additive enum change in `invai-contracts` (outside `modules/orders/**` — see clarifications):
```ts
// schemas/orders.ts: ITEM_FLAG_CODES gains
"channel_edit_after_press",
```

## Clarifications from the plan review

- **T-7-2 must not start until wave 6's T-6-3 (profit UI) merges to `main`.** T-6-3 is live in `invai-backend-t63`, uncommitted, editing `modules/finance/router.ts` and `modules/finance/service.ts` — the exact files T-7-2 owns in full. T-6-1, T-6-2 and T-6-5 are already merged; only T-6-3 and T-6-4 (ai, no overlap) are still open. The wave already sequences T-7-2 second — add this as a hard gate, not just an ordering preference: check `invai-backend`'s `main` has T-6-3's commit before T-7-2's builder touches `modules/finance/**`.
- **Wave 6's T-6-5 (`5339a57`, already on `main`) changed the shape T-7-3 and T-7-4 build on.** It added a required `scope`/company argument to `carrierAdapter`/`getChannelAdapter` and touched `modules/shipping/service.ts`, `modules/shipping/jobs.ts`, `modules/channels/sync.ts` and `modules/billing/service.ts` (43 lines) as call-site updates. Not a live conflict — it's merged — but T-7-3's "the fee lookup only" hunk in `shipping/service.ts` and T-7-4's staleness hunk in `channels/sync.ts` must be written against current `main`, not against the pre-wave-6 file shapes the cards were drafted from.
- **T-7-1 and T-7-3 both touch `modules/shipping/service.ts`.** T-7-1 owns "the export procedure only," T-7-3 owns "the fee lookup only." Fine as separate hunks, but the wave order (T-7-1 and T-7-3 both start first) means both builders may edit this file at once — stage and commit only your own hunks (per `agent-brief.md`), and whichever lands second rebases its diff onto the first's commit before committing, not the other way around.
- **`db/schema/shipping.ts` (`exportedAt`) needs a grant to T-7-1.** Its owned paths list `modules/shipping/**` and `integrations/channels/exports/**`, not `db/schema/`. The export procedure cannot be built without this column.
- **`db/schema/finance.ts` (`refund_events`) and `invai-contracts` (`RefundEvent`, `finance.refunds.*`) need a grant to T-7-2.** Same shape of gap: owned paths list `modules/finance/**` and the CSV/Shopify refund parsers, not `db/schema/` or `invai-contracts`.
- **`invai-contracts` needs a grant to T-7-4** for `NormalizedOrder.sourceUpdatedAt` and the new `channel_edit_after_press` flag code (stubs 3 and 4). Populating `sourceUpdatedAt` also touches every channel adapter's `normalize()` (Shopify plus the Etsy/Amazon/TikTok/Walmart CSV parsers) — that's `integrations/channels/**`, T-7-1's territory this wave, not T-7-4's. Recommend: T-7-4 lands the contract field and the orders-side check; T-7-1's integrations-engineer populates it per-adapter as a small addition to the same CSV-parsing work it's already doing for exports, coordinated so the two don't collide on the same adapter files.
- **The re-import ship-by fix (`import.ts:144`) needs more than a comparison fix.** `updateExisting` doesn't currently receive `timeZone`/`processingDays`, so it can't recompute ship-by the way `createOrder` does — it only has the raw channel value to compare against the already-computed one, which is the bug. Threading those two through the call site is in scope for `modules/orders/**` but worth flagging so it isn't treated as a one-line diff.
- **T-7-3's $0.10 default alongside an open OI-1 is fine, but narrow it explicitly.** OI-1's own "default if no answer" and recommendation both name $0.10 as the code default while the owner decides between pricing-experiment options — T-7-3 doing this now doesn't jump ahead of the owner. Add a code comment on `PLAN_CATALOG.labelFeeCents` pointing at `OI-1` (not just a bare number), and note in the report that the other three cost-model gaps OI-1 lists (AI design generation still counted, Scale priced at $1,499 in the model vs. `custom`/uncapped in code, revenue booked for free pilots) are out of scope for this card and remain open.

## Numbers
- Test DB `invai_test_t7<k>`.
- API port `31<k>0`, web `51<k>3`.
- `REDIS_URL` `/<k>`.
- DB copy `invai_t7<k>_copy`.

## Build log and follow-ups
- T-7-2:
  - Grant approved after the fact for the refund-ingest hunks in `channels/sync.ts` and the `ChannelRefund` type in `integrations/channels/types.ts`.
  - Contracts `CHANNEL_RULES` TikTok `transactionPct` should be 6, not 8 (architect).
  - The Walmart refund-fee rule is an assumption, since it isn't documented (to verify with a pilot).
  - Shopify refund webhooks aren't handled; the poll covers them (integrations-engineer).
- T-7-1: Etsy, TikTok and Walmart template columns are unverified until the owner downloads the templates (OI-4).
- T-7-4: `settings.shipsSaturday` is read but has no UI yet (web follow-up). The staleness approach was approved as "newest channel timestamp applied", not `orders.updated_at`.
- **Grant (tech lead, 2026-09-26), recorded here:** T-7-4 was granted `integrations/channels/**` for the hold signals (`holds` on `ParsedCsv` and `FetchOrdersResult`, TikTok on-hold, Amazon buyer-cancel requests) and the Walmart CSV per-line cancel fix, plus `db/schema/orders.ts` `channel_updated_at` with migration 0022 and about 3 lines in `sync.ts`.
- **Grant (tech lead, 2026-09-26):** T-7-5 may edit invai-ui `Progress`, the Tabs wrapper, `Badge` and the `theme.css` success color (axe AC6), plus simple fixes for the web typecheck errors.
- **Gate (waves 6+7) YELLOW:** two blocking bugs found. (1) `vendorInbox` is missing the `printing` state (T-6-2 regression); a fix is granted to the T-6-2 author. (2) The seed has no `productionPartner` (T-8-1); a seed fix is granted to the T-8-1 author. A gate re-run of the API and web E2E follows.
