-- losing_order_rate v1 (metrics/definitions/losing_order_rate.md)
-- Orders placed in the window whose CM2 (before ads) is below zero, of orders with a profit line.
-- Refund events are attached to their order regardless of refund date (order view, not period P&L).
-- Reprint lines are included: a reprint's extra cost is what often makes an order lose money.
WITH shops AS (
  SELECT id AS company_id, slug, timezone FROM companies
  WHERE type = 'shop' AND deleted_at IS NULL AND demo_owner_user_id IS NULL
    AND (settings->>'demoRetiredAt') IS NULL),
w AS (SELECT s.*, (:'from'::date::timestamp AT TIME ZONE s.timezone) AS f,
             (:'to'::date::timestamp AT TIME ZONE s.timezone) AS t FROM shops s),
o AS (
  SELECT w.slug, pl.order_id, min(pl.channel) AS channel,
    sum(pl.net_cents + pl.ads_cost_cents) AS cm2_lines
  FROM w JOIN profit_lines pl ON pl.company_id = w.company_id
   AND pl.placed_at >= w.f AND pl.placed_at < w.t
  GROUP BY 1, 2),
r AS (SELECT order_id, sum(amount_cents - fee_recovered_cents) AS net_refund
      FROM refund_events WHERE voided_at IS NULL GROUP BY 1)
SELECT o.slug, o.channel, count(*) AS orders,
  count(*) FILTER (WHERE o.cm2_lines - coalesce(r.net_refund, 0) < 0) AS losing_orders,
  round(100.0 * count(*) FILTER (WHERE o.cm2_lines - coalesce(r.net_refund, 0) < 0) / count(*), 1) AS losing_pct,
  coalesce(sum(o.cm2_lines - coalesce(r.net_refund, 0)) FILTER (WHERE o.cm2_lines - coalesce(r.net_refund, 0) < 0), 0) AS loss_cents
FROM o LEFT JOIN r ON r.order_id = o.order_id
GROUP BY 1, 2 ORDER BY 1, 2;
