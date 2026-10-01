-- size_mix_gap v1 (metrics/definitions/size_mix_gap.md)
-- Per blank style x color: each size's share of units sold (non-cancelled order items; a reprinted
-- unit still counts, decision 0020) placed in the last :'days' days against its share of on-hand
-- stock. gap_pts = stock share -
-- sales share, in percentage points. Positive = over-stocked size, negative = under-stocked.
-- Only style x color groups with >= 30 units sold are shown (minimum sample).
WITH shops AS (
  SELECT id AS company_id, slug, timezone FROM companies
  WHERE type = 'shop' AND deleted_at IS NULL AND demo_owner_user_id IS NULL
    AND (settings->>'demoRetiredAt') IS NULL),
sold AS (
  SELECT oi.company_id, oi.blank_variant_id, count(*) AS units
  FROM order_items oi JOIN orders o ON o.id = oi.order_id
  WHERE oi.state <> 'cancelled' AND oi.blank_variant_id IS NOT NULL
    AND o.placed_at >= now() - make_interval(days => :'days'::int)
  GROUP BY 1, 2),
stock AS (SELECT company_id, blank_variant_id, sum(on_hand) AS on_hand FROM stock_levels GROUP BY 1, 2),
v AS (
  SELECT s.slug, bv.style_code, bv.color, bv.size, coalesce(so.units, 0) AS units, coalesce(st.on_hand, 0) AS on_hand
  FROM shops s JOIN blank_variants bv ON bv.company_id = s.company_id
  LEFT JOIN sold so ON so.blank_variant_id = bv.id
  LEFT JOIN stock st ON st.blank_variant_id = bv.id),
g AS (
  SELECT v.*, sum(units) OVER (PARTITION BY slug, style_code, color) AS g_units,
              sum(on_hand) OVER (PARTITION BY slug, style_code, color) AS g_stock FROM v)
SELECT slug, style_code, color, size, units, on_hand,
  round(100.0 * units / nullif(g_units, 0), 1) AS sales_share_pct,
  round(100.0 * on_hand / nullif(g_stock, 0), 1) AS stock_share_pct,
  round(100.0 * on_hand / nullif(g_stock, 0) - 100.0 * units / nullif(g_units, 0), 1) AS gap_pts
FROM g WHERE g_units >= 30
ORDER BY slug, style_code, color, abs(100.0 * on_hand / nullif(g_stock, 0) - 100.0 * units / nullif(g_units, 0)) DESC NULLS LAST
LIMIT 20;
