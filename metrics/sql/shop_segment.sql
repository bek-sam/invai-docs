-- shop_segment v1 (metrics/definitions/shop_segment.md)
-- Average orders per day over the 28 shop-days before :'asof' (exclusive), cancelled included
-- (they still cost work), sample workspaces excluded. small < 100, mid 100-999, large >= 1000.
WITH shops AS (
  SELECT id AS company_id, slug, timezone FROM companies
  WHERE type = 'shop' AND deleted_at IS NULL AND demo_owner_user_id IS NULL
    AND (settings->>'demoRetiredAt') IS NULL),
w AS (
  SELECT s.*, ((:'asof'::date - 28)::timestamp AT TIME ZONE s.timezone) AS f,
         (:'asof'::date::timestamp AT TIME ZONE s.timezone) AS t
  FROM shops s)
SELECT w.slug, count(o.id) AS orders_28d,
  round(count(o.id) / 28.0, 1) AS orders_per_day,
  CASE WHEN count(o.id) / 28.0 < 100 THEN 'small'
       WHEN count(o.id) / 28.0 < 1000 THEN 'mid' ELSE 'large' END AS segment
FROM w LEFT JOIN orders o ON o.company_id = w.company_id AND o.placed_at >= w.f AND o.placed_at < w.t
GROUP BY w.slug ORDER BY w.slug;
