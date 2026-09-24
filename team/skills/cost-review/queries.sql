-- Per-tenant cost drivers for the InvAI cost review. Read-only; run as the owner role.
-- Local:  docker exec -i local-postgres-1 psql -U invai -d invai -v period='2026-09' -v since='2026-09-01' -v until='2026-10-01' < .claude/skills/cost-review/queries.sql
-- AWS: only with the owner's go-ahead (real shop data).
\pset footer off

\echo '1. Usage vs plan per shop for the period (usage table + plans)'
select c.name, c.plan, u.orders_imported, p.orders_per_month as order_limit,
       u.labels_bought, u.label_fees_cents, u.sheets_built,
       u.ai_credits, p.ai_credits_per_month as ai_credit_limit, p.price_monthly_cents
from usage u
join companies c on c.id = u.company_id
left join plans p on p.key = c.plan
where u.period = :'period'
order by u.orders_imported desc;

\echo '2. AI spend per shop (ai_jobs; cost_cents is 0 on the mock provider)'
select c.name, count(*) as calls, sum(j.tokens_in) as tokens_in, sum(j.tokens_out) as tokens_out,
       sum(j.cache_read_tokens) as cache_read,
       round(100.0 * sum(j.cache_read_tokens) / nullif(sum(j.tokens_in) + sum(j.cache_read_tokens), 0), 1) as cache_hit_pct,
       sum(j.cost_cents) as ai_cents, sum(j.credits) as credits
from ai_jobs j join companies c on c.id = j.company_id
where j.created_at >= :'since' and j.created_at < :'until'
group by c.name order by ai_cents desc, calls desc;

\echo '3. AI spend per route and model (watch cache_hit_pct < 50 on routes that should hit)'
select j.kind, j.model, j.provider, count(*) as calls, sum(j.cost_cents) as ai_cents,
       round(avg(j.tokens_in + j.tokens_out)) as avg_tokens,
       round(100.0 * sum(j.cache_read_tokens) / nullif(sum(j.tokens_in) + sum(j.cache_read_tokens), 0), 1) as cache_hit_pct,
       count(*) filter (where j.status = 'failed') as failed
from ai_jobs j
where j.created_at >= :'since' and j.created_at < :'until'
group by 1, 2, 3 order by ai_cents desc, calls desc;

\echo '4. Labels per shop: InvAI label fee revenue vs postage passed through'
select c.name, count(*) as labels, sum(l.label_fee_cents) as fee_revenue_cents,
       sum(l.postage_cents) as postage_cents,
       count(*) filter (where l.voided_at is not null) as voided
from labels l join companies c on c.id = l.company_id
where l.purchased_at >= :'since' and l.purchased_at < :'until'
group by c.name order by labels desc;

\echo '4b. Cross-check from shipments (the demo seed writes shipments without label rows; counts should match 4 on real data)'
select c.name, count(*) as labeled_shipments, sum(s.label_fee_cents) as fee_cents, sum(s.postage_cents) as postage_cents
from shipments s join companies c on c.id = s.company_id
where s.labeled_at >= :'since' and s.labeled_at < :'until'
group by c.name order by labeled_shipments desc;

\echo '5. Stored file bytes per shop and kind (files table; S3 Storage Lens is the source of truth in AWS)'
select c.name, f.kind, count(*) as files, pg_size_pretty(coalesce(sum(f.size_bytes), 0)) as size
from files f join companies c on c.id = f.company_id
group by c.name, f.kind order by c.name, sum(f.size_bytes) desc nulls last;

\echo '6. Background work per shop (jobs table; render seconds are not recorded yet)'
select c.name, j.kind, count(*) as jobs,
       round(sum(extract(epoch from (j.finished_at - j.created_at)))::numeric, 1) as total_seconds,
       count(*) filter (where j.status = 'failed') as failed
from jobs j join companies c on c.id = j.company_id
where j.created_at >= :'since' and j.created_at < :'until'
group by c.name, j.kind order by total_seconds desc nulls last;
