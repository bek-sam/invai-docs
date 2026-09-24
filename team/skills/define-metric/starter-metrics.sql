-- Starter SQL for InvAI's core pilot metrics. Tested 2026-09-24 against the local dev DB
-- (seed shop) as the table owner:
--   docker exec -i local-postgres-1 psql -U invai -d invai -v from=2026-08-25 -v to=2026-09-25 < starter-metrics.sql
-- Local only. In any shared or deployed environment, metrics read through approved,
-- PII-free views (to be created by the data-analyst), never buyer_pii or raw payloads.
-- Each query groups by company_id so segment cuts can join a shop-segment table later.

-- late_rate: orders shipped after InvAI's ship_by, of orders shipped in the window
SELECT o.company_id, o.channel,
  count(*) AS shipped,
  count(*) FILTER (WHERE o.shipped_at > o.ship_by) AS shipped_late,
  round(100.0 * count(*) FILTER (WHERE o.shipped_at > o.ship_by) / nullif(count(*), 0), 1) AS late_rate_pct
FROM orders o
WHERE o.shipped_at >= :'from' AND o.shipped_at < :'to'
GROUP BY 1, 2 ORDER BY 1, 2;

-- overdue_open: orders past ship_by and still not shipped or cancelled, right now
SELECT company_id, channel, count(*) AS overdue_open
FROM orders
WHERE shipped_at IS NULL AND cancelled_at IS NULL AND ship_by < now()
GROUP BY 1, 2 ORDER BY 1, 2;

-- film_use: length-weighted utilization of sheets that went to the vendor (includes each
-- batch's short last sheet, because the shop pays for that film too)
SELECT company_id, count(*) AS sheets,
  round((100 * sum(utilization * length_in) / nullif(sum(length_in), 0))::numeric, 1) AS film_use_pct
FROM gang_sheets
WHERE created_at >= :'from' AND created_at < :'to'
  AND status IN ('sent', 'acknowledged', 'printed', 'shipped', 'received')
GROUP BY 1;

-- reprint_rate: reprints requested / distinct items that reached pressed in the window
WITH pressed AS (
  SELECT company_id, count(DISTINCT order_item_id) AS n FROM order_item_transitions
  WHERE to_state = 'pressed' AND created_at >= :'from' AND created_at < :'to' GROUP BY 1),
rp AS (
  SELECT company_id, count(*) AS n FROM reprints
  WHERE requested_at >= :'from' AND requested_at < :'to' GROUP BY 1)
SELECT p.company_id, coalesce(rp.n, 0) AS reprints, p.n AS items_pressed,
  round(100.0 * coalesce(rp.n, 0) / nullif(p.n, 0), 1) AS reprint_rate_pct
FROM pressed p LEFT JOIN rp USING (company_id);

-- reprint reasons (REPRINT_REASONS in invai-contracts/src/schemas/production.ts)
SELECT company_id, reason, count(*) FROM reprints
WHERE requested_at >= :'from' AND requested_at < :'to'
GROUP BY 1, 2 ORDER BY 1, 3 DESC;

-- scan_block_rate: floor scans that blocked, by station and reason (MISMATCH_REASONS)
SELECT company_id, station, coalesce(mismatch, 'ok') AS result, count(*) AS scans
FROM scans WHERE scanned_at >= :'from' AND scanned_at < :'to'
GROUP BY 1, 2, 3 ORDER BY 1, 2, 4 DESC;

-- label_attach_rate: shipped orders whose label was bought in InvAI
SELECT o.company_id, count(DISTINCT o.id) AS shipped_orders,
  count(DISTINCT sh.order_id) FILTER (WHERE sh.labeled_at IS NOT NULL AND sh.voided_at IS NULL) AS labeled_in_invai
FROM orders o LEFT JOIN shipments sh ON sh.order_id = o.id
WHERE o.shipped_at >= :'from' AND o.shipped_at < :'to'
GROUP BY 1;
