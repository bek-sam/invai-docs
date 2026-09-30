# Spec: business analytics v2 (the shop's numbers, complete)

- Author: data-analyst, 2026-09-28, on the owner's direction ("improve the business analytics of the platform to the 100% possible level, so it uses all the possible ways to improve the business", relayed by the tech lead 2026-09-28).
- Status: **ready for waves A1/A2 (Tracks A–C only).** Track D stays gated (see below).
- Scope refs: `product/scope.md#mvp-in` items 5, 6, 7, 8, 13, 14, 17; fences `#market-and-digest-fences`; `decisions/0006-v1-cuts.md` (statistical forecasting stays cut).
- Metric definitions: `metrics/definitions/` (20 files, index `README.md`); tested SQL: `metrics/sql/`.
- Builds on: `specs/assistant-business-analyst.md` (wave 17), `specs/market-signals.md` (wave 18), `specs/weekly-digest.md` (wave 19).

## Problem and evidence
InvAI already computes true profit per order, design, blank and channel, and the assistant and digest explain it. A DTF shop owner still can't answer, from InvAI, the questions that decide next month's money:
- "Am I losing money on shipping?" On the seed shop, labels cost $1,313 more than buyers paid for shipping over 263 orders, about $5 an order, **about a third of the Profit page's net ($3,803.71)** for the same window. Nothing in the product shows this number. (SEED, mock postage: `metrics/definitions/shipping_margin.md`.)
- "Which orders lose money, and why?" 8 of 272 orders had negative contribution before ads (`losing_order_rate.md`); the Profit page sorts by net but never says "these lose money".
- "Where does my sales money go?" Fees, refunds, shipping loss and reprints take 16–31% of gross sales per channel (`revenue_leakage.md`). Shops see only net.
- "What stock am I sitting on, and which sizes am I short?" 19 blank variants worth $2,233 had no use in the window; a Sand L sells at 35% of its style's units but holds 5.5% of its stock (`blank_stock_health.md`, `size_mix_gap.md`).
- "Why did profit change?" The assistant compares periods by channel, not by volume versus per-unit profit, and not by design.
- "Is my press labor number real?" Profit uses a fixed 4 minutes per shirt; the floor scans that could measure it are never used for timing.

Research: pain #6 "not knowing true profit" (frequency 4, severity 4), #7 blank stockouts and dead stock, #8 label costs, #1 late-shipment penalties, #5 film waste (`research/03-pain-points.md`). **0 pilot shops have asked** (no pilot is live); the owner directed the work. So the plan is cheap first: tracks A–C are SQL over data InvAI already stores, no AI spend, no outside data.

## 1. Audit: what exists today (2026-09-28)
| Surface | What it shows or computes | Files |
|---|---|---|
| Profit page | Revenue, 8 cost buckets, net, margin % by order, design, blank style, channel, day; totals; `incomplete` flag; estimated buckets per line; CSV export; recompute | `invai-web/src/routes/_app/analytics/profit.tsx`; `invai-backend/src/modules/finance/service.ts` (`getProfit`, `exportProfitCsv`, `orderProfit`, `recomputeProfit`); `profit.ts`, `fees.ts` (Amazon/Etsy/TikTok referral schedules), `refunds.ts` (dated refund ledger) |
| Ad spend page | Manual and CSV ad spend by day, channel, campaign; allocation by revenue share or per order | `invai-web/src/routes/_app/analytics/ad-spend.tsx`; `finance/service.ts` (`importAdSpendCsv`) |
| Cost settings | Fee tables, transfer ¢/sq in, packaging, labor rate and minutes per item, ads allocation | `invai-web/src/routes/_app/settings/costs.tsx`; `db/schema/finance.ts` (`cost_settings`) |
| Today | Due today, overdue, at risk, on hold, blocked (mapping, artwork), sheets, per-station waiting/done, capacity vs workload, packed-unlabeled, tracking failures, low stock, alerts | `invai-backend/src/modules/today/service.ts`; `invai-web/src/routes/_app/index.tsx` |
| Alerts | order_at_risk, order_overdue, sync_broken, sheet_stuck, stock_low, plan_limit_reached, qc_fail_spike, AI and ops alerts | `invai-contracts/src/schemas/alerts.ts`; `today/service.ts` (`generateAlerts`) |
| Assistant (14 read-only tools) | `get_profit`, `get_orders_summary`, `get_stock`, `get_listing_performance`, `get_channel_performance`, `get_production_status`, `compare_periods`, `get_ad_performance` (ROAS, TACoS, ad cost per order), `get_design_insights` (rising, falling, low-margin, cross-listing gaps), `get_fulfillment_health` (on-time, median hours to ship, overdue, reprints by reason with cost, refunds), `get_market_trend`, `get_seasonality`, `get_price_position`, `simulate_price` | `invai-backend/src/modules/ai/assistant-tools.ts`, `analyst-queries.ts` |
| Market signals | Trend (OLS), year over year, seasonality index and act-by date, price position, competition density, margin at price, price-response estimate (elasticity from own history), opportunity score; rules R1–R5; recommendation record with votes, adoption and 28-day outcome | `invai-backend/src/modules/market/{signals,compute,rules,feedback,history}.ts`; `specs/market-signals.md` |
| Weekly digest | Snapshot (last week, week before, trailing 4–8); detectors D1 data health, D2 revenue/net change, D3 margin slip, D4 ads, D5 designs, D6 fulfilment, D7 stock, D8 wins; ranking; Market watch; clicks, votes, views | `invai-backend/src/modules/digest/{snapshot,detectors,rank,render}.ts`; `invai-web/src/routes/_app/digests/**` |
| Inventory | Velocity, reorder point, days of cover, free-freight top-up, reorder suggestions, low stock | `invai-backend/src/modules/inventory/{reorder,service}.ts` |
| Reprints screen | Reprint list by reason | `invai-web/src/routes/_app/production/reprints.tsx` |
| Billing usage | Orders, labels, label fees, sheets, AI credits vs plan | `db/schema/billing.ts` (`usage`) |
| Pilot KPI SQL | late rate, overdue open, film use, reprint rate, scan block rate, label attach rate | `.claude/skills/define-metric/starter-metrics.sql` |
| Product analytics events | **None.** No SDK, no taxonomy (`instrument-analytics-event`) | — |

Data that exists but no report uses: `shipments.postage_cents` vs `orders.shipping_cents` (shipping margin); `shipments.weight_oz`, `rate_quotes` (carrier choice); `scans.scanned_at` per station (measured press time); `order_item_transitions` (waits per step, late drivers); `gang_sheets.cost_cents × utilization` (film waste $); `inventory_movements` consume (turns, dead stock); `purchase_order_lines.unit_cost_cents` and PO dates (blank price and lead-time trends); `orders.discount_cents`; `orders.buyer_ref` (repeat buyers, gated).

## 2. What "complete" means for a DTF shop
What the leading tools do (checked 2026-09-28):
- **Profit apps** (TrueProfit, BeProfit, Lifetimely): real-time net profit per order after COGS, shipping, fees and ads; Lifetimely adds contribution margin and LTV cohorts by first product, channel and geography ([Lifetimely](https://www.lifetimely.io/), [Lifetimely vs TrueProfit](https://useamp.com/alternatives/lifetimely-vs-trueprofit/), [BeProfit alternatives](https://trueprofit.io/blog/beprofit-alternatives)).
- **Triple Whale**: blended ROAS / MER (only right when every paid channel is connected), attribution windows, RFM segments ([metrics library](https://kb.triplewhale.com/en/articles/6127778-summary-dashboard-metrics-library), [blended ROAS limits](https://datadrew.io/blog/blended-roas-what-it-cant-tell-you/), [RFM](https://www.triplewhale.com/blog/rfm-segmentation)).
- **Print-shop software** (Printavo, Pythias): daily output, line efficiency, order status dashboards, date-range exports ([Pythias](https://pythiastechnologies.com/features), [Printavo](https://www.printavo.com/features/)).
- **ShipStation Analytics**: spend by carrier, service and region; shipping charged vs label cost per shipment ([Shipping Cost report](https://help.shipstation.com/hc/en-us/articles/4403822818331-Analytics-Reports-Shipments), [analytics](https://www.shipstation.com/blog/shipstation-analytics/)).
- **eRank / Marmalead** (Etsy), **Helium 10 / Jungle Scout** (Amazon): keyword and competitor research. Fenced for InvAI (no scraping, no Etsy competitor data, licensed sources only with the owner; `scope.md` fences). InvAI's advantage is the part none of them has: the shop's own production and cost data.

"Complete" for InvAI, by area (✅ have, ◐ partial, ✗ missing):
| Area | Complete means | Today |
|---|---|---|
| Profit | CM1/CM2/CM3 per order, design, SKU, channel; losing orders; leakage by component; shipping margin; why-changed bridge | ◐ net per dimension only |
| Cash | Break-even with fixed costs; operating profit pace; 13-week cash view (payout lag, open POs, run-rate) | ✗ |
| Customers | Repeat rate, cohorts, LTV at contribution, RFM segments | ✗ (gated) |
| Designs and SKUs | Lifecycle stage, winners/losers, dead designs, size/color mix, cannibalization | ◐ rising/falling/low-margin/gaps; market trend |
| Pricing | Margin at price, elasticity from own history, discount rate | ✅ margin at price and price-response estimate (market); ✗ discount rate |
| Channels and ads | Channel mix, ROAS, TACoS, MER, break-even ROAS, attribution limits stated | ◐ ROAS/TACoS; no MER or break-even |
| Operations | Throughput, bottleneck, measured labor per unit, reprint and film waste $, on-time by driver | ◐ counts and on-time; no $, timing or drivers |
| Inventory and suppliers | Turns, dead stock $, stockout exposure, size-curve reorder, supplier price and lead-time trend | ◐ reorder and low stock only |
| Shipping | Cost per zone and weight, carrier/service mix, cheaper-rate misses | ✗ |
| Alerts and anomalies | Threshold alerts; anomaly detection on daily numbers | ◐ threshold alerts; anomalies need ≥ 8 weeks history (digest "Later") |
| Goals | Monthly targets with pace | ✗ |
| Benchmarks | Against similar shops | ✗ **fenced**: 10+ shops per cell, counsel's ToS/DPA clause, tenant opt-out |
| What to do next | Ranked actions with $ impact, always visible; the assistant answers "why" with evidence; exports | ◐ weekly digest top 3; assistant; profit CSV |

## 3. Gap analysis
Value for a **mid** shop (300 orders/day ≈ 9,000/month), scaled from the seed's per-order figures; every value is an estimate to be replaced by pilot data. Effort S ≤ 1 card, M 1–2 cards, L 3+.

| Capability | Status | Value to the shop (estimate) | Effort | Data we have / need | Fence check |
|---|---|---|---|---|---|
| Shipping margin by channel, weight, service, zone | missing | Seed loses ~$5/order on shipping; recovering even $0.50/order = **$4,500/month** | M | have: postage, shipping charged, weight; need: `shipments.dest_zone` (from ZIP3 at label time, no address kept) | ok |
| Why-profit-changed bridge (volume vs per-unit, by design and cost line) | missing | Hours of spreadsheet work per week; right answer to the #1 assistant question | S | have | ok |
| CM ladder and losing orders | partial | Seed: 3% of orders lose money; fixing their causes on 9,000 orders ≈ **$1,500–3,000/month** | S | have | ok |
| Revenue leakage (discounts, fees, refunds, shipping, reprints) | missing | Makes 16–31% of gross visible; controllable part (shipping, reprints, refunds) is where the money is | S | have; offsite-ads fee needs import support | ok |
| Reprint cost and film waste $ | partial (counts) | Seed: reprints 3.1% of items, film waste 17.5% of film spend; halving both ≈ **$1,000–2,000/month** | S | have | ok |
| Late-shipment drivers | partial | Protects marketplace ranking (pain #1); avoids Amazon/TikTok penalties | S | have | ok |
| Measured press time and bottleneck | missing | Correct labor in every profit number; 1 hour/day of staffing decisions | M | have scans and transitions; seed lacks realistic timing | staff metrics shown in aggregate only |
| Design lifecycle and dead designs | partial | Retire 20–30% dead listings; focus ads and blanks on growing designs | S | have; seed needs history (B-130) | ok |
| Blank turns, dead stock $, size-mix gap | missing | Seed: $2,233 dead stock; freeing 10% of stock cash; fewer size stockouts | M | have | no automatic POs (fence) |
| Stockout exposure (sold units waiting on blanks) | missing | Prevents late orders; small per week, severe when it happens | S | have | ok |
| Supplier price and lead-time trend | missing | A 5% blank price rise on 9,000 units ≈ $1,500/month found early | S | have (PO lines); seed has none | ok |
| MER and break-even ROAS | partial | Stops ad spend below break-even; seed Shopify ROAS 3.1 vs break-even 2.0 | S | have | attribution by channel only (stated) |
| Break-even and operating profit pace | missing | Owner knows by mid-month if the month covers rent and salaries | S | need `cost_settings.fixed_monthly_cents` | ok |
| Always-on ranked actions with $ impact (Today) | partial (weekly digest) | Actions mid-week, not only Monday | M | have (digest detectors) | suggestions only; nothing auto-changes |
| Assistant "why" with evidence (new tools) | partial | Answers the questions above in words, en/es | M | have | read-only (item 13) |
| Exports for every view (in-app CSV) | partial (profit only) | Accountant and spreadsheet hand-off | S | have | ok |
| Goals and targets with pace | missing | Focus: one number to hit per month | S–M | need a goals table | **scope change** (new surface) |
| Anomaly alerts (robust z on daily numbers) | missing | Catches a fee change, a broken import or a viral spike in a day | M | need ≥ 8 weeks history | digest "Later" item; **PM + owner** |
| Customer analytics (repeat, cohorts, LTV, RFM) | missing | Tells which designs and channels bring buyers back; high value for Shopify-heavy shops, low for marketplace-only | L | have `buyer_ref` (name hash, weak); need a keyed hash of channel buyer id | **scope change; compliance** (Amazon buyer data only for fulfilment, 30-day PII; Etsy API Terms "analytics" clause; 18-month cap) |
| 13-week cash view | missing | Avoids cash crunches before Q4 blank buys | M–L | need payout schedules per channel (settings), open POs | **scope change**; a run-rate, not a forecast (0006 holds) |
| Scheduled report emails | missing | Accountant gets the P&L monthly without logging in | S | have | **owner**: needs OI-12/13/14 (email provider, address, CAN-SPAM) |
| Cross-shop benchmarks | missing | "Your film use vs similar shops" | M | need 10+ shops per cell | **fenced** until trigger in `scope.md` "Later" |
| Demand forecasting model | missing | — | — | — | **cut** (`decisions/0006`); no new evidence, not proposed |

## 4. Top 15 additions by value
1. **Shipping margin** by channel, service, weight and zone, with free-shipping orders called out.
2. **Why profit changed** (profit bridge): volume vs per-unit profit, by design and by cost line; feeds digest D2 and the assistant.
3. **Contribution margin ladder and losing orders**: CM1/CM2/CM3 on every Profit view; a "orders that lost money" list with the cost line that did it.
4. **Revenue leakage waterfall**: gross sales → discounts → fees → refunds → shipping loss → reprints → contribution.
5. **Reprint and film waste in dollars**, by reason, station and vendor.
6. **Size-mix gap, dead stock and turns** for blanks, feeding reorder suggestions as a size split (suggestion only).
7. **Late-shipment drivers**: on-time by personalization, rush, multi-unit, blocked > 24 h, vendor turnaround.
8. **Ranked actions on Today** with $ impact, from the digest detectors plus new ones, all week.
9. **Break-even and operating profit pace** (fixed monthly costs setting).
10. **Measured press time** from scans, with a "update your labor setting" suggestion; bottleneck step from waits.
11. **Design lifecycle**: new, growing, steady, declining, dead listings.
12. **MER and break-even ROAS** per channel, with the attribution caveat.
13. **Assistant tools v6**: `get_unit_economics`, `explain_profit_change`, `get_operations_health`, `get_inventory_health`, `get_shipping_insights`.
14. **Supplier price and lead-time trends**, with margin impact per design and a lead-time setting check.
15. **Customer repeat rate and cohorts** (Shopify first, Amazon excluded), gated on the owner and compliance.

Also proposed but lower or gated: stockout exposure (small, folded into item 6's card), CSV export on every view (folded into web cards), goals and targets, anomaly alerts, 13-week cash view, scheduled report emails. Benchmarks stay fenced; forecasting stays cut.

## 5. Rules for every analytics feature
1. **One definition.** Every number on a screen, in the assistant or in the digest comes from a function that implements a definition in `metrics/definitions/`, and the definition names that function. The web shows the same number as the assistant and the digest (parity test, AC-G1).
2. **Counts next to every percent**; below the definition's minimum sample, show counts and "not enough data yet".
3. **Estimates are marked.** Any number built on an estimated bucket (`profit_lines.estimated`), a mock provider or a user setting shows it.
4. **Associations, not causes.** Driver cuts say "late orders were more often personalized", never "personalization caused it".
5. **Suggest, never act.** Nothing writes prices, listings, ads, POs or settings (fence). A suggestion to change a setting links to the settings screen.
6. **No buyer PII.** Customer analytics (gated) uses only a keyed pseudonymous id; no name, email, address or ZIP is read by analytics code; outputs are counts. `dest_zone` is a carrier zone number (1–9), not an address.
7. **Own data only.** Nothing computed for one shop uses another shop's data.
8. **Cheap by default.** Tracks A–C add no AI spend; the assistant tools cost only when asked.
9. **Sample workspaces** get the same analytics on seed data, labelled "sample data".
10. **en/es** for every label, empty state and explanation; money through `Intl`; percent-point changes as points (wave 20 rule).

## 6. Behaviour by track

### Track A: profit and cash (scope item 8)
- `analytics.unitEconomics({period, dimension: order|design|blank|sku|channel, channel?})` → rows with revenue, CM1, CM2, CM3, their %, orders, units, estimated share; totals equal the Profit page totals.
- `analytics.losingOrders({period, limit≤50})` → orders with CM2 < 0: order number (the shop's own order number, allowed on the shop's own screen), channel, design, CM2, the largest cost line.
- `analytics.leakage({period, channel?})` → the waterfall components (`revenue_leakage.md`) and `ordersWithoutProfitLine`.
- `analytics.shippingMargin({period, groupBy: channel|service|weightBand|zone})` → labeled orders, charged, label cost, margin, per order, free-shipping orders; `zone` rows only for shipments with `dest_zone`.
- `analytics.profitBridge({period, basePeriod?, by: design|channel|costLine})` → total change = volume + rate; top 10 movers.
- `analytics.breakEven({period})` → fixed monthly costs, CM3 per order, break-even orders, pace, operating profit pace; `fixedCostsSet: false` when the setting is empty.
- `cost_settings.fixed_monthly_cents` (int, nullable) with a plain-language hint that labor per shirt is already counted.
- `shipments.dest_zone` (smallint, nullable): the shipping module stores the carrier zone at label time (from origin and destination ZIP3 in memory); no address or ZIP is stored for analytics.

### Track B: operations (scope items 5, 7, 14)
- `analytics.operations({period})` → reprint cost by reason/station/vendor; film waste $ and film use by vendor; waits per step (median, p90, still waiting) and the bottleneck step; measured press minutes per unit per station vs the labor setting; late rate by driver with counts; `hasEnoughHistory: boolean` (whole-response flag, distinct from each metric's own per-widget threshold) for the AC-B/C-screen1 first-run state.
- Station and person: shop-facing views show stations, never a named person's speed (owner decision needed before per-person views).

### Track C: inventory, suppliers, designs (scope items 6, 8, 16)
- `analytics.inventoryHealth({days})` → on-hand value, turns, dead stock variants and value, size-mix gaps (|gap| ≥ 10 points, ≥ 30 units), stockout exposure; `hasEnoughHistory: boolean` (AC-B/C-screen1).
- `analytics.supplierTrends({period})` → unit cost by supplier × style × month, median lead days, and the lead-time setting when measured differs by > 3 days (AC-C5).
- `analytics.designLifecycle({asOf, channel?})` → stage per design with u4, p4, last sale; when the market module has a trend for the design, that trend is shown and wins; `hasEnoughHistory: boolean` (AC-B/C-screen1).
- Reorder suggestions gain an optional size split proportional to the trailing size curve (suggestion; the shop edits the PO).

### Track E: actions, assistant, digest, exports (scope items 13, 14, 17)
- **Actions panel on Today**: up to 5 ranked actions with $ impact, using the digest's detector code and ranking (`digest/detectors.ts`, `rank.ts`) run daily on a trailing 7-day window. Same fixed action wording and deep links. Clicks recorded like digest clicks.
- **New digest detectors**: D9 shipping loss (loss per order worse by ≥ $0.50 vs 4-week median, ≥ 30 labeled orders), D10 losing orders (> 5% of orders), D11 dead stock or size gap (dead stock > 15% of stock value, or a size gap ≤ −15 points with < 14 days of cover), D12 blank price up (≥ 5% vs 3 months ago), D13 break-even pace (pace below break-even, only if fixed costs set). D2 names the bridge's biggest mover.
- **Assistant tools** (read-only, `{data, summary, answer}`, ≤ 20 rows, `withTenant`): `get_unit_economics`, `explain_profit_change`, `get_operations_health`, `get_inventory_health`, `get_shipping_insights`. Prompt v6: for a "why" question call `explain_profit_change` first; every recommendation carries its evidence numbers and the metric name.
- **Exports**: every analytics view has "Export CSV" with the same filters (the profit export pattern).

### Track D: needs a scope change (not in waves A1–A2)
- D-1 Goals and targets: the shop sets monthly net profit, on-time rate, reprint rate and film-use targets; Today and the digest show pace.
- D-2 Anomaly alerts: robust z-score (median and MAD over ≥ 8 weeks, same weekday) on daily orders, net, fee rate and refund rate; an alert only at |z| ≥ 3.5 and a $ floor.
- D-3 Customer analytics: keyed buyer id (HMAC of channel + channel buyer id, name-hash fallback marked approximate); repeat rate, monthly cohorts, 90/180/365-day contribution per buyer, 5 RFM groups; Shopify first; Amazon never; Etsy, TikTok and Walmart after compliance review; counts only, no buyer list.
- D-4 13-week cash view: opening cash (entered by the shop), expected payouts from the channel payout lag (settings), open POs, run-rate costs; labelled "projection from your last 8 weeks, not a forecast".
- D-5 Scheduled report emails (monthly P&L CSV to named people): after OI-12/13/14.

## Acceptance criteria (Given / When / Then)
- **AC-Seed1** (T-A1, backing every AC below that names a minimum sample) Given a fresh seed, when it finishes, then: order history spans ≥ 18 months with a Q4 peak of ≥ 1.5x the trailing average; ≥ 2 late-shipment drivers have ≥ 30 orders each; ≥ 1 station has ≥ 100 timed press scans with a realistic (non-constant) interval spread; ≥ 2 supplier×style PO pairs show a unit-cost change ≥ 5% or a lead-time change > 3 days; ≥ 2 Shopify buyers each have ≥ 2 orders; ≥ 3 distinct reprint reasons exist across ≥ 2 stations and ≥ 2 vendors; ≥ 1 style/color/size shows a size-mix gap ≥ 15 points with ≥ 30 units sold; ≥ 1 variant qualifies as dead stock (stock > 0, no movement in 90+ days) at a nonzero dollar value; golden-path order/item counts and Today's queue counts are unchanged, or the diff is stated and re-verified green.

Tracks A–C (waves A1–A2):
- **AC-A1** Given the demo seed and a period, when an owner opens Analytics → Profit with the "Contribution" view, then CM1, CM2 and CM3 per channel appear, and CM3 totals equal the Profit page's Net for the same period to the cent (parity test in backend and one E2E).
- **AC-A2** Given an order whose label cost is larger than its revenue less its other costs, when the owner opens "Orders that lost money", then that order is listed with its CM2 and "Label" as the largest cost line, and an order with positive CM2 is not listed.
- **AC-A3** Given labeled orders with shipping charged and label costs, when the owner opens Shipping profit, then each channel shows labeled orders, charged, label cost and margin that match `metrics/sql/shipping_margin.sql` on the same database, and free-shipping orders are counted. Given **zero labeled shipments** in the period, then the tab shows "No labeled shipments yet in this period" instead of a blank table or a $0 margin that reads as good news.
- **AC-A4** Given a shipment labeled after T-A4 lands, when it is bought, then `shipments.dest_zone` holds a zone 1–9 and no new column holds an address, ZIP or name (test asserts the column list).
- **AC-A5** Given two weeks with different sales, when the owner asks the assistant "why did profit change this week?", then it calls `explain_profit_change`, the stated volume and per-unit parts add up to the stated change, and the top design named is the one `profit_bridge.sql` ranks first.
- **AC-A6** Given no fixed costs set, when the owner opens the break-even card, then it says "Add your monthly fixed costs to see break-even" with a link to Settings → Costs, and no break-even number is shown. Given $2,500 set, then break-even orders and pace match `break_even.sql`.
- **AC-A7** Given a period with 105 orders that have no profit line, when any leakage or CM view loads, then it shows "105 orders aren't in these numbers yet" and never a silently partial total.
- **AC-B1** Given reprints and sheets in the period, when the owner opens Analytics → Operations, then reprint cost by reason and film waste $ match `reprint_cost.sql` and `film_waste_cost.sql`.
- **AC-B2** Given press scans at realistic intervals (seed T-A1), when Operations loads, then measured press minutes per unit per station appear with the timed count, and when the measured median differs from the labor setting by > 25% with ≥ 100 timed units, a suggestion links to Settings → Costs; with fewer timed units it says "not enough scans yet".
- **AC-B3** Given late shipped orders in the seed, when Operations shows late-shipment drivers, then each cut shows counts, cuts under 30 orders show counts only, and the copy says "were more often", not "caused".
- **AC-B/C-screen1** Given a shop live under 2 weeks (or otherwise below every metric's minimum sample across the board), when the owner opens Operations, Inventory health or Design lifecycle, then the screen shows one whole-screen "not enough history yet" state (the AC-A7 banner pattern), distinct from and in addition to each widget's own per-metric threshold note (AC-B2's "not enough scans yet", the size/style minimum in AC-C1).
- **AC-C1** Given the seed's G64000 Sand stock, when the owner opens Inventory health, then the L size shows as under-stocked with its sales and stock share, and a style × color with < 30 units sold is shown as "not enough data" rather than omitted (rule 2).
- **AC-C2** Given variants with stock and no use in 90 days, when Inventory health loads, then dead stock count and value match `blank_stock_health.sql`.
- **AC-C3** Given a reorder suggestion for a style with a size gap, when the owner creates a PO from it, then the proposed quantities follow the size curve and the owner can edit every line before submitting; nothing is submitted automatically.
- **AC-C4** Given a design with an active listing and no sale in 60 days, when Design lifecycle loads, then it is "dead"; given the market module has a trend for a design, then that trend is shown.
- **AC-C5** Given purchase-order lines for a supplier × style over several months, when the owner opens Supplier trends, then unit cost by month and median lead days match `supplier_trends.md`'s SQL, and when the measured lead time differs from the style's lead-time setting by > 3 days, a suggestion links to the setting.
- **AC-E1** Given D9 conditions (shipping loss per order worse by ≥ $0.50 vs the 4-week median, ≥ 30 labeled orders), when the digest builds, then a D9 action "Review shipping prices on {{channel}}" appears with its $ impact; below the minimum it doesn't fire.
- **AC-E1b** Given D10 conditions (> 5% of orders in the period are losing orders, ≥ 30 orders total), when the digest builds, then a D10 action "Review your losing orders" appears with its $ impact; below the minimum it doesn't fire.
- **AC-E1c** Given D11 conditions (dead stock > 15% of stock value, or a size gap ≤ −15 points with < 14 days of cover), when the digest builds, then a D11 action naming the style/color appears; below either threshold it doesn't fire.
- **AC-E1d** Given D12 conditions (a supplier's unit cost is ≥ 5% higher than 3 months ago), when the digest builds, then a D12 action naming the supplier and style appears with the margin impact; below the threshold it doesn't fire.
- **AC-E1e** Given D13 conditions (pace is below break-even, fixed costs set), when the digest builds, then a D13 action appears; with no fixed-costs setting, D13 never fires (no break-even to be below).
- **AC-E1f** Given a period where profit changed and `explain_profit_change` names a top mover, when the digest's D2 detector runs for the same period, then D2's copy names that same top mover.
- **AC-E2** Given the Today page, when the owner opens it on a Wednesday, then up to 5 ranked actions appear with $ impact and a button each, from the same detectors as the digest, and clicking one records a click. Given zero detectors fire (a healthy week), then the panel shows a plain "Nothing needs attention right now" state, not an empty gap or a hidden panel.
- **AC-E3** Given a question in Spanish, when a v6 tool answers, then the reply and every label are in Spanish.
- **AC-E4** Given two companies A and B, when any `analytics.*` procedure or v6 tool runs for A, then no row of B appears (test per procedure and tool).
- **AC-E5** Given a user without `finance.read` (designer, presser, packer, receiver, vendor), when they call any `analytics.*` procedure, then they get `FORBIDDEN`.
- **AC-E6** Given any analytics view, when the owner clicks Export CSV, then the file has the same rows and totals as the screen for the same filters and holds no buyer name, email, address or personalization text.
- **AC-G1** Given the digest's last-completed calendar week as the period, with no channel filter and `dimension: order` (whole-shop totals, the only shape the digest snapshot exposes), when the Profit page, `analytics.unitEconomics`, the assistant's `get_unit_economics` and the digest snapshot each compute net for that exact week, then all four are equal to the cent (one shared function, `analytics/shared.ts`'s `computeNet`). A second, separate case covers `channel`-filtered parity: given the same week with `channel: "shopify"`, `unitEconomics` and `get_unit_economics` (which both accept a channel filter) are equal to each other; the digest snapshot has no per-channel net to compare against.
- **AC-G2** Given a large-shop profile (1,000 orders/day, 90 days), when any `analytics.*` read runs, then it answers in under 1 s p95 locally (`scale-test`), else the card adds a nightly rollup.

Track D criteria are written after the owner's answer.

## Proposed task cards and waves
Change order: contracts → backend → web; at most 5 cards per wave; reviewer on every card plus the co-reviewers named.

**Overlap with the PM's growth rows (backlog "Proposed: growth opportunities", filed the same day, B-143..B-161; OI-17).** Reconciled so nothing is built twice:
- **B-153** (labor per piece and station throughput from scan gaps) is the same capability as measured press time here: T-A4 implements B-153 using `metrics/definitions/press_minutes_per_unit.md`; the per-person view stays off by default in both.
- **B-152** (cash-flow view: 4-week payouts vs committed spend) is the same need as Track D-4: one card, T-A14 = B-152, with this spec's labelling rule; horizon (4 vs 13 weeks) is the PM's call.
- **B-146** (Q4 margin guard: fee tables with effective dates, blank price refresh, margin-drop detector) contains D12 "blank price up": T-A9 builds D12 on `supplier_trends.md` and leaves the fee-table and price-refresh parts to B-146.
- **B-145** (carrier adjustments in profit) makes `shipping_margin` more accurate; no change to the cards here, the definition gets a version line when it lands.
- Backlog ids (section "Proposed: analytics v2"): T-A1 B-168, T-A2 B-169, T-A3 B-170, T-A4 B-171, T-A5 B-172, T-A6 B-173, T-A7 B-174, T-A8 B-175, T-A9 B-176, T-A10 B-177, T-A11 B-178, T-A12 B-179, T-A13 B-180, T-A14 B-152, T-A15 B-181; SQL move B-182; Amazon shipping-credit check B-183.
- **B-150** (capacity planner) can reuse `stage_wait_hours` and `press_minutes_per_unit`; no card here.

### Wave A1: data and read services (in scope; PM confirms)
| Card | Owner | Scope | Co-reviewers | Flags |
|---|---|---|---|---|
| T-A1 Analytics-ready seed: 18 months of closed history with a Q4 peak, some late shipments, realistic scan intervals, POs with price changes and lead times, a few repeat Shopify buyers, several reprint reasons (absorbs B-130; golden-path counts and Today queues unchanged) | backend-foundation + qa-engineer | `src/db/seed/**` | qa-engineer, data-analyst (numbers look real) | golden path |
| T-A2 Contract: `analytics` namespace (unitEconomics, losingOrders, leakage, shippingMargin, profitBridge, breakEven, operations, inventoryHealth, supplierTrends, designLifecycle, export), `CostSettings.fixedMonthlyCents`, `Shipment.destZone`, v6 assistant tool names, `finance.read` on every procedure | architect | `invai-contracts/**` | backend-foundation, web-engineer (consumer), ai-engineer | contract |
| T-A3 Finance analytics service: CM ladder, losing orders, leakage, shipping margin, bridge, break-even; `fixed_monthly_cents` migration; profit parity test (AC-G1) | backend-engineer (finance) | `src/modules/finance/**`, new `src/modules/analytics/**` read service, `db/schema/finance.ts` + migration | backend-foundation (migration), security-reviewer (tenancy), data-analyst (definitions) | tenancy, migration |
| T-A4 Operations and shipping analytics: reprint and film $, waits and bottleneck, measured press time, late drivers; `shipments.dest_zone` set at label time | backend-engineer (production, shipping) | `src/modules/analytics/operations*.ts`, `src/modules/shipping/**` (zone only), `db/schema/shipping.ts` + migration | backend-foundation, security-reviewer (no address stored), data-analyst | tenancy, migration, pii |
| T-A5 Inventory and design analytics: turns, dead stock, size mix, stockout exposure, supplier trends, design lifecycle; size-split suggestion on reorder | backend-engineer (inventory) | `src/modules/analytics/inventory*.ts`, `src/modules/inventory/reorder.ts` (size split only) | architect (cross-module), data-analyst | tenancy |

### Wave A2: screens, assistant, digest, Today (in scope; PM confirms)
| Card | Owner | Scope | Co-reviewers | Flags |
|---|---|---|---|---|
| T-A6 Web Profit v2: contribution view, losing orders, leakage waterfall, shipping profit tab, why-changed bridge, break-even card, fixed-cost setting, CSV on each | web-engineer | `invai-web/src/routes/_app/analytics/**`, `settings/costs.tsx` | product-designer, qa-engineer | ui |
| T-A7 Web Operations and Inventory health screens, design lifecycle column on Designs | web-engineer | new `analytics/operations.tsx`, `analytics/inventory.tsx`, `catalog/designs.index.tsx` (column) | product-designer | ui |
| T-A8 Assistant tools v6 + prompt v6 ("why" with evidence) + evals | ai-engineer | `src/modules/ai/**`, `src/ai/**`, `evals/assistant/**` | security-reviewer (injection, tenancy), data-analyst | ai, tenancy |
| T-A9 Digest D9–D13 and D2 bridge mover; en/es templates | backend-engineer (digest) | `src/modules/digest/**` | product-manager (wording), data-analyst | data-integrity |
| T-A10 Today actions panel (daily detectors, ranked, clicks) | backend-engineer (today) + web-engineer | `src/modules/today/**`, `invai-web/src/routes/_app/index.tsx` (panel) | qa-engineer (golden path), product-designer | ui, golden path |

### Wave A3: gated items (only after the owner's answer and a PM scope change)
| Card | Owner | Gate |
|---|---|---|
| T-A11 Goals and targets with pace | architect + backend-engineer + web-engineer | owner yes (new surface) |
| T-A12 Anomaly alerts (robust z, ≥ 8 weeks) | backend-engineer (today) | owner yes; 8 weeks of history per shop |
| T-A13 Customer analytics (keyed buyer id, repeat, cohorts, LTV, RFM) | backend-foundation (buyer key) + backend-engineer + web-engineer | owner yes + compliance-officer review (Amazon excluded; Etsy clause) + threat model |
| T-A14 Cash view (= B-152; horizon set by the PM) | backend-engineer (finance) + web-engineer | owner yes |
| T-A15 Scheduled report emails | backend-foundation + web-engineer | OI-12, OI-13, OI-14 answered |

## Success metrics
- `action_adoption_rate` (`metrics/definitions/action_adoption_rate.md`): ≥ 30% of analytics actions clicked after 4 pilot weeks; a detector under 10% for 4 weeks with ≥ 30 shown is reviewed.
- Weekly active use of an analytics view by the owner or office in ≥ 60% of pilot shops (needs the analytics event taxonomy, `metrics/events.md`, to be written).
- Pilot-level money outcomes (read out with `experiment-readout`, before/after per shop, counts only): shipping margin per order, reprint cost, film waste, dead stock value.

## Open questions
1. ~~PM: are tracks A–C inside items 5–8, 13, 14, 17 as argued here, or does any need its own scope line?~~ **Answered 2026-09-30 (product-manager):** yes. B-168..B-177 (Tracks A–C, waves A1/A2) fit inside scope items 5, 6, 7, 8, 13, 14 and 17 with no fence violation; full row-by-row check in `waves/analytics-scope-check.md`. B-178..B-181 (Track D) stay out of A1/A2, gated on owner-inbox OI-18 (and B-181 additionally on OI-12/13/14); this spec's Track D section already reflects that fence correctly and needs no change.
2. Compliance-officer: does Etsy's API Terms "no analytics" clause cover a seller's own repeat-buyer counts computed inside the seller's tool? (Before T-A13.)
3. ~~Integrations-engineer: does the Amazon CSV carry shipping credits?~~ **Resolved (wave 22, T-22-3, B-183):** no parser bug; the Amazon export genuinely carries no separate shipping line for these orders. `shipping_margin.md`'s caveat stands; follow-ups tracked as B-197, B-198.
4. Owner: may shop-facing analytics ever show one named presser's speed? (Default: stations only.)
5. Architect: a nightly rollup table (`analytics_daily` per shop) now, or only if AC-G2 fails?

## Review log (product-manager, 2026-09-30)
- Scope: confirmed by product-manager, see open question 1 and `waves/analytics-scope-check.md`. Track D fenced on OI-18 (not approved); nothing in waves A1/A2 needs a scope change.
- **product-designer (flow):** verdict **changes-required** (`waves/A1/reviews/business-analytics-v2-product-designer.md`), 4 blocking findings: no zero-labeled-shipments state (AC-A3), no screen-level "too little history" state for Operations/Inventory/Design (distinct from per-metric thresholds), D10-D13 had no acceptance criteria, AC-E2 didn't cover the zero-actions/healthy-week state. **All four fixed in this edit**: AC-A3 extended; new AC-B/C-screen1 added (`hasEnoughHistory` flag on `operations`, `inventoryHealth`, `designLifecycle`); AC-E1b..E1f added for D10-D13 and the D2 bridge-mover; AC-E2 extended with the zero-actions state.
- **qa-engineer (testability):** verdict **changes-required** (`waves/A1/reviews/business-analytics-v2-qa-engineer.md`), 4 blocking findings: T-A1 (seed) had no numeric acceptance criterion of its own, `analytics.supplierTrends` had no AC, D10-D13 had no ACs (same gap product-designer found), AC-G1's parity wasn't one unambiguous assertion (period boundary and channel/dimension filter unstated). **All four fixed in this edit**: new AC-Seed1 with numeric thresholds; new AC-C5 for supplierTrends; AC-E1b..E1f (as above); AC-G1 rewritten to pin the digest's last-completed week, no channel filter, `dimension: order` as the comparable case, with a second named per-channel case.
- Both reviewers' non-blocking notes (en/es per-surface ACs, AC-C1's exclusion-vs-"not enough data" wording, thin coverage on 3 of 5 v6 tools) are left for the wave A2 UX-spec and card-writing stage; none blocks A1/A2 carding.
- customer-success (evidence): not run as a separate review this round (PM budget, per task-intake direction); evidence is the owner's direction (2026-09-28, 0 pilots live yet, quoted in "Problem and evidence" above) plus research pain #6/#7/#8/#1/#5 citations already in the spec. No pilot-specific claim is made beyond what's cited; flag to customer-success for a light evidence pass once pilots are live and Track D evidence is needed.
