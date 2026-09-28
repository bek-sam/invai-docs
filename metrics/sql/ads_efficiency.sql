-- mer and breakeven_roas v1 (metrics/definitions/ads_efficiency.md)
-- MER (blended) = all revenue / all ad spend in the window (shop tz), every channel, ad_spend by day.
-- Channel ROAS = channel revenue / channel ad spend (same as get_ad_performance).
-- Break-even ROAS = 1 / CM2 ratio (CM2 = contribution before ads, contribution_margin.md): the
-- ROAS below which ads lose money on the channel at today's margins.
WITH shops AS (
  SELECT id AS company_id, slug, timezone FROM companies
  WHERE type = 'shop' AND deleted_at IS NULL AND demo_owner_user_id IS NULL
    AND (settings->>'demoRetiredAt') IS NULL),
w AS (SELECT s.*, (:'from'::date::timestamp AT TIME ZONE s.timezone) AS f,
             (:'to'::date::timestamp AT TIME ZONE s.timezone) AS t FROM shops s),
rev AS (
  SELECT w.slug, pl.channel, sum(pl.revenue_cents) AS revenue,
    sum(pl.net_cents + pl.ads_cost_cents) AS cm2
  FROM w JOIN profit_lines pl ON pl.company_id = w.company_id AND pl.placed_at >= w.f AND pl.placed_at < w.t
  GROUP BY 1, 2),
ads AS (
  SELECT w.slug, a.channel, sum(a.amount_cents) AS spend
  FROM w JOIN ad_spend a ON a.company_id = w.company_id AND a.day >= :'from'::date AND a.day < :'to'::date
  GROUP BY 1, 2),
j AS (SELECT coalesce(r.slug, a.slug) AS slug, coalesce(r.channel, a.channel) AS channel,
             coalesce(r.revenue, 0) AS revenue, coalesce(r.cm2, 0) AS cm2, coalesce(a.spend, 0) AS spend
      FROM rev r FULL JOIN ads a ON a.slug = r.slug AND a.channel = r.channel)
SELECT slug, channel, revenue AS revenue_cents, spend AS ad_spend_cents,
  round(revenue::numeric / nullif(spend, 0), 2) AS roas,
  round(revenue::numeric / nullif(cm2, 0), 2) AS breakeven_roas,
  cm2 - spend AS cm3_cents
FROM j
UNION ALL
SELECT slug, 'ALL (MER)', sum(revenue), sum(spend), round(sum(revenue)::numeric / nullif(sum(spend), 0), 2),
  round(sum(revenue)::numeric / nullif(sum(cm2), 0), 2), sum(cm2) - sum(spend)
FROM j GROUP BY slug ORDER BY 1, 2;
