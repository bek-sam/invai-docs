# Scale seed profiles (proposal)

Derived from research 11 (stage table: 50–300 orders/day per shop; staging seed of 1,000 companies with a skewed size mix and 12 months of orders) and research 12 §3.9 (a 50k-order "large tenant"). The generator is to be created (`invai-backend/src/db/seed/scale/`, `pnpm db:seed:scale --profile <name>`, backlog B-34); qa-engineer owns the profiles, backend-foundation reviews the seed code.

| Profile | Companies | Size mix (orders/day per shop) | History | Rough totals | Question it answers |
|---|---|---|---|---|---|
| `small` (pilot) | 20 | 15 small (30–60), 4 mid (100–200), 1 large (300) | 90 days | ~180k orders | Does the pilot stage meet every p95 with 2× peak? |
| `mid` (growth) | 200 | 80% small, 18% mid, 2% large (300–600) | 6 months | ~3–4M orders | Where do RLS plans, pooling and queue fairness break at 100s of shops? |
| `large` (scale rehearsal) | 1,000 | long tail: 85% small, 13% mid, 2% large, plus one 50k-order tenant | 12 months | ~15–20M orders | Tenant-first indexes, trigram search across tenants, outbox and `order_items` growth |

## What each company gets
- 1 location, 4 stations (pick, press, QC, pack) with station tokens and staff PINs.
- 1–3 channel connections (mix of csv and mock Shopify), SKU rules, 20–300 designs, blank variants with stock that never goes negative.
- Orders over the history window with a daily curve (Monday and holiday peaks), multi-unit orders (one order item per unit), personalization on ~10% of items, and item states that match age: old orders shipped/delivered, recent ones spread across ready, on_sheet, pressed, packed.
- Gang sheets, transfers, scans, shipments and labels (mock carrier) for shipped work, so the production and shipping tables have realistic volume.
- `outbox_events`, `audit_log` and `order_item_transitions` rows consistent with those transitions (these are the tables that grow fastest).
- Buyer PII only from a fake generator (`scrub-pii-fixture` rules): never real names or addresses.

## Size mix for print files (keep the demo seed's realism)
Adult front 10.5 × 12 in, youth 8.5 × 9.5, left chest 3.75, sleeve 3 × 10, back 12 × 14. Unrealistic sizes once made sheets look 51.7% efficient; real mixes give 86–91%.

## Load per profile (starting point for k6)
| Scenario | small | mid | large |
|---|---|---|---|
| Floor scans (20 stations × 1 / 3 s per active shop) | 20 active shops ≈ 130 scans/s | 50 active ≈ 330/s | 100 active ≈ 670/s |
| Order import burst (10× normal) | 10× of ~2k orders/day | 10× of ~20k/day | 10× of ~100k/day |
| Sheet builds at once | 5 tenants | 10 tenants | 20 tenants |
| Dashboard reads | 1 req/s per active office user, 2 users per shop | same | same |

Adjust "active" counts to the stage question; record the numbers used in the report.
