-- break_even_orders v1 (metrics/definitions/break_even.md)
-- Orders per month needed to cover the shop's fixed monthly costs at the trailing window's
-- contribution per order (CM3 per order, the Profit page's Net / orders).
-- Fixed costs are not stored today: pass them with -v fixed_cents=... (spec card T-A2 adds
-- cost_settings.fixed_monthly_cents). Pace = orders in the window scaled to 30 days.
WITH shops AS (
  SELECT id AS company_id, slug, timezone FROM companies
  WHERE type = 'shop' AND deleted_at IS NULL AND demo_owner_user_id IS NULL
    AND (settings->>'demoRetiredAt') IS NULL),
w AS (SELECT s.*, (:'from'::date::timestamp AT TIME ZONE s.timezone) AS f,
             (:'to'::date::timestamp AT TIME ZONE s.timezone) AS t,
             (:'to'::date - :'from'::date) AS days FROM shops s),
x AS (
  SELECT w.slug, w.days, count(DISTINCT pl.order_id) AS orders, sum(pl.net_cents) AS net
  FROM w JOIN profit_lines pl ON pl.company_id = w.company_id AND pl.placed_at >= w.f AND pl.placed_at < w.t
  GROUP BY 1, 2)
SELECT slug, orders, net AS cm3_cents, round(net::numeric / nullif(orders, 0)) AS cm3_per_order_cents,
  :'fixed_cents'::bigint AS fixed_monthly_cents,
  ceil(:'fixed_cents'::bigint / nullif(net::numeric / nullif(orders, 0), 0)) AS break_even_orders_per_month,
  round(orders * 30.0 / days) AS pace_orders_per_month,
  round(net * 30.0 / days) - :'fixed_cents'::bigint AS operating_profit_pace_cents
FROM x ORDER BY 1;
