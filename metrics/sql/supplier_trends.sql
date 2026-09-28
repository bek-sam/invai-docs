-- blank_cost_change and supplier_lead_time_days v1 (metrics/definitions/supplier_trends.md)
-- Per supplier and blank style, by month of PO submission: weighted average unit cost on PO lines
-- and median days from submitted_at to received_at (fully received POs only). Cancelled POs excluded.
WITH shops AS (
  SELECT id AS company_id, slug, timezone FROM companies
  WHERE type = 'shop' AND deleted_at IS NULL AND demo_owner_user_id IS NULL
    AND (settings->>'demoRetiredAt') IS NULL)
SELECT s.slug, po.supplier, bv.style_code,
  to_char(po.submitted_at AT TIME ZONE s.timezone, 'YYYY-MM') AS month,
  sum(l.qty) AS units,
  round(sum(l.qty * l.unit_cost_cents)::numeric / nullif(sum(l.qty), 0), 1) AS avg_unit_cost_cents,
  round((percentile_cont(0.5) WITHIN GROUP (ORDER BY extract(epoch FROM po.received_at - po.submitted_at) / 86400)
     FILTER (WHERE po.status = 'received'))::numeric, 1) AS median_lead_days
FROM shops s JOIN purchase_orders po ON po.company_id = s.company_id AND po.status <> 'cancelled'
  AND po.submitted_at IS NOT NULL AND po.submitted_at >= :'from'::date AND po.submitted_at < :'to'::date
JOIN purchase_order_lines l ON l.purchase_order_id = po.id
JOIN blank_variants bv ON bv.id = l.blank_variant_id
GROUP BY 1, 2, 3, 4 ORDER BY 1, 2, 3, 4;
