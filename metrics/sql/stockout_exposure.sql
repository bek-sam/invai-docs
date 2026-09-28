-- stockout_exposure v1 (metrics/definitions/stockout_exposure.md)
-- Right now: open, not-yet-pressed units whose blank variant has no available stock at any
-- location (sum of stock_levels.available <= 0), with the revenue those units carry
-- (order_items.unit_price_cents) and the oldest ship-by among them. These are the units a
-- stockout delays; the digest D7 and Today alert look forward, this looks at units already sold.
WITH shops AS (
  SELECT id AS company_id, slug, timezone FROM companies
  WHERE type = 'shop' AND deleted_at IS NULL AND demo_owner_user_id IS NULL
    AND (settings->>'demoRetiredAt') IS NULL),
avail AS (SELECT blank_variant_id, sum(available) AS available FROM stock_levels GROUP BY 1)
SELECT s.slug, count(oi.id) AS units_waiting_on_blank, count(DISTINCT oi.blank_variant_id) AS blanks_out,
  coalesce(sum(oi.unit_price_cents), 0) AS revenue_at_risk_cents, min(oi.ship_by) AS earliest_ship_by
FROM shops s LEFT JOIN order_items oi ON oi.company_id = s.company_id
  AND oi.state IN ('ready', 'needs_artwork', 'on_sheet', 'transfer_in')
  AND oi.blank_variant_id IN (SELECT blank_variant_id FROM avail WHERE available <= 0)
GROUP BY 1 ORDER BY 1;
