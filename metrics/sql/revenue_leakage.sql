-- revenue_leakage v1 (metrics/definitions/revenue_leakage.md)
-- Money that leaves between the list price and the shop's pocket, per channel, as cents and as a
-- share of gross sales (subtotal + shipping charged, before discounts):
--   discounts, channel fees (after fees recovered on refunds), refunds, shipping loss (label cost
--   above shipping charged; labeled orders only), reprint cost (estimate, same rule as
--   fulfillmentHealth in invai-backend/src/modules/ai/analyst-queries.ts).
-- Only orders that have profit lines count (fees come from profit lines); the rest are reported
-- as orders_without_profit_line so the number is never silently partial.
-- Orders by placed_at; refunds by refunded_at; reprints by requested_at; shop tz.
WITH shops AS (
  SELECT id AS company_id, slug, timezone FROM companies
  WHERE type = 'shop' AND deleted_at IS NULL AND demo_owner_user_id IS NULL
    AND (settings->>'demoRetiredAt') IS NULL),
w AS (SELECT s.*, (:'from'::date::timestamp AT TIME ZONE s.timezone) AS f,
             (:'to'::date::timestamp AT TIME ZONE s.timezone) AS t FROM shops s),
ord AS (
  SELECT w.slug, o.channel,
    count(*) FILTER (WHERE has_pl) AS orders,
    count(*) FILTER (WHERE NOT has_pl) AS orders_without_profit_line,
    sum(o.subtotal_cents + o.shipping_cents) FILTER (WHERE has_pl) AS gross,
    sum(o.discount_cents) FILTER (WHERE has_pl) AS discounts
  FROM w JOIN (SELECT o.*, EXISTS (SELECT 1 FROM profit_lines p WHERE p.order_id = o.id) AS has_pl
               FROM orders o WHERE o.status <> 'cancelled') o
    ON o.company_id = w.company_id AND o.placed_at >= w.f AND o.placed_at < w.t
  GROUP BY 1, 2),
fee AS (
  SELECT w.slug, pl.channel, sum(pl.channel_fees_cents) AS fees
  FROM w JOIN profit_lines pl ON pl.company_id = w.company_id AND pl.placed_at >= w.f AND pl.placed_at < w.t
  GROUP BY 1, 2),
ref AS (
  SELECT w.slug, r.channel, sum(r.amount_cents) AS refunds, sum(r.fee_recovered_cents) AS recovered
  FROM w JOIN refund_events r ON r.company_id = w.company_id AND r.voided_at IS NULL
   AND r.refunded_at >= w.f AND r.refunded_at < w.t
  GROUP BY 1, 2),
shp AS (
  SELECT w.slug, o.channel, sum(greatest(x.label - o.shipping_cents, 0)) AS ship_loss
  FROM w JOIN (SELECT order_id, company_id, sum(postage_cents + label_fee_cents) AS label
               FROM shipments WHERE voided_at IS NULL AND labeled_at IS NOT NULL GROUP BY 1, 2) x
    ON x.company_id = w.company_id
  JOIN orders o ON o.id = x.order_id AND o.placed_at >= w.f AND o.placed_at < w.t
  GROUP BY 1, 2),
rp AS (
  SELECT w.slug, o.channel, count(*) AS reprints,
    sum(CASE WHEN rp.blank_consumed THEN coalesce(pl.blank_cost_cents, 0) ELSE 0 END
        + coalesce(pl.transfer_cost_cents, 0) / (1 + (SELECT count(*) FROM reprints r2
            WHERE r2.order_item_id = rp.order_item_id AND r2.status <> 'cancelled'))) AS reprint_cost
  FROM w JOIN reprints rp ON rp.company_id = w.company_id AND rp.status <> 'cancelled'
   AND rp.requested_at >= w.f AND rp.requested_at < w.t
  JOIN order_items oi ON oi.id = rp.order_item_id
  JOIN orders o ON o.id = oi.order_id
  LEFT JOIN profit_lines pl ON pl.order_item_id = rp.order_item_id
  GROUP BY 1, 2)
SELECT ord.slug, ord.channel, ord.orders, ord.orders_without_profit_line, ord.gross AS gross_cents,
  ord.discounts AS discount_cents,
  coalesce(fee.fees, 0) - coalesce(ref.recovered, 0) AS fee_cents,
  coalesce(ref.refunds, 0) AS refund_cents,
  coalesce(shp.ship_loss, 0) AS shipping_loss_cents,
  coalesce(rp.reprint_cost, 0) AS reprint_cost_cents,
  round(100.0 * (ord.discounts + coalesce(fee.fees, 0) - coalesce(ref.recovered, 0) + coalesce(ref.refunds, 0)
        + coalesce(shp.ship_loss, 0) + coalesce(rp.reprint_cost, 0)) / nullif(ord.gross, 0), 1) AS leakage_pct
FROM ord
LEFT JOIN fee USING (slug, channel) LEFT JOIN ref USING (slug, channel)
LEFT JOIN shp USING (slug, channel) LEFT JOIN rp USING (slug, channel)
ORDER BY 1, 2;
