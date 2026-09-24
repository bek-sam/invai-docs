-- Tenant-isolation audit for the local InvAI database. Read-only.
-- Run as the owner role, from the workspace root:
--   docker exec -i local-postgres-1 psql -U invai -d invai -v ON_ERROR_STOP=1 < .claude/skills/tenant-isolation-audit/audit.sql
-- Every section says what a clean result looks like.
\pset footer off

\echo '1. Tables with company_id but RLS off or no policy (expect: 0 rows)'
select c.table_name, t.rowsecurity,
       (select count(*) from pg_policies p where p.schemaname = 'public' and p.tablename = c.table_name) as policies
from information_schema.columns c
join pg_tables t on t.schemaname = 'public' and t.tablename = c.table_name
where c.table_schema = 'public' and c.column_name = 'company_id'
  and (not t.rowsecurity
       or not exists (select 1 from pg_policies p where p.schemaname = 'public' and p.tablename = c.table_name));

\echo '2. Policies whose predicate is not plain company_id equality (expect: only reviewed vendor/public-read policies)'
select tablename, policyname, qual
from pg_policies
where schemaname = 'public'
  and coalesce(qual, '') not like '(company_id = (NULLIF(current_setting(''app.company_id''::text, true), ''''::text))::uuid)'
order by tablename;

\echo '3. Views and materialized views without security_invoker (expect: 0 rows)'
select c.relname, c.relkind, c.reloptions
from pg_class c join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relkind in ('v', 'm')
  and not coalesce('security_invoker=true' = any(c.reloptions), false);

\echo '4. SECURITY DEFINER functions in public (expect: 0 rows, or reviewed with a pinned search_path)'
select p.proname, p.proconfig
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public' and p.prosecdef;

\echo '5. App role must not be superuser, bypass RLS or own tables (expect: f, f, 0)'
select rolsuper, rolbypassrls,
       (select count(*) from pg_tables where schemaname = 'public' and tableowner = 'invai_app') as owned_tables
from pg_roles where rolname = 'invai_app';

\echo '6. Tenant-table indexes that do not lead with company_id (review: tenant queries must use a company_id-leading index)'
select i.tablename, i.indexname
from pg_indexes i
where i.schemaname = 'public'
  and exists (select 1 from information_schema.columns c
              where c.table_schema = 'public' and c.table_name = i.tablename and c.column_name = 'company_id')
  and i.indexdef not like '%(company_id%'
  and i.indexname not like '%_pkey'
order by i.tablename, i.indexname;

\echo '7. As invai_app with no tenant set: tables that return rows (expect: none listed)'
set role invai_app;
do $$
declare r record; n bigint;
begin
  for r in select distinct c.table_name from information_schema.columns c
           join pg_tables t on t.schemaname = 'public' and t.tablename = c.table_name
           where c.table_schema = 'public' and c.column_name = 'company_id' loop
    begin
      execute format('select count(*) from public.%I', r.table_name) into n;
      if n > 0 then raise notice 'VISIBLE WITHOUT TENANT: % (% rows)', r.table_name, n; end if;
    exception when insufficient_privilege then null;
    end;
  end loop;
end $$;
reset role;

\echo '8. As invai_app scoped to one company: rows of other companies visible (expect: none listed)'
select id as audit_company from companies where type = 'shop' order by created_at limit 1 \gset
begin;
set local role invai_app;
select set_config('app.company_id', :'audit_company', true);
do $$
declare r record; n bigint;
begin
  for r in select distinct c.table_name from information_schema.columns c
           join pg_tables t on t.schemaname = 'public' and t.tablename = c.table_name
           where c.table_schema = 'public' and c.column_name = 'company_id' loop
    begin
      execute format('select count(*) from public.%I where company_id <> current_setting(''app.company_id'')::uuid', r.table_name) into n;
      if n > 0 then raise notice 'CROSS-TENANT ROWS VISIBLE: % (% rows)', r.table_name, n; end if;
    exception when insufficient_privilege then null;
    end;
  end loop;
end $$;
rollback;
\echo 'Done.'
