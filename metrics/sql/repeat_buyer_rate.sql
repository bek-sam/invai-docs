-- repeat_buyer_rate v1 DRAFT (metrics/definitions/repeat_buyer_rate.md) -- gated, see caveats
-- Of distinct buyers (orders.buyer_ref, a company-scoped hash; never decoded, never output) with a
-- first order in the cohort window, the share who ordered again within :'days' days of their first
-- order. Amazon is excluded (buyer data may be used only to fulfil the order; DPP 30-day PII rule).
-- Output is counts per shop and channel only: no buyer_ref values leave the query.
WITH shops AS (
  SELECT id AS company_id, slug, timezone FROM companies
  WHERE type = 'shop' AND deleted_at IS NULL AND demo_owner_user_id IS NULL
    AND (settings->>'demoRetiredAt') IS NULL),
o AS (
  SELECT s.slug, o.channel, o.buyer_ref, o.placed_at
  FROM shops s JOIN orders o ON o.company_id = s.company_id
  WHERE o.buyer_ref IS NOT NULL AND o.status <> 'cancelled' AND o.channel <> 'amazon'),
firsts AS (SELECT slug, buyer_ref, min(placed_at) AS first_at, (array_agg(channel ORDER BY placed_at))[1] AS first_channel
           FROM o GROUP BY 1, 2)
SELECT f.slug, f.first_channel, count(*) AS new_buyers,
  count(*) FILTER (WHERE EXISTS (SELECT 1 FROM o x WHERE x.slug = f.slug AND x.buyer_ref = f.buyer_ref
     AND x.placed_at > f.first_at AND x.placed_at <= f.first_at + make_interval(days => :'days'::int))) AS repeat_buyers,
  CASE WHEN count(*) >= 30 THEN round(100.0 * count(*) FILTER (WHERE EXISTS (SELECT 1 FROM o x WHERE x.slug = f.slug
     AND x.buyer_ref = f.buyer_ref AND x.placed_at > f.first_at
     AND x.placed_at <= f.first_at + make_interval(days => :'days'::int))) / count(*), 1) END AS repeat_rate_pct
FROM firsts f
WHERE f.first_at >= :'from'::date AND f.first_at < :'to'::date
GROUP BY 1, 2 ORDER BY 1, 2;
