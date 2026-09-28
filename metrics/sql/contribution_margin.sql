-- contribution_margin v1 (metrics/definitions/contribution_margin.md)
-- CM1 = revenue - channel fees - blank - transfer            (product margin)
-- CM2 = CM1 - label - packaging - labor - refunds (net of fee recovered)   (after fulfillment)
-- CM3 = CM2 - ads                                              (= the Profit page's "Net")
-- Window: profit lines by placed_at, refund events by refunded_at (same rule as getProfit), shop tz.
-- Cut: by channel. Swap `pl.channel` for design_id / style_code for the other cuts.
WITH shops AS (
  SELECT id AS company_id, slug, timezone FROM companies
  WHERE type = 'shop' AND deleted_at IS NULL AND demo_owner_user_id IS NULL
    AND (settings->>'demoRetiredAt') IS NULL),
w AS (SELECT s.*, (:'from'::date::timestamp AT TIME ZONE s.timezone) AS f,
             (:'to'::date::timestamp AT TIME ZONE s.timezone) AS t FROM shops s),
lines AS (
  SELECT w.slug, pl.channel,
    count(DISTINCT pl.order_id) AS orders,
    sum(pl.revenue_cents) AS revenue,
    sum(pl.channel_fees_cents) AS fees,
    sum(pl.blank_cost_cents + pl.transfer_cost_cents) AS cogs,
    sum(pl.label_cost_cents + pl.packaging_cost_cents + pl.labor_cost_cents) AS fulfil,
    sum(pl.refunds_cents) AS cancel_refunds,
    sum(pl.ads_cost_cents) AS ads,
    sum(pl.net_cents) AS net_lines
  FROM w JOIN profit_lines pl ON pl.company_id = w.company_id
   AND pl.placed_at >= w.f AND pl.placed_at < w.t
  GROUP BY 1, 2),
refs AS (
  SELECT w.slug, r.channel, sum(r.amount_cents) AS refunds, sum(r.fee_recovered_cents) AS recovered
  FROM w JOIN refund_events r ON r.company_id = w.company_id AND r.voided_at IS NULL
   AND r.refunded_at >= w.f AND r.refunded_at < w.t
  GROUP BY 1, 2)
SELECT coalesce(l.slug, r.slug) AS slug, coalesce(l.channel, r.channel) AS channel,
  coalesce(l.orders, 0) AS orders, coalesce(l.revenue, 0) AS revenue_cents,
  coalesce(l.revenue, 0) - coalesce(l.fees, 0) + coalesce(r.recovered, 0) - coalesce(l.cogs, 0) AS cm1_cents,
  coalesce(l.revenue, 0) - coalesce(l.fees, 0) + coalesce(r.recovered, 0) - coalesce(l.cogs, 0)
    - coalesce(l.fulfil, 0) - coalesce(l.cancel_refunds, 0) - coalesce(r.refunds, 0) AS cm2_cents,
  coalesce(l.net_lines, 0) - coalesce(r.refunds, 0) + coalesce(r.recovered, 0) AS cm3_cents,
  round(100.0 * (coalesce(l.net_lines, 0) - coalesce(r.refunds, 0) + coalesce(r.recovered, 0))
        / nullif(l.revenue, 0), 1) AS cm3_pct
FROM lines l FULL JOIN refs r ON r.slug = l.slug AND r.channel = l.channel
ORDER BY 1, 4 DESC;
