select 'counts', (select string_agg(t||'='||n, ' ' order by t) from (
  select 'orders' t, count(*) n from orders union all select 'items', count(*) from order_items
  union all select 'transitions', count(*) from order_item_transitions union all select 'sheets', count(*) from gang_sheets
  union all select 'transfers', count(*) from transfers union all select 'shipments', count(*) from shipments
  union all select 'movements', count(*) from inventory_movements union all select 'stock', count(*) from stock_levels
  union all select 'alerts', count(*) from alerts union all select 'ad_spend', count(*) from ad_spend
  union all select 'blanks', count(*) from blank_variants union all select 'designs', count(*) from designs
  union all select 'products', count(*) from products union all select 'sku_rules', count(*) from sku_rules
  union all select 'scans', count(*) from scans union all select 'reprints', count(*) from reprints
  union all select 'listings', count(*) from listings union all select 'audit', count(*) from audit_log
  union all select 'vendor_access', count(*) from vendor_access
  union all select 'staff_pins', count(*) from staff_pins union all select 'station_tokens', count(*) from station_tokens
  union all select 'users', count(*) from users union all select 'members', count(*) from members) x);
select 'orders', md5(string_agg(concat_ws('|',order_no,channel,status,subtotal_cents,shipping_cents,total_cents,item_count,is_rush,has_personalization,buyer_note,buyer_ref,hold_reason,cancel_reason,tags::text), ',' order by order_no)) from orders;
select 'items', md5(string_agg(concat_ws('|',o.order_no,i.line_no,i.unit_no,i.state,i.channel_sku,i.title,i.variant_title,i.unit_price_cents,i.artwork_status,i.is_reprint,i.placement,i.print_width_in,i.personalization::text), ',' order by o.order_no,i.line_no,i.unit_no)) from order_items i join orders o on o.id=i.order_id;
select 'transitions', md5(string_agg(concat_ws('|',from_state,to_state,n), ',' order by from_state,to_state)) from (select from_state,to_state,count(*) n from order_item_transitions group by 1,2) t;
select 'timeline_offsets', md5(string_agg(concat_ws('|',o.order_no,extract(epoch from (t.created_at - o.placed_at))::int), ',' order by o.order_no, extract(epoch from (t.created_at - o.placed_at))::int)) from order_item_transitions t join orders o on o.id=t.order_id;
select 'sheets', md5(string_agg(concat_ws('|',name,length_in,utilization,status,transfer_count,reprint_count,cost_cents,tracking_code), ',' order by name)) from gang_sheets;
select 'shipments', md5(string_agg(concat_ws('|',status,postage_cents,tracking_code,weight_oz,tracking_push_status), ',' order by tracking_code)) from shipments;
select 'stock', md5(string_agg(concat_ws('|',b.sku,s.on_hand,s.reserved,s.available,s.shelf), ',' order by b.sku)) from stock_levels s join blank_variants b on b.id=s.blank_variant_id;
select 'movements', string_agg(concat_ws('=',kind,q), ' ' order by kind) from (select kind, sum(qty) q from inventory_movements group by 1) m;
select 'alerts', md5(string_agg(concat_ws('|',kind,severity,title,message), ',' order by kind,title)) from alerts;
select 'ad_spend', md5(string_agg(concat_ws('|',channel,campaign,amount_cents), ',' order by channel,campaign,amount_cents)) from ad_spend;
select 'usage', string_agg(concat_ws('|',orders_imported,labels_bought,label_fees_cents,sheets_built,ai_credits), ',') from usage;
select 'connections', string_agg(concat_ws('|',channel,name,status,external_shop_id,provider), ',' order by channel) from channel_connections;
select 'vendor', string_agg(concat_ws('|',name,email,status,delivery,vendor_company_id is not null), ',') from vendor_connections;
select 'location', string_agg(concat_ws('|',name,address::text), ',') from locations;
