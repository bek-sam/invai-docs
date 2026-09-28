# Metric definitions (index)

Owner: data-analyst. One file per metric (`define-metric` playbook, template in `.claude/skills/define-metric/template.md`). A changed formula gets a new version line; old reports keep their version.

**Where the SQL lives:** `invai-docs/metrics/sql/<file>.sql`, tested on the local seed. They move to `invai-backend/scripts/analytics/` with backlog B-49; they were kept in `invai-docs` on 2026-09-28 because wave 20 card T-20-5 owns `invai-backend/scripts/**` while it runs. Run locally only:
```
docker exec -i local-postgres-1 psql -U invai -d invai -v from=2026-08-28 -v to=2026-09-29 < invai-docs/metrics/sql/<file>.sql
```
Outside local: approved, aggregated read-only views only (not built yet), never `buyer_pii`.

Every query excludes sample workspaces the same way as `realCompanySql()` and outputs shop slug, channel, ids and numbers only.

| Metric | Label (en) | Owner | SQL | Status |
|---|---|---|---|---|
| [shop_segment](shop_segment.md) | Shop size | product-manager | `shop_segment.sql` | v1 |
| [contribution_margin](contribution_margin.md) | Contribution margin (CM1/CM2/CM3) | product-manager | `contribution_margin.sql` | v1 |
| [losing_order_rate](losing_order_rate.md) | Orders that lost money | product-manager | `losing_orders.sql` | v1 |
| [shipping_margin](shipping_margin.md) | Shipping profit or loss | product-manager | `shipping_margin.sql` | v1 |
| [revenue_leakage](revenue_leakage.md) | Where your sales money goes | product-manager | `revenue_leakage.sql` | v1 |
| [profit_bridge](profit_bridge.md) | Why profit changed | product-manager | `profit_bridge.sql` | v1 |
| [reprint_cost](reprint_cost.md) | Reprint cost | product-manager | `reprint_cost.sql` | v1 |
| [film_waste_cost](film_waste_cost.md) | Wasted film | product-manager | `film_waste_cost.sql` | v1 |
| [late_rate](late_rate.md) | Late shipments (with driver cuts) | customer-success | `late_rate_drivers.sql` | v1 |
| [press_minutes_per_unit](press_minutes_per_unit.md) | Press time per shirt | product-manager | `press_minutes_per_unit.sql` | v1 |
| [stage_wait_hours](stage_wait_hours.md) | Where work waits | product-manager | `stage_wait_hours.sql` | v1 |
| [design_lifecycle_stage](design_lifecycle_stage.md) | Design stage | product-manager | `design_lifecycle.sql` | v1 |
| [blank_stock_health](blank_stock_health.md) | Blank turns and dead stock | product-manager | `blank_stock_health.sql` | v1 |
| [size_mix_gap](size_mix_gap.md) | Size mix vs stock | product-manager | `size_mix_gap.sql` | v1 |
| [stockout_exposure](stockout_exposure.md) | Sold but waiting on blanks | customer-success | `stockout_exposure.sql` | v1 |
| [supplier_trends](supplier_trends.md) | Blank prices and supplier lead time | product-manager | `supplier_trends.sql` | v1 |
| [ads_efficiency](ads_efficiency.md) | MER and break-even ROAS | product-manager | `ads_efficiency.sql` | v1 |
| [break_even](break_even.md) | Break-even orders | product-manager | `break_even.sql` | v1 (needs fixed-cost setting) |
| [repeat_buyer_rate](repeat_buyer_rate.md) | Repeat buyers | product-manager | `repeat_buyer_rate.sql` | DRAFT, gated (OI) |
| [action_adoption_rate](action_adoption_rate.md) | Actions taken | product-manager | `action_adoption.sql` | v1 |

Still to define (starter SQL exists in `.claude/skills/define-metric/starter-metrics.sql`): `overdue_open`, `film_use` (inside film_waste_cost), `reprint_rate` (inside reprint_cost), `scan_block_rate`, `label_attach_rate`, `sku_auto_map_rate`, `minutes_saved`.

Review: product-manager (meaning matches the product question). compliance-officer only when a number reaches public copy.
