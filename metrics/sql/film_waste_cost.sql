-- film_waste_cost v1 (metrics/definitions/film_waste_cost.md)
-- Money spent on DTF film that carried no transfer: sheet cost x (1 - utilization), for sheets
-- that went to the vendor (sent or later), by sheet created_at, shop tz. Also film_use (length-
-- weighted utilization, same rule as .claude/skills/define-metric/starter-metrics.sql).
WITH shops AS (
  SELECT id AS company_id, slug, timezone FROM companies
  WHERE type = 'shop' AND deleted_at IS NULL AND demo_owner_user_id IS NULL
    AND (settings->>'demoRetiredAt') IS NULL),
w AS (SELECT s.*, (:'from'::date::timestamp AT TIME ZONE s.timezone) AS f,
             (:'to'::date::timestamp AT TIME ZONE s.timezone) AS t FROM shops s)
SELECT w.slug, count(g.id) AS sheets, coalesce(sum(g.cost_cents), 0) AS film_cost_cents,
  round(coalesce(sum(g.cost_cents * (1 - g.utilization)), 0))::int AS film_waste_cents,
  round((100 * sum(g.utilization * g.length_in) / nullif(sum(g.length_in), 0))::numeric, 1) AS film_use_pct,
  count(g.id) FILTER (WHERE g.cost_cents IS NULL OR g.cost_cents = 0) AS sheets_without_cost
FROM w LEFT JOIN gang_sheets g ON g.company_id = w.company_id AND g.created_at >= w.f AND g.created_at < w.t
  AND g.status IN ('sent', 'acknowledged', 'printing', 'printed', 'shipped', 'received')
GROUP BY 1 ORDER BY 1;
