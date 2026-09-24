-- Dry-run measurements. Run against the ISOLATED dry-run database only:
--   docker exec -i local-postgres-1 psql -U invai -d invai_dryrun_<slug> < queries.sql
-- Column names checked against invai-backend/src/db/schema (snake_case) on 2026-09-24.

-- 1. Parse rate per import run (and channel format)
SELECT r.format, r.started_at, r.rows_total, r.rows_failed,
       r.orders_imported, r.orders_updated, r.orders_skipped, r.items_needing_mapping,
       round(100.0 * (r.rows_total - r.rows_failed) / nullif(r.rows_total, 0), 1) AS parse_rate_pct
FROM import_runs r
ORDER BY r.started_at;

-- Failed-row messages (no buyer data is stored here, but check before copying out)
SELECT r.format, e->>'index' AS row_index, e->>'message' AS message
FROM import_runs r, jsonb_array_elements(r.errors::jsonb) e
ORDER BY r.started_at;

-- 2. SKU auto-map rate per channel (run before and after adding rules)
SELECT o.channel,
       count(*) AS items,
       count(*) FILTER (WHERE i.state = 'needs_mapping') AS unmapped,
       round(100.0 * count(*) FILTER (WHERE i.state <> 'needs_mapping') / count(*), 1) AS auto_map_pct
FROM order_items i JOIN orders o ON o.id = i.order_id
GROUP BY o.channel ORDER BY o.channel;

-- Unmapped SKU patterns, most common first (explain each one in the report)
SELECT o.channel, i.channel_sku, count(*) AS items
FROM order_items i JOIN orders o ON o.id = i.order_id
WHERE i.state = 'needs_mapping'
GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 50;

-- 3. Ship-by: InvAI's computed date per order, to compare with the marketplace's own date
SELECT o.channel, o.order_no, o.placed_at, o.ship_by, o.is_rush, o.shipping_method
FROM orders o ORDER BY o.channel, o.placed_at LIMIT 200;

-- 4. Personalization: items with answers and artwork flags (sample 20 per channel by hand)
SELECT o.channel, o.order_no, i.personalization, i.artwork_status, i.flags
FROM order_items i JOIN orders o ON o.id = i.order_id
WHERE o.has_personalization
ORDER BY o.channel, o.order_no LIMIT 100;
-- NOTE: personalization text can contain buyer names. Read it here; never paste it into the repo.
