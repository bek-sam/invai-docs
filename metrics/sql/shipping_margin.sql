-- shipping_margin v1 (metrics/definitions/shipping_margin.md)
-- Per labeled order: shipping the buyer paid (orders.shipping_cents) minus what the label cost
-- (postage + InvAI label fee, non-voided shipments). Orders shipped without an InvAI label are
-- excluded (label cost unknown) and counted separately. Window: labeled_at, shop tz.
WITH shops AS (
  SELECT id AS company_id, slug, timezone FROM companies
  WHERE type = 'shop' AND deleted_at IS NULL AND demo_owner_user_id IS NULL
    AND (settings->>'demoRetiredAt') IS NULL),
w AS (SELECT s.*, (:'from'::date::timestamp AT TIME ZONE s.timezone) AS f,
             (:'to'::date::timestamp AT TIME ZONE s.timezone) AS t FROM shops s),
lab AS (
  SELECT w.slug, sh.order_id, sum(sh.postage_cents + sh.label_fee_cents) AS label_cents,
         min(sh.carrier || ' ' || coalesce(sh.service, '')) AS service
  FROM w JOIN shipments sh ON sh.company_id = w.company_id AND sh.labeled_at >= w.f
   AND sh.labeled_at < w.t AND sh.voided_at IS NULL
  GROUP BY 1, 2)
SELECT lab.slug, o.channel, count(*) AS labeled_orders,
  sum(o.shipping_cents) AS shipping_charged_cents,
  sum(lab.label_cents) AS label_cost_cents,
  sum(o.shipping_cents) - sum(lab.label_cents) AS shipping_margin_cents,
  round((sum(o.shipping_cents) - sum(lab.label_cents))::numeric / count(*), 0) AS margin_per_order_cents,
  count(*) FILTER (WHERE o.shipping_cents = 0) AS free_shipping_orders
FROM lab JOIN orders o ON o.id = lab.order_id
GROUP BY 1, 2 ORDER BY 1, 6;
