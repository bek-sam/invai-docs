-- profit_bridge v1 (metrics/definitions/profit_bridge.md)
-- Why net profit (CM3, profit lines only) changed between a base window [:'bfrom', :'bto') and a
-- current window [:'from', :'to'), shop tz. Per design d (unmapped designs pooled as one key):
--   volume_d = (units1 - units0) * cm_per_unit0          (sold more or fewer)
--   rate_d   = units1 * (cm_per_unit1 - cm_per_unit0)    (each unit earned more or less: price,
--                                                          fees, costs, ads, refunds on the line)
--   new/lost designs: all of cm1 (new) or -cm0 (lost) goes to volume.
-- Sum over designs: volume + rate = change, exactly (no residual). Rows: the total plus the top
-- 5 designs by |contribution| (design ids only).
WITH shops AS (
  SELECT id AS company_id, slug, timezone FROM companies
  WHERE type = 'shop' AND deleted_at IS NULL AND demo_owner_user_id IS NULL
    AND (settings->>'demoRetiredAt') IS NULL),
w AS (SELECT s.*,
  (:'bfrom'::date::timestamp AT TIME ZONE s.timezone) AS bf, (:'bto'::date::timestamp AT TIME ZONE s.timezone) AS bt,
  (:'from'::date::timestamp AT TIME ZONE s.timezone) AS f, (:'to'::date::timestamp AT TIME ZONE s.timezone) AS t
  FROM shops s),
p AS (
  SELECT w.slug, coalesce(pl.design_id::text, 'unmapped') AS design,
    count(*) FILTER (WHERE pl.placed_at >= w.bf AND pl.placed_at < w.bt AND NOT pl.is_reprint) AS u0,
    coalesce(sum(pl.net_cents) FILTER (WHERE pl.placed_at >= w.bf AND pl.placed_at < w.bt), 0) AS cm0,
    count(*) FILTER (WHERE pl.placed_at >= w.f AND pl.placed_at < w.t AND NOT pl.is_reprint) AS u1,
    coalesce(sum(pl.net_cents) FILTER (WHERE pl.placed_at >= w.f AND pl.placed_at < w.t), 0) AS cm1
  FROM w JOIN profit_lines pl ON pl.company_id = w.company_id
   AND ((pl.placed_at >= w.bf AND pl.placed_at < w.bt) OR (pl.placed_at >= w.f AND pl.placed_at < w.t))
  GROUP BY 1, 2),
e AS (
  SELECT slug, design, u0, u1, cm0, cm1,
    CASE WHEN u0 = 0 OR u1 = 0 THEN cm1 - cm0 ELSE round((u1 - u0) * cm0::numeric / u0) END AS volume,
    CASE WHEN u0 = 0 OR u1 = 0 THEN 0 ELSE (cm1 - cm0) - round((u1 - u0) * cm0::numeric / u0) END AS rate
  FROM p),
ranked AS (SELECT e.*, row_number() OVER (PARTITION BY slug ORDER BY abs(cm1 - cm0) DESC) AS rn FROM e)
SELECT slug, 'TOTAL' AS design, sum(u0) AS units0, sum(u1) AS units1, sum(cm0) AS cm0_cents,
  sum(cm1) AS cm1_cents, sum(cm1 - cm0) AS change_cents, sum(volume) AS volume_cents, sum(rate) AS rate_cents
FROM e GROUP BY slug
UNION ALL
SELECT slug, design, u0, u1, cm0, cm1, cm1 - cm0, volume, rate FROM ranked WHERE rn <= 5
ORDER BY 1, 2 DESC;
