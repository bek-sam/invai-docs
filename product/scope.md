# InvAI scope

Owner: `product-manager`. Nothing outside this file gets built. Changes come only through the `scope-change-request` playbook: the PM approves, and the owner also approves when a change affects cost or risk. Baseline written by the tech lead on 2026-09-24 from `build/v1-plan.md` §2. The PM maintains it from here.

## Segments
| Segment | Shop profile | What they need first | Onboarding level |
|---|---|---|---|
| **Small** | 1–3 people, under 100 orders/day, often Etsy-first | Orders in one place, SKU mapping, gang sheets, labels; low price; self-serve setup | Self-serve |
| **Mid** | 5–30 staff, 100–1,000 orders/day, several marketplaces | Scan-checked floor, vendor portal, inventory, profit | Assisted |
| **Large** | 30+ staff or several locations, 1,000+ orders/day | Throughput, roles and permissions, reliability, data migration | White-glove |

Pilots target **mid** first. Small shops must be able to self-serve without a call. Large shops come after the scale test passes (`scale-test`).

## Always in scope
- Bugs in shipped features
- Security findings and incidents
- Compliance deadlines: marketplace approvals, Amazon's data-protection rules, privacy requests
- Reliability and observability needed to run pilots safely

## MVP: in
<a id="mvp-in"></a>
1. Order Hub sorted by real ship-by date, at-risk alerts, holds, cancel
2. CSV import for Etsy, Amazon, TikTok, Walmart and Shopify, plus the Shopify API adapter
3. SKU mapper
4. Gang Sheet Builder (nesting, order/QR labels, PNG and PDF)
5. Production floor app: pick, press, QC, pack, scan match, offline queue, English and Spanish
6. Blank inventory, reservations, POs, receiving, reorder
7. Shipping: rate shopping, labels, batch 4x6 PDF, tracking push
8. Profit per order, design, blank and channel
9. DTF vendor portal
10. AI listing drafts with validators, human approval and disclosure
11. Trademark risk check
12. Personalization rendering and checks
13. AI business assistant (read-only tools)
14. Today command center, onboarding checklist, demo mode
15. Plan limits (Stripe checkout when keys exist)

## MVP: out (see `decisions/0006-v1-cuts.md`)
- AI design generation
- Direct Amazon SP-API, until the security review and pen test are done
- Direct Etsy, TikTok and Walmart APIs, until approvals land (the adapters stay ready)
- SanMar, GPU upscaling, shape-aware nesting, statistical forecasting, silent label printing, buyer message drafts

## Pricing hypothesis
- **To test:** $149 / $349 / $699 per month for mid and large shops.
- **Research 02:** small shops pay $49–149 per month. The PM must decide the small-shop entry plan through a `pricing-experiment` before public launch.
- The owner decides prices.

## Change log
| Date | Change | Approved by |
|---|---|---|
| 2026-09-24 | Baseline from v1-plan §2; segments added | tech-lead (PM to confirm) |
