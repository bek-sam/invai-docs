-- press_minutes_per_unit v1 (metrics/definitions/press_minutes_per_unit.md)
-- Measured press time per unit: for each station, the gap between consecutive successful press
-- scans, counting only gaps from 6 seconds to 10 minutes (longer gaps are breaks, setup or idle; shorter
-- ones are double scans or synthetic seed rows; both are
-- dropped). Median and p75 minutes per unit, units per active hour, per station.
-- Compare with cost_settings.labor_minutes_per_item (the estimate profit uses today).
WITH shops AS (
  SELECT id AS company_id, slug, timezone FROM companies
  WHERE type = 'shop' AND deleted_at IS NULL AND demo_owner_user_id IS NULL
    AND (settings->>'demoRetiredAt') IS NULL),
w AS (SELECT s.*, (:'from'::date::timestamp AT TIME ZONE s.timezone) AS f,
             (:'to'::date::timestamp AT TIME ZONE s.timezone) AS t FROM shops s),
gaps AS (
  SELECT w.slug, sc.station_id,
    extract(epoch FROM sc.scanned_at - lag(sc.scanned_at) OVER (PARTITION BY sc.station_id ORDER BY sc.scanned_at)) / 60.0 AS gap_min
  FROM w JOIN scans sc ON sc.company_id = w.company_id AND sc.action = 'press' AND sc.ok
   AND sc.scanned_at >= w.f AND sc.scanned_at < w.t)
SELECT g.slug, g.station_id, count(*) FILTER (WHERE gap_min BETWEEN 0.1 AND 10) AS timed_units,
  round(percentile_cont(0.5) WITHIN GROUP (ORDER BY gap_min) FILTER (WHERE gap_min BETWEEN 0.1 AND 10)::numeric, 2) AS median_min,
  round(percentile_cont(0.75) WITHIN GROUP (ORDER BY gap_min) FILTER (WHERE gap_min BETWEEN 0.1 AND 10)::numeric, 2) AS p75_min,
  round((60 * count(*) FILTER (WHERE gap_min BETWEEN 0.1 AND 10) / nullif(sum(gap_min) FILTER (WHERE gap_min BETWEEN 0.1 AND 10), 0))::numeric, 1) AS units_per_active_hour,
  (SELECT cs.labor_minutes_per_item FROM cost_settings cs JOIN companies c ON c.id = cs.company_id WHERE c.slug = g.slug) AS estimate_min
FROM gaps g GROUP BY 1, 2 ORDER BY 1, 2;
