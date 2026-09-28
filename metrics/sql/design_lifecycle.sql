-- design_lifecycle_stage v1 (metrics/definitions/design_lifecycle_stage.md)
-- Per design with an active listing or a sale in the last 365 days, as of :'asof' (shop tz):
--   units last 4 weeks (u4), the 4 weeks before (p4), weeks since first sale, days since last sale.
-- Stage (first rule that matches):
--   dead     : active listing, no sale in 60 days (or never sold and listed >= 60 days ago is not
--              knowable today: listings has no created date, so "never sold" counts as dead)
--   new      : first sale < 8 weeks ago
--   growing  : u4 >= 3 and u4 >= 1.25 * p4
--   declining: p4 >= 3 and u4 <= 0.75 * p4
--   steady   : everything else with a sale in 60 days
-- Units exclude reprints and cancelled items (one order item = one unit).
WITH shops AS (
  SELECT id AS company_id, slug, timezone FROM companies
  WHERE type = 'shop' AND deleted_at IS NULL AND demo_owner_user_id IS NULL
    AND (settings->>'demoRetiredAt') IS NULL),
w AS (SELECT s.*, (:'asof'::date::timestamp AT TIME ZONE s.timezone) AS t FROM shops s),
sales AS (
  SELECT w.slug, oi.design_id,
    count(*) FILTER (WHERE o.placed_at >= w.t - interval '28 days') AS u4,
    count(*) FILTER (WHERE o.placed_at >= w.t - interval '56 days' AND o.placed_at < w.t - interval '28 days') AS p4,
    min(o.placed_at) AS first_sale, max(o.placed_at) AS last_sale
  FROM w JOIN order_items oi ON oi.company_id = w.company_id AND oi.design_id IS NOT NULL
   AND NOT oi.is_reprint AND oi.state <> 'cancelled'
  JOIN orders o ON o.id = oi.order_id AND o.placed_at < w.t AND o.placed_at >= w.t - interval '365 days'
  GROUP BY 1, 2),
listed AS (
  SELECT DISTINCT w.slug, l.design_id FROM w
  JOIN listings l ON l.company_id = w.company_id AND l.state = 'active' AND l.design_id IS NOT NULL),
d AS (
  SELECT coalesce(s.slug, l.slug) AS slug, coalesce(s.design_id, l.design_id) AS design_id,
    coalesce(s.u4, 0) AS u4, coalesce(s.p4, 0) AS p4, s.first_sale, s.last_sale, l.design_id IS NOT NULL AS listed
  FROM sales s FULL JOIN listed l ON l.slug = s.slug AND l.design_id = s.design_id),
staged AS (
  SELECT d.*, w.t,
    CASE
      WHEN listed AND (last_sale IS NULL OR last_sale < w.t - interval '60 days') THEN 'dead'
      WHEN first_sale >= w.t - interval '56 days' THEN 'new'
      WHEN u4 >= 3 AND u4 >= 1.25 * p4 THEN 'growing'
      WHEN p4 >= 3 AND u4 <= 0.75 * p4 THEN 'declining'
      WHEN last_sale >= w.t - interval '60 days' THEN 'steady'
      ELSE 'inactive' END AS stage
  FROM d JOIN w ON w.slug = d.slug)
SELECT slug, stage, count(*) AS designs, sum(u4) AS units_last_4w
FROM staged GROUP BY 1, 2 ORDER BY 1, 2;
