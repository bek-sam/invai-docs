-- reprint_cost v1 (metrics/definitions/reprint_cost.md)
-- Estimated cost of reprints requested in the window, by reason: one more transfer (the item's
-- transfer cost split over its prints) plus the blank when blank_consumed. Same rule as
-- fulfillmentHealth (invai-backend/src/modules/ai/analyst-queries.ts). Rate per item pressed uses
-- the starter reprint_rate denominator (distinct items that reached `pressed`).
WITH shops AS (
  SELECT id AS company_id, slug, timezone FROM companies
  WHERE type = 'shop' AND deleted_at IS NULL AND demo_owner_user_id IS NULL
    AND (settings->>'demoRetiredAt') IS NULL),
w AS (SELECT s.*, (:'from'::date::timestamp AT TIME ZONE s.timezone) AS f,
             (:'to'::date::timestamp AT TIME ZONE s.timezone) AS t FROM shops s),
pressed AS (
  SELECT w.slug, count(DISTINCT tr.order_item_id) AS n
  FROM w JOIN order_item_transitions tr ON tr.company_id = w.company_id AND tr.to_state = 'pressed'
   AND tr.created_at >= w.f AND tr.created_at < w.t GROUP BY 1)
SELECT w.slug, rp.reason, count(*) AS reprints, p.n AS items_pressed,
  round(100.0 * count(*) / nullif(p.n, 0), 1) AS rate_pct,
  sum(CASE WHEN rp.blank_consumed THEN coalesce(pl.blank_cost_cents, 0) ELSE 0 END
      + coalesce(pl.transfer_cost_cents, 0) / (1 + (SELECT count(*) FROM reprints r2
          WHERE r2.order_item_id = rp.order_item_id AND r2.status <> 'cancelled')))::int AS cost_cents
FROM w JOIN reprints rp ON rp.company_id = w.company_id AND rp.status <> 'cancelled'
  AND rp.requested_at >= w.f AND rp.requested_at < w.t
LEFT JOIN profit_lines pl ON pl.order_item_id = rp.order_item_id
LEFT JOIN pressed p ON p.slug = w.slug
GROUP BY 1, 2, 4 ORDER BY 1, 3 DESC;
