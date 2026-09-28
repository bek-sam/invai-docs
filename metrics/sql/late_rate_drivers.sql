-- late_rate v1 with driver cuts (metrics/definitions/late_rate.md)
-- Of orders shipped in the window (shipped_at, shop tz; cancelled excluded), the share that
-- shipped after InvAI's ship_by. Cut by the drivers a shop can act on:
--   channel, personalization, rush, multi-unit order, and whether any unit waited > 24 h in
--   needs_mapping or needs_artwork (from order_item_transitions).
WITH shops AS (
  SELECT id AS company_id, slug, timezone FROM companies
  WHERE type = 'shop' AND deleted_at IS NULL AND demo_owner_user_id IS NULL
    AND (settings->>'demoRetiredAt') IS NULL),
w AS (SELECT s.*, (:'from'::date::timestamp AT TIME ZONE s.timezone) AS f,
             (:'to'::date::timestamp AT TIME ZONE s.timezone) AS t FROM shops s),
shipped AS (
  SELECT w.slug, o.id, o.channel, o.has_personalization, o.is_rush, o.item_count > 1 AS multi_unit,
         o.shipped_at > o.ship_by AS late
  FROM w JOIN orders o ON o.company_id = w.company_id AND o.shipped_at >= w.f AND o.shipped_at < w.t
   AND o.status <> 'cancelled'),
blocked AS (
  -- time spent in a blocked state = next transition time - entry time, per item
  SELECT DISTINCT tr.order_id
  FROM (SELECT order_id, order_item_id, to_state, created_at,
               lead(created_at) OVER (PARTITION BY order_item_id ORDER BY created_at) AS left_at
        FROM order_item_transitions) tr
  WHERE tr.to_state IN ('needs_mapping', 'needs_artwork')
    AND coalesce(tr.left_at, now()) - tr.created_at > interval '24 hours'),
cut AS (
  SELECT s.slug, 'channel' AS driver, s.channel AS value, s.late FROM shipped s
  UNION ALL SELECT s.slug, 'personalized', s.has_personalization::text, s.late FROM shipped s
  UNION ALL SELECT s.slug, 'rush', s.is_rush::text, s.late FROM shipped s
  UNION ALL SELECT s.slug, 'multi_unit', s.multi_unit::text, s.late FROM shipped s
  UNION ALL SELECT s.slug, 'blocked_over_24h', (b.order_id IS NOT NULL)::text, s.late
            FROM shipped s LEFT JOIN blocked b ON b.order_id = s.id)
SELECT slug, driver, value, count(*) AS shipped, count(*) FILTER (WHERE late) AS late,
  CASE WHEN count(*) >= 30 THEN round(100.0 * count(*) FILTER (WHERE late) / count(*), 1) END AS late_rate_pct
FROM cut GROUP BY 1, 2, 3 ORDER BY 1, 2, 3;
