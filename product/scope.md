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
16. <a id="market-signals"></a>**Market signals for the assistant** (SCR-001, owner OI-6, 2026-09-27; spec `specs/market-signals.md`): deterministic trend, seasonality, price-position and margin-at-price signals with a confidence band, from the shop's own data and ToS-compliant outside sources only (official APIs for the shop's own listings, public official datasets, licensed data). Four read-only assistant tools, recommendation rules R1–R5, a feedback record per recommendation. Every outside source has a mock; mock answers are labelled "sample data".
17. <a id="weekly-digest"></a>**Weekly business review digest** (SCR-002, owner OI-7, 2026-09-27; spec `specs/weekly-digest.md`): a weekly digest per shop with numbers and ranked actions computed in code, rendered from en/es templates, shown in-app to everyone with profit access and emailed only to people who opt in (one-click unsubscribe). An AI-written summary runs in shadow mode (built, checked, never sent) until the real-model eval (OI-8) passes; the template is always the fallback. Includes a Market watch block fed by item 16.
18. <a id="listing-photos"></a>**AI listing photos** (SCR-008, owner approved in chat 2026-10-02, quote "implement these all"; spec `specs/listing-photos.md`; decision `0022-listing-photos-design-lock.md`): a shop picks one of its own uploaded designs, garment types (tee, hoodie, crewneck, tank) and blank colors; InvAI produces per-marketplace listing photo sets. **Phase A** (wave 26): AI design analysis (recommended colors, contrast warnings, alt text, image order), drawn garment templates composited with the real design at its real print size on the real blank hex, a white-underbase preview, channel presets with automated checks (Amazon, Etsy, Shopify, TikTok, Walmart), XMP `contains-synthetic-performer` and Etsy AI disclosure where they apply, credits per image, shop approval before any image leaves InvAI, zip download, attach to an AI listing draft. **Phase B** (wave 27): a gated image-generation provider draws lifestyle scenes around the design; design-lock drift checks; push approved images to Shopify.
   - **Fences:** the design's own pixels are never generated or altered by an image model — only `invai-imaging` composites them, deterministically (decision 0022). Real image generation (OpenAI GPT Image) stays off until the owner sets `IMAGE_GEN_PROVIDER=openai` (OI-25); the default is a deterministic mock, and every mock output is labelled as a sample/illustration. No shop image ever leaves InvAI without that shop's approval. Only Shopify gets an API image push (phase B); every other channel gets a zip download until that channel's approvals and adapter exist. Not SCR-007 (AI-invented designs; still open, OI-17): this feature only photographs a design the shop already uploaded.

<a id="market-and-digest-fences"></a>
### Fences on items 16 and 17 (hard limits, set with the owner's approval)
- **No scraping, ever.** No scraper APIs, no unofficial Google Trends libraries, no reading marketplace or competitor web pages. Permanent, not a deferral.
- **No cross-seller aggregation of marketplace data.** Data that came from a marketplace (API or the shop's own CSV export) is used only for that shop. It never feeds another shop's answer, a benchmark or a model.
- **Cross-shop benchmarks deferred.** Benchmarks over InvAI-native production data (film use, reprint rate, press throughput) wait for: a ToS/DPA clause reviewed by counsel, a tenant opt-out, and at least 10 shops per cell. Trigger: 10+ live shops and counsel's clause.
- **No automatic price or listing changes.** Market signals and the digest suggest; the shop acts. Nothing writes prices, listings, ads or POs.
- **No Etsy competitor data** (other sellers' listings, prices or tags through the Etsy API) until Etsy agrees in writing (owner decides whether to ask).
- **No real paid data source or new outside account without the owner** (Jungle Scout, Keepa, Google Trends alpha, Pinterest app, a production email provider). The mock stays in place until then.
- **Mock outside data never reaches a real shop in production.** Mock market sources are used and shown only outside production and in sample workspaces (`isSampleWorkspace`); for a real shop in production a mock counts as "no source" (`specs/market-signals.md`, "Providers and mocks").
- **No demand forecasting model.** Trend and seasonality are descriptive (what happened, with confidence). The only projection is the labelled price-response estimate in the spec, and only from the shop's own price history. The v1 cut of statistical forecasting (`decisions/0006-v1-cuts.md`) stands.
- **The digest carries no promotions or upsells** (keeps it account information for CAN-SPAM; counsel to confirm before the first real email).

## MVP: out (see `decisions/0006-v1-cuts.md`)
- AI design generation
- Direct Amazon SP-API, until the security review and pen test are done
- Direct Etsy, TikTok and Walmart APIs, until approvals land (the adapters stay ready)
- SanMar, GPU upscaling, shape-aware nesting, statistical forecasting, silent label printing, buyer message drafts
- Everything listed under "Fences on items 16 and 17" above

## Later (deferred, with a trigger)
| Item | Trigger to reconsider |
|---|---|
| Real Google Trends adapter | Owner applies to the alpha (OI-9), Google accepts, and the alpha terms allow use in a paid product |
| Real Amazon pricing/catalog and Walmart pricing-insights adapters | SP-API app approval / Walmart Solution Provider approval |
| Amazon Brand Analytics signals | A brand-registered pilot shop grants the role |
| Pinterest trends | A pilot shows Pinterest-led niches matter, and the owner registers a Pinterest app |
| Jungle Scout or another licensed source | Written embedding licence (OI-11) and the owner's spend approval |
| Etsy competitor price analytics | Etsy's written permission (OI-10) |
| Cross-shop production benchmarks | 10+ live shops per cell, counsel-reviewed ToS/DPA clause |
| Digest: "production week" variant for leads, per-department digests for large shops, monthly variant, Slack/WhatsApp | Two pilot shops ask |

## Pricing hypothesis
- **To test:** $149 / $349 / $699 per month for mid and large shops.
- **Research 02:** small shops pay $49–149 per month. The PM must decide the small-shop entry plan through a `pricing-experiment` before public launch.
- The owner decides prices.

## Change log
| Date | Change | Approved by |
|---|---|---|
| 2026-09-24 | Baseline from v1-plan §2; segments added | tech-lead (PM to confirm) |
| 2026-09-27 | Added item 16, market signals for the assistant (SCR-001), with its fences; research `research/14-market-signals.md` | owner (OI-6), product-manager |
| 2026-09-27 | Added item 17, weekly business review digest (SCR-002); AI summary in shadow mode until OI-8; research `research/15-weekly-digest.md` | owner (OI-7), product-manager |
| 2026-09-27 | Added the "Later" list with triggers; recorded in `decisions/0014-market-signals-and-digest-scope.md` | product-manager |
| 2026-09-27 | Fence added: mock outside market data only outside production and in sample workspaces (spec reviews of market-signals and weekly-digest, customer-success blocker) | product-manager |
| 2026-10-02 | Added item 18, AI listing photos (SCR-008), phases A and B; fences: design pixels never AI-generated (decision 0022), real image generation off until OI-25, approval before any image leaves InvAI, only Shopify gets an API push | owner (in chat), product-manager |
