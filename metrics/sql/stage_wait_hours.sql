-- stage_wait_hours v1 (metrics/definitions/stage_wait_hours.md)
-- Where work waits: for items that entered a state in the window, hours until they left it
-- (next transition), median and p90 per state. The state with the largest median wait on the
-- critical path (ready -> on_sheet -> transfer_in -> pressed -> packed -> shipped) is the bottleneck.
-- Items still in the state are measured to now() and counted as `still_waiting`.
WITH shops AS (
  SELECT id AS company_id, slug, timezone FROM companies
  WHERE type = 'shop' AND deleted_at IS NULL AND demo_owner_user_id IS NULL
    AND (settings->>'demoRetiredAt') IS NULL),
w AS (SELECT s.*, (:'from'::date::timestamp AT TIME ZONE s.timezone) AS f,
             (:'to'::date::timestamp AT TIME ZONE s.timezone) AS t FROM shops s),
tr AS (
  SELECT w.slug, x.to_state, x.created_at, x.left_at
  FROM w JOIN (SELECT company_id, order_item_id, to_state, created_at,
                      lead(created_at) OVER (PARTITION BY order_item_id ORDER BY created_at) AS left_at
               FROM order_item_transitions) x
    ON x.company_id = w.company_id AND x.created_at >= w.f AND x.created_at < w.t
  WHERE x.to_state IN ('needs_mapping', 'needs_artwork', 'ready', 'on_sheet', 'transfer_in', 'pressed', 'packed'))
SELECT slug, to_state AS state, count(*) AS entries, count(*) FILTER (WHERE left_at IS NULL) AS still_waiting,
  round((percentile_cont(0.5) WITHIN GROUP (ORDER BY extract(epoch FROM coalesce(left_at, now()) - created_at) / 3600))::numeric, 1) AS median_h,
  round((percentile_cont(0.9) WITHIN GROUP (ORDER BY extract(epoch FROM coalesce(left_at, now()) - created_at) / 3600))::numeric, 1) AS p90_h
FROM tr GROUP BY 1, 2 ORDER BY 1, array_position(ARRAY['needs_mapping','needs_artwork','ready','on_sheet','transfer_in','pressed','packed'], to_state::text);
