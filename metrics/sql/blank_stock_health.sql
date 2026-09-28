-- blank_turns and dead_stock_value v1 (metrics/definitions/blank_stock_health.md)
-- Per shop, as of now, trailing :'days' days (default use 90):
--   consumed units (inventory_movements kind 'consume', qty is negative), on hand now, stock value
--   at blank_variants.cost_cents, annualized turns = consumed cost * 365/days / on-hand value,
--   dead stock = on-hand units of variants with no consumption in the window (value in cents),
--   days of cover per variant are in inventory.reorderSuggestions (not repeated here).
WITH shops AS (
  SELECT id AS company_id, slug, timezone FROM companies
  WHERE type = 'shop' AND deleted_at IS NULL AND demo_owner_user_id IS NULL
    AND (settings->>'demoRetiredAt') IS NULL),
cons AS (
  SELECT m.company_id, m.blank_variant_id, -sum(m.qty) AS used
  FROM inventory_movements m WHERE m.kind = 'consume'
    AND m.created_at >= now() - make_interval(days => :'days'::int) GROUP BY 1, 2),
stock AS (
  SELECT sl.company_id, sl.blank_variant_id, sum(sl.on_hand) AS on_hand FROM stock_levels sl GROUP BY 1, 2)
SELECT s.slug,
  sum(st.on_hand) AS on_hand_units,
  sum(st.on_hand * bv.cost_cents) AS on_hand_value_cents,
  coalesce(sum(c.used * bv.cost_cents), 0) AS consumed_cost_cents,
  round((coalesce(sum(c.used * bv.cost_cents), 0) * 365.0 / :'days'::int
        / nullif(sum(st.on_hand * bv.cost_cents), 0))::numeric, 1) AS turns_per_year,
  count(*) FILTER (WHERE st.on_hand > 0 AND c.used IS NULL) AS dead_variants,
  coalesce(sum(st.on_hand * bv.cost_cents) FILTER (WHERE st.on_hand > 0 AND c.used IS NULL), 0) AS dead_stock_value_cents
FROM shops s JOIN stock st ON st.company_id = s.company_id
JOIN blank_variants bv ON bv.id = st.blank_variant_id
LEFT JOIN cons c ON c.company_id = st.company_id AND c.blank_variant_id = st.blank_variant_id
GROUP BY 1 ORDER BY 1;
