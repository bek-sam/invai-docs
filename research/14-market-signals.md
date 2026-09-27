# 14. Market signals for the assistant: sources, terms, algorithm, MVP

- Date: 2026-09-27. Why: OI-6 approved (owner, 2026-09-27) and `product/scope-changes/SCR-001-assistant-external-market-signals.md`.
- Guardrails from OI-6: only ToS-compliant sources (official APIs, first-party data, licensed data, public official datasets). No scraping. Every provider gets a mock. Any real paid subscription or key goes back to `owner-inbox.md` before it is bought. Nothing may put the pending Etsy Commercial Access or Amazon SP-API applications at risk.
- Builds on: wave 17 analyst tools (`invai-backend/src/modules/ai/assistant-tools.ts`: `compare_periods`, `get_ad_performance`, `get_design_insights`, `get_fulfillment_health`, …), the profit model (`src/modules/finance/profit.ts`, fee tables in `finance/fees`), the trademark check (`src/modules/ai/trademark.ts`), and the adapter pattern (`src/integrations/carriers/index.ts`: the real adapter when a key is set, otherwise the mock; a sample workspace always gets the mock).
- Tags: **[V]** verified on the cited page on the access date. **[3P]** third-party summary, not the primary text. **[U]** uncertain; confirm before relying on it. All URLs were accessed on 2026-09-27 unless noted.

## 0. The answer in brief
1. **No official source gives Etsy search volume or Etsy competitor sales.** Etsy's API terms restrict using the API for analytics. Their live text returns 403 to us, but our Aug 2026 Wayback reading in research 10 lists "collect data for analytics, ML or AI training" under MUST NOT. Etsy competitor-price analytics through `findAllListingsActive` is therefore **avoid** until Etsy confirms it in writing. Asking would itself be a question in the Commercial Access review, so the owner should decide whether to ask.
2. **Cross-tenant benchmarks built from marketplace-origin data (prices, units, sell-through) are not allowed.** Amazon AUP §4.4 and §4.6, Shopify API Terms §6.2.5 and §6.2.8, Walmart's developer terms and TikTok Shop's partner terms each forbid aggregating one seller's data for others, or using it for benchmarking. Benchmarks are legitimate only over **InvAI-native operational data**, and only with k ≥ 10 companies and a dominance cap.
3. **Usable sources, all official and all free or unpriced today:**
   - The shop's own history (the strongest signal).
   - Amazon Product Pricing `getCompetitiveSummary` for the shop's own ASINs, after SP-API approval.
   - Walmart `getPricingInsights` for the shop's own items.
   - Google Trends API (alpha, application-gated).
   - Pinterest Trends API.
   - US Census Monthly Retail Trade (macro seasonality).
   - Amazon Brand Analytics, only for brand-registered shops.
4. **Paid tools:**
   - Jungle Scout's API costs $29–$199/mo, but its terms forbid making its data available to third parties without approval, so it needs a written reseller or embedding licence.
   - Keepa's API starts at €49/mo, but no licence terms were readable.
   - Helium 10's API is enterprise-only.
   - eRank, EverBee and Alura have no public API.
   - None of these can be embedded today without a written licence.
5. **The algorithm (§3) is deterministic first and the LLM second.** Jobs compute the signals (trend slope, seasonality index, price percentile, competition density, margin at candidate price) with confidence scores. The assistant only reads them through tools, cites source and date, and refuses below the thresholds.
6. **MVP:**
   - A `MarketSignalProvider` interface with mocks for every source.
   - Real computation over own data and Census.
   - Four read-only tools.
   - A `market_recommendations` feedback table.
   - Estimated cost: about $1–2 per tenant per month, almost all AI tokens.

---

## 1. Source inventory

Verdicts:
- **Now (mock):** build the adapter and mock now; the real call is free and needs no new approval beyond what the channel already has.
- **Later:** needs an approval, key or paid licence (goes to the owner inbox).
- **Avoid:** terms forbid it, or the risk outweighs the value.

### 1.1 Official marketplace APIs

#### Etsy Open API v3
- **What it gives:** the shop's own listings, receipts and transactions (already used by the channel adapter). The public active-listing search (`GET /v3/application/listings/active`, "findAllListingsActive") returns other sellers' public listings, with price, tags and views [U on views]. **There is no search-volume, keyword or trend endpoint**; the feature request "Etsy Search Analytics" is open as GitHub discussion #681 (https://github.com/etsy/open-api/discussions/681).
- **Terms:** the live terms at https://www.etsy.com/legal/api return **403** to our fetcher (tried WebFetch and curl on 2026-09-27; a web.archive.org fetch was also blocked). What we have:
  - Research 10 (Aug 2026 Wayback snapshot, terms updated 2025-06-16) paraphrases the MUST NOTs: "Collect data for analytics, ML or AI training", "Request more than the minimum data needed", "Use multiple keys to evade rate limits"; and freshness: "listing content must be at most 6 h stale; other content at most 24 h".
  - The archived pre-2020 terms (https://www.etsy.com/legal/api-archived/, as quoted by search results [3P]) say you may not use the API "in a manner unrelated to seller or buyer activity, such as to determine information about Etsy's internal systems or to perform marketing analytics, without the permission of Etsy", and "screen-scraping is not allowed".
  - Commercial Access review criteria (https://developer.etsy.com/documentation/ [V]): "Applications must follow the caching policies identified in Section 1 of the API Terms of Use", and scraping is prohibited.
- **Rate limits:** per API key, shown in the `x-limit-per-second` and `x-limit-per-day` headers; upgrades by email to developer@etsy.com (https://developer.etsy.com/documentation/essentials/rate-limits [V]).
- **Verdict:**
  - Own-shop data: **use now** (already in scope).
  - Competitor listing search for price analytics: **avoid**. The analytics clause plausibly covers it. Pulling thousands of other sellers' listings also conflicts with "minimum data needed" and the 6 h freshness rule, and Commercial Access is pending.
  - Revisit only with Etsy's written OK. That would be an owner-sent question and must not go into the Commercial Access application unasked (**OI needed**).

#### Amazon SP-API
- **Product Pricing API** (`getCompetitiveSummary`, `getItemOffers`, `getItemOffersBatch`):
  - `getCompetitiveSummary` returns the featured buying options (Buy Box), the lowest priced offers, reference prices, and similar items for a list of ASINs. It takes 1–20 ASINs per batch. Rate: **0.033 req/s, burst 1** (https://developer-docs.amazon/sp-api/reference/getcompetitivesummary [V]).
  - `getItemOffersBatch`: 0.1 req/s, burst 1 since 2023 (https://developer-docs.amazon.com/sp-api/changelog/starting-may-1-2023-the-rate-for-the-getitemoffersbatch-operation-within-the-product-pricing-api-will-be-lowered [3P summary]).
  - Role: "Pricing" together with "Product Listing" (https://developer-docs.amazon.com/sp-api/docs/product-pricing-api-v0-use-case-guide [3P summary]). These are **non-restricted** roles, with no PII.
- **Catalog Items API** (`searchCatalogItems` by keyword): catalog attributes and `salesRanks` (classification ranks). Role: **Product Listing** (https://developer-docs.amazon/sp-api/docs/role-mappings [V]).
- **Brand Analytics reports:**
  - `GET_BRAND_ANALYTICS_SEARCH_TERMS_REPORT`: "Most-clicked ASINs by search keyword and department".
  - Search Query Performance: "impressions, clicks, cart adds, and purchases".
  - Search Catalog Performance.
  - Requirements: the **Brand Analytics** role, and the seller must be "registered in Amazon Brand Registry" and "a brand representative". Periods are WEEK/MONTH/QUARTER (the terms report also allows DAY). Request-only (https://developer-docs.amazon/sp-api/docs/report-type-values-analytics [V]). Data Kiosk also needs the Brand Analytics role (role mappings [V]).
  - Most small DTF shops are not brand-registered [U; pilots will tell].
- **Terms:** Acceptable Use Policy (https://solutionproviderportal.amazon.com/solution-provider/policy?policyType=AUP&locale=en_US [V]):
  - §4.4: "Do not aggregate data across Authorized Users' businesses or customers obtained through the Amazon Services API to provide or sell to any parties, including competing Authorized Users."
  - §4.5: "Do not promote, publish or share insights about Amazon's business. Do not use insights about Amazon's business for your own business purposes."
  - §4.6: "Do not disclose Information, individually labelled or aggregated, to other Application users, affiliated entities or any outside parties, unless required to perform acceptable Authorized User activities."
  - Reading: pricing data fetched **for seller A, about A's own ASINs, shown only to A**, is the documented repricer use case (https://developer.amazonservices.com/solutions-automated-pricing-management-on-amazon). Pooling it across sellers is not allowed.
- **Cost:** Amazon announced a $1,400/yr fee plus GET-call fees for 2026, then **cancelled them on 2026-05-12** (https://novadata.io/resources/news/amazon-sp-api-subscription-fees-2026 , https://ppc.land/amazon-drops-sp-api-fees-after-developer-pushback/ [3P]). Current cost: $0 [U: watch `provider-deprecation-watch`].
- **Verdict:**
  - Pricing plus Catalog on the shop's own ASINs: **later**. It needs the SP-API app approval that is pending; the DPP review is for restricted roles, and Pricing is not restricted. Build the adapter and mock **now**.
  - Brand Analytics: **later**, and only for brand-registered shops that grant the role.
  - Competitor ASINs discovered with `searchCatalogItems` and priced with `getCompetitiveSummary` to position the shop's own product: **later**. It is the standard repricing use and does not fall under §4.4–4.6 as long as results stay per seller [U: confirm in the SP-API use-case description we submit].

#### Walmart Marketplace API
- **What it gives:** `POST /v3/price/getPricingInsights` covers **your items**: current price, Buy Box price, competitive price info, repricer details. Filters include `priceCompetitiveness`, `buyBoxWinRate`, `salesRank`, `gmvL30D`, `traffic` and `isInDemand` (https://developer.walmart.com/us-marketplace/docs/get-pricing-insights-data-for-your-items; the page 404'd for WebFetch, so the fields come from the search index snippet [3P]). The Insights API has listing quality and item performance (https://developer.walmart.com/doc/us/mp/us-mp-insights/).
- **Terms** (https://developer.walmart.com/global-marketplace/docs/terms-and-conditions [3P summary]): developers shall not "collect, retain, use, access, rent, sell, disclose, reconfigure, de-identify, re-identify or aggregate Walmart Confidential Information for any purpose other than to provide the Services", nor "use Walmart Confidential Information to create any derivative work or product without Walmart's express written authorization."
- **Rate limits:** token bucket per seller and per solution provider (research 10).
- **Verdict: later.** It needs a Solution Provider app (3–5 weeks, research 10). Adapter and mock **now**. Per-shop only, never pooled.

#### Shopify Admin API
- **What it gives:** the merchant's own store data only; no market data. Shopify does not provide cross-store market data to apps.
- **Terms** (https://www.shopify.com/legal/api-terms, last updated 2026-02-27 [V]):
  - §6.2.5: "not use information from Merchants or Customers for competitive benchmarking".
  - §6.2.1: "not use … Merchant Data … except as necessary to provide the Application services to the Merchant".
  - §6.2.8: no transfer to third parties or other apps "except as necessary to provide your Application's services". The search summary says this includes "anonymous, aggregate or derived data" [3P].
  - §2.3.24: no use of Shopify API information "to create, develop, train, fine tune, or improve any machine learning or artificial intelligence systems … except with … Shopify's prior written consent, or … the relevant Merchant's consent".
- **Verdict:** own-store signals, **now**. Cross-store benchmarks from Shopify data: **avoid**. Our feedback loop must not "train" models on Shopify merchant data. Tuning numeric thresholds per merchant, on that merchant's own data, is within §2.3.24(b) only with merchant consent, so keep global tuning to InvAI-native data [U: counsel].

#### TikTok Shop Partner API
- **What it gives:** analytics for the authorized shop only, e.g. "Get Shop Performance" (https://partner.tiktokshop.com/docv2/page/get-shop-performance-202405) and "Get Shop Video Performance List" (https://partner.tiktokshop.com/docv2/page/get-shop-video-performance-list-202509). These pages need JavaScript, so their field lists are not verified. There is no official market or trend endpoint for other shops [3P: https://www.echotik.live/blog/tiktok-shop-data-api-access-endpoints-metrics-and-analytics-2026/].
- **Terms** (Global TikTok Shop Partner Center ToS, https://seller-br.tiktok.com/university/essay?knowledge_id=3037474364589840 [3P summary]): partners agree not to share TikTok Data with third parties except Permitted Users, not to "attempt to de-aggregate or de-anonymize TikTok Data", and not to "use TikTok Data to create or improve profiles or segments". A Data Security and Privacy Review is required (https://partner.tiktokshop.com/docv2/page/data-security-and-privacy-review).
- **Verdict:** own-shop analytics, **later** (Partner approval). TikTok Creative Center and "top products" pages have no official API, so **avoid**; third-party "TikTok Shop data APIs" (Apify, EchoTik, etc.) are scrapers.

### 1.2 Official public demand and trend data

#### Google Trends API (alpha)
- **What it gives:** "a rolling window of the last 5 years of data", "daily, weekly, monthly, and yearly" aggregation, countries and sub-regions, and **consistently scaled** values ("API data is not scaled from 0 to 100"), so pulls can be joined over time (https://developers.google.com/search/apis/trends [V]). Announced 2025-07-24 (https://developers.google.com/search/blog/2025/07/trends-api).
- **Access:** application-gated alpha; Google prioritises "developers that know what they want to do". It is still alpha in Aug 2026, with no published price, quotas or GA date [3P: https://scrapebadger.com/blog/does-google-trends-have-an-api-what-to-use-in-2026].
- **Terms for commercial embedding: not published [U].** Read the alpha agreement before using the data in a paid product.
- **Freshness:** data up to about 48 h old [3P: https://www.searchenginejournal.com/google-trends-api-alpha-launching-breaking-news/551935/].
- **Verdict: later.** Applying is an outbound submission, so the owner decides. It is the best general demand and seasonality source. Mock **now**. Unofficial libraries (pytrends, SerpApi "Google Trends") scrape the web UI: **avoid**.

#### Pinterest API v5: Trends
- **What it gives:** `GET /trends/keywords/{region}/top/{trend_type}` returns the top trending keywords with week-over-week, month-over-month and year-over-year growth, plus "weekly observations of relative search volume over the past year, normalized to a [0-100] range", and optionally `predicted_time_series`. `normalize_against_group` allows comparison between keywords (https://developers.pinterest.com/docs/api/v5/trending_keywords-list/ ; response model https://github.com/pinterest/pinterest-python-generated-api-client/blob/main/docs/TrendingKeywordsResponse.md [3P summary]).
- **Useful for:** gift and seasonal apparel niches (Pinterest is a leading indicator for Etsy-style shopping [U]).
- **Not verified:** access tier and scopes (the doc page did not render). It probably needs a Pinterest app with at least trial access and an OAuth'd business account [U]. It is "top trending" lists, not arbitrary keyword lookup, unless `include_keywords` is supported [U].
- **Verdict: later.** Needs a Pinterest developer app (an outbound application, so owner). Mock now.

#### US Census Bureau: Monthly Retail Trade (MARTS / MRTS)
- **What it gives:** monthly US retail sales by kind of business, including clothing stores (NAICS 448/4481) and nonstore retailers (454), seasonally adjusted and not adjusted, through the Economic Indicator Time Series API (`api.census.gov/data/timeseries/eits/...`) (https://www.census.gov/retail/ ; API guide https://www2.census.gov/data/api-documentation/EITS_API_User_Guide_Dec2020.pdf).
- **Terms:** public US-government data; a free API key raises limits [U on exact limits].
- **Use:** macro seasonality prior and "is the whole category down" context.
- **Freshness:** advance estimate about 2 weeks after month end.
- **Verdict: now.** Free; a free key is still a key, so tell the owner, but no spend. Mock plus a fixture of the real series.
- **Optional:** BLS CPI apparel (price level) for "is everyone raising prices" context. Same terms class. Now, optional.

### 1.3 Paid third-party market-data providers

| Provider | API? | Data | Cost | Licence to embed in our SaaS | Verdict |
|---|---|---|---|---|---|
| **Jungle Scout API** | Yes (https://www.junglescout.com/products/jungle-scout-api/ [V]) | Amazon keywords by ASIN and by keyword, **historical search volume**, product database, sales estimates, share of voice | Included 100 req/mo on Growth Accelerator / Brand Owner; add-ons 1,000 = $29, 4,000 = $99, 10,000 = $199; overage $0.05 per request [V] | Its terms prohibit "renting, leasing, lending, selling, licensing, sublicensing … or otherwise making available the Services or the Jungle Scout Data to any third party entities", except "Approved Clients" (search summary of the MSA, https://www.junglescout.com/msa-for-agencies-private-equity/ [3P]). Embedding for our tenants therefore **needs a written data licence** | **Later** (owner and legal); best Amazon demand source if licensable |
| **Keepa API** | Yes (https://keepa.com/api-docs/ [V]) | Amazon price, BSR and offer history per ASIN; best-seller lists | From €49/mo for 20 tokens/min; 1 token per ASIN product request; 50 per best-seller list (https://keepa.com/api-docs/plans-tokens.html [V]; prices [3P]) | Terms not publicly readable (only a Scribd copy). Keepa's data is collected by Keepa, not through SP-API, and is not governed by our SP-API AUP, but its **provenance is Keepa's own crawling** [U] | **Later**, only after reading the licence; reputational review, since reviewers may ask where the data comes from |
| **Helium 10** | Enterprise plan only, via a sales call (https://revenuegeeks.com/software/helium-10/api [3P]) | Amazon keyword and product research | Custom | Unknown; enterprise contracts are usually for the subscriber's own use [U] | **Avoid for now** (cost unknown, licence unknown) |
| **eRank** | No public API. Its ToS prohibits "automated systems, bots or software to extract data" (https://erank.com/legal/terms-of-service [3P summary]) | Etsy keyword volume estimates | $5.99–$9.99/mo per user [3P] | No embedding route | **Avoid** (possible later partnership, owner-level) |
| **EverBee** | No public API found; a Chrome extension plus dashboard. Sales figures are "reverse-engineered from review counts, listing age", about 80% claimed accuracy [3P: https://revenuegeeks.com/software/everbee] | Etsy sales and revenue estimates | $29.99/mo [3P] | None | **Avoid** |
| **Alura** | No public API found [3P] | Etsy keyword and product research | subscription | None | **Avoid** |
| Scraper APIs (Apify Etsy/Walmart/TikTok scrapers, ScrapingBee, SerpApi, pytrends) | Yes | Scraped marketplace pages | cheap | Breaks marketplace ToS; exactly what OI-6 forbids | **Avoid, permanently** |

A possible reseller path: the shop connects **its own** Jungle Scout, eRank or other account and uses the output itself (bring your own key). The licence question is then the shop's, not ours [U: Jungle Scout's terms may still restrict third-party apps calling on a subscriber's behalf; read before building].

### 1.4 First-party data (already held)
- **Per shop (strongest, always allowed):** orders and items by design, channel, date and price; per-unit costs (blank, transfer film, label, packaging, labor, fees, ads, refunds) from `finance/profit.ts`; listing status per channel; design tags; fulfillment health. This covers the shop's own seasonality, trend, price-response and margin-at-price analysis with no outside data.
- **Across shops:** see §2.

---

## 2. Cross-tenant benchmarks: what is legitimate

### 2.1 What the marketplace terms say
| Data origin | Rule | Can it feed a cross-tenant benchmark? |
|---|---|---|
| Amazon (SP-API) | AUP §4.4 no aggregation across Authorized Users "to provide or sell to any parties, including competing Authorized Users"; §4.6 no disclosure "individually labelled or aggregated" to other application users | **No** |
| Shopify | §6.2.5 no "competitive benchmarking"; §6.2.8 transfers only as needed for the app's services (including aggregate/derived, per summary [3P]) | **No** |
| Walmart | no aggregation "for any purpose other than to provide the Services"; no derivative products without written authorization | **No** |
| TikTok Shop | share only with Permitted Users; no de-aggregation, profiles or segments | **No** |
| Etsy | no analytics use; minimum data | **No** |
| CSV exports the shop uploads (Etsy/Amazon/TikTok exports) | not obtained through the API, so the API terms don't bind directly; but the seller's own marketplace agreement may treat the data as confidential [U] | **Treat as No.** Same data, same risk; an app reviewer won't distinguish the transport |

**So "median price per product type" and "sell-through by niche" across shops are not legitimate at MVP.** Both are built from marketplace orders. Revisit only with written permission from a marketplace, and counsel.

### 2.2 What is legitimate: InvAI-native operational data
This is data our software generates from the shop's own production, not obtained from a marketplace:
- Film efficiency (gang-sheet utilization %).
- Transfer cost per square inch.
- Press throughput (units per labor hour).
- Reprint rate by reason.
- Median hours from order paid to shipped, and on-time rate (computed by us; the ship-by comes from the channel, so use only the derived rate, never raw channel fields [U]).
- Label cost per shipment by weight band (carrier rates are ours; EasyPost terms [U]).

Blank cost per garment style comes from supplier APIs and POs. S&S and SanMar prices can be account-specific negotiated prices, so **exclude them until the supplier terms are checked** [U].

Conditions:
1. **Contract basis:** InvAI's ToS and DPA must say we may create de-identified aggregate statistics from service usage. The drafts are with `legal-doc-draft`; add the clause and mark it for counsel. Tenants can opt out (`company.settings.benchmarkOptOut`); sample and demo workspaces are always excluded.
2. **k-anonymity:** publish a cell only if it has **k ≥ 10 distinct companies** and **≥ 200 underlying units** (items or shipments).
3. **Dominance rule:** suppress the cell if the largest company contributes **> 30%** of the cell's units, or the top two **> 50%**. This is the standard (n,k) dominance idea statistical agencies use [U on exact parameters; ours are deliberately strict for small N].
4. **No differencing:** fixed dimensions only (garment class × region = US), recomputed **monthly** in a job, never on a live query. No arbitrary filters, and no "benchmark excluding me". Values are rounded: percentiles to the nearest whole %, money to $0.05, rates to 1 decimal.
5. **Output only** p25, median and p75. Never min, max or a count of companies below 20.
6. **Separate store:** a global `benchmark_cells` table holds no `company_id` and no ids, only the dimension keys, statistics, k and computed_at. It is written by a `withSystem` job, the one allowed cross-tenant use (CLAUDE.md). A test asserts that every published row has k ≥ 10.
7. **Expected availability:** needs ≥ 10 active shops per cell, so it is **not useful until well after the pilots**. Build it later (§4); don't block the MVP on it.

---

## 3. Market-analysis algorithm

Principles:
- Deterministic code computes every number. The LLM chooses which tool to call, explains the result, and ranks at most 3 actions. It never invents a number, a competitor or a trend.
- Every signal carries `{value, unit, source, asOf, n, confidence}`.

### Step 1: Collect (job queue, never in the request path)
1. **Scope set.** For each active design and product type the shop sells: design tags, name tokens, garment class (tee, hoodie, sweatshirt, tank, kids, other, from the blank's style), channels listed, and personalization flag.
2. **Own history.** Weekly units, revenue, net and average landed price per design × channel, from the last 156 weeks (3 years) of orders. One order item is one unit.
3. **Demand series** for each niche keyword set (Step 2): weekly interest from each enabled provider (Google Trends, Pinterest, Amazon Brand Analytics for brand-registered shops, Jungle Scout if licensed). Pull 5 years where available; public-query results go in the global cache (§4.3).
4. **Price comparables** for each own listing on channels with an approved pricing API: Amazon `getCompetitiveSummary` (featured offer and lowest offers) for the shop's own ASINs, plus up to 20 comparable ASINs from `searchCatalogItems` on the design's keywords, garment class and "t-shirt". Walmart `getPricingInsights` for own items. **No Etsy, TikTok or Shopify competitor prices** (§1).
5. **Macro series.** Census NAICS 448 monthly sales, not seasonally adjusted, for 10 years.
6. **Record provenance** for every datum: `source`, `fetchedAt`, `asOf` (the provider's data date), `requestKey` and `licence` (`official_api | public_dataset | licensed | first_party`).

### Step 2: Normalize
1. **Niche taxonomy.** A fixed list of about 60–80 niches (for example teacher, nurse, dog-mom, fishing, Christmas, Halloween, 4th-of-July, Mother's Day, birthday-squad, bachelorette, faith, sports-team-generic, retro-70s, funny-dad). Keep it under the PM (a data file, en/es labels).
   - Map each design to up to 2 niches: first by an exact or stemmed tag match against the niche's keyword list.
   - If no match: a Haiku classification with a JSON schema `{niche, confidence}`, accepted only if confidence ≥ 0.7. Otherwise the design is `unclassified` and gets no external signal.
   - The shop can correct the mapping; the correction wins.
2. **Keyword set per niche:** 3–5 canonical queries ("teacher shirt", "teacher t-shirt", "teacher gift shirt"), maintained with the taxonomy, never generated per request. Stable keys keep the caches shared and the series comparable.
3. **Trademark screen before any query or suggestion.** Every keyword and every design idea goes through `trademark.ts`. Terms at or above the trademark-risk threshold are dropped from queries and never suggested (Etsy IP policy: repeat infringement means termination, research 10).
4. **Landed price** = item price + the per-item share of shipping charged − discounts, in cents. Comparables use the same definition (Amazon: listing price + shipping from the offer).
5. **Comparable set filter:** same channel and marketplace (US), same garment class, new condition, same personalization flag, landed price between $5 and $80. Drop outliers outside **[Q1 − 1.5·IQR, Q3 + 1.5·IQR]**.
6. **Time alignment:** ISO weeks in the shop's time zone for its own data. Provider series are resampled to ISO weeks (mean of daily values; monthly series are not resampled; they drive monthly seasonality only).

### Step 3: Compute signals
Notation: `y_t` is the weekly series (own units, or external interest), `t = 1..T`.

**3.1 Trend (momentum)**
- Fit OLS on `z_t = ln(y_t + 1)` over the last **W = 26 weeks** (13 if the design is younger). The slope `β` is per week.
- **4-week growth** `g4 = e^(4β) − 1`. The t-statistic is `t_β = β / SE(β)`.
- Classify:
  - `rising`: g4 ≥ +15% and t_β ≥ 1.7.
  - `falling`: g4 ≤ −15% and t_β ≤ −1.7.
  - `flat`: otherwise.
  - `insufficient`: fewer than 13 points, or `y_t = 0` in more than 50% of weeks.
- **Year over year**, when ≥ 56 weeks exist: `yoy = Σ y(last 4w) / Σ y(same 4w last year) − 1`. Report it only if the denominator is ≥ 10 units (own data) or the interest is > 0 (external).
- **Deseasonalize before the trend call** when a seasonality index exists: `y'_t = y_t / SI(week_t)`. This stops "sales rise in November" from being called a trend.

**3.2 Seasonality index**
- Monthly index `SI_m = mean_y(m) / mean_y(all months)`, averaged over the full years available. It needs **≥ 2 complete years** of the same series; otherwise `insufficient`.
- Source priority: the shop's own design, niche units if ≥ 2 years and ≥ 100 units per year; else the external demand series for the niche (Google Trends, 5 years); else Census NAICS 448 as a **category prior** only (labelled "all US clothing stores").
- **Peak months:** SI ≥ 1.3. **Off months:** SI ≤ 0.8.
- **Lead time** to act = weeks until the first peak month − **(production lead time + 3 weeks listing ramp)** [U: the ramp is a heuristic; tune from feedback]. Production lead time comes from the shop's own median hours from paid to shipped, converted to weeks and rounded up. Flag it "act now" when the lead time is ≤ 2 weeks and the peak is ≤ 10 weeks away.

**3.3 Price position**
- For own landed price `p` and the comparable set `C` (n prices): **percentile** `P = (#{c < p} + 0.5·#{c = p}) / n`.
- Report the median, Q1 and Q3 of `C`, and the Buy Box / featured price where the source gives it.
- Bands: **low** P < 0.25, **market** 0.25–0.75, **premium** > 0.75.
- Minimum n = 8 comparables (n ≥ 20 for "high" confidence).

**3.4 Competition density** (the weakest signal; relative only)
- Amazon only: `D = offers_on_comparables / max(demand_index, ε)`, where `offers_on_comparables` is the sum of offer counts on the up-to-20 comparable ASINs, and `demand_index` is the niche's latest 4-week mean external interest.
- Report it only as a **rank among the shop's own niches** (tercile: less crowded, typical, crowded), never as an absolute number.
- No density for Etsy, TikTok, Shopify or Walmart (no compliant data).

**3.5 Margin at candidate price** (the shop's real costs)
For a design × channel × garment class, from the trailing 90 days of `finance` buckets:
```
unitCost      = (blank + transfer + label + packaging + labor) / units          [cents]
adsPerUnit    = adsCost_channel / units_channel                                  [cents]
refundRate    = refunds / revenue                                                [0..1]
feeCents(p)   = referralFeeCents(channel, category, p + shippingCharged)         [finance/fees; Etsy 6.5% + 3% + 25¢ etc.]
net(p)        = p + shippingCharged − feeCents(p) − unitCost − adsPerUnit − refundRate·p
marginPct(p)  = 100 · net(p) / (p + shippingCharged)
breakEven     = min p such that net(p) ≥ 0            (solve over a 5¢ grid)
floorPrice    = min p such that marginPct(p) ≥ 15     (the wave-17 low-margin line)
```
- Candidate prices: the current price p0, then **p0 × {0.90, 0.95, 1.05, 1.10}**, then Q1, median and Q3 of `C` if available. Round to .99 or .00, following the shop's current ending.
- Output a table of `p, marginPct, net per unit`.
- **Expected profit change** is shown only when the shop has its own price-response evidence: ≥ 2 distinct price points for the design with ≥ 30 units each, in windows without a sale or promotion. Then:
  - Arc elasticity `ε = (ΔQ/avgQ) / (ΔP/avgP)`, clamped to [−4, 0].
  - Projected units `Q(p) = Q0 · (p/p0)^ε`.
  - Projected net `= Q(p) · net(p)`, labelled "estimate".
  - Otherwise show only margin per unit and say the volume effect is unknown.

**3.6 Opportunity score** (used only to rank candidates, never shown as a number)
- `S = 0.35·trendZ + 0.25·seasonLead + 0.20·marginHeadroom + 0.20·(1 − densityTercile/2)`.
- Terms:
  - `trendZ`: t_β clamped to [−3, 3] and rescaled to [0, 1].
  - `seasonLead`: 1 if "act now", 0.5 if a peak is 10–20 weeks out, else 0.
  - `marginHeadroom = clamp((marginPct(p0) − 15) / 30, 0, 1)`.
  - Missing terms are dropped and the remaining weights renormalized.

### Step 4: Confidence
Each signal gets `confidence = s · f · r · a`, with each factor in [0, 1]:
- **Sample size** `s = min(1, n / n_target)`. Targets:

  | Signal | n_target |
  |---|---|
  | Trend | 26 weekly points |
  | Seasonality | 3 years (1 at 2 years = 0.67) |
  | Price position | 20 comparables |
  | Own-data claims | 30 units |
  | Elasticity | 2 × 30 units |

- **Freshness** `f = 0.5^(age / halfLife)`. `age` = now − `asOf`. Half-life per source:

  | Source | Half-life |
  |---|---|
  | Own orders | 7 days |
  | Amazon or Walmart pricing | 1 day (TTL 24 h) |
  | Google Trends and Pinterest | 14 days |
  | Brand Analytics weekly | 14 days |
  | Census | 60 days |
  | Benchmarks | 45 days |

- **Reliability** `r`:

  | Source | r |
  |---|---|
  | First-party orders and costs | 1.0 |
  | Official marketplace API (pricing, Brand Analytics) | 0.9 |
  | Google Trends | 0.8 |
  | Pinterest Trends | 0.7 |
  | Census (category prior) | 0.6 |
  | Licensed estimates (Jungle Scout, Keepa) | 0.6 |
  | Taxonomy mapping by Haiku (multiply in) | its confidence |

- **Agreement** `a`: 1.0 if the independent sources agree in direction (for example own-data trend and external trend both rising), 0.7 if only one source exists, 0.4 if they disagree. When they disagree, say so; don't average them.
- **Bands:**
  - **high** ≥ 0.70: may drive a recommendation.
  - **medium** 0.40–0.69: may drive a recommendation labelled "test".
  - **low** < 0.40: shown only as context, "not enough data". It never drives an action.

### Step 5: Generate recommendations, with guardrails
1. **Candidate rules** run in code over the signals (examples):
   - **R1 Seasonal prep:** a niche peak is ≤ 10 weeks away, and the shop has a design in that niche with confidence ≥ medium. Action: ensure it is listed on every connected channel (reuses the `get_design_insights` cross-listing gap) and stock blanks for the peak. The expected-units estimate is last year's peak units × (1 + yoy), only when last year exists.
   - **R2 Price test up:** price band low, marginPct(p0) < 25, comparables n ≥ 8, trend not falling. Action: test p0 × 1.05–1.10, capped at the comparables' median.
   - **R3 Price floor breach:** marginPct(p0) < 15. Action: raise to `floorPrice`, or stop ads on that design. This needs no external data, so it is always allowed.
   - **R4 Ride a rising niche:** external trend rising with confidence ≥ medium in a niche where the shop has 1–2 designs. Action: design ideas **in that niche**, each run through the trademark check. Never "copy competitor X".
   - **R5 Drop or rest:** own trend falling with confidence high, off-season, and margin < 15%. Action: pause ads and deprioritize.
2. **The LLM receives only rule outputs and signals** (inside the existing `<data>` isolation). It picks up to 3, orders them by opportunity score and confidence, and writes finding → evidence → action → expected impact ("estimate", with its arithmetic), as in the wave-17 analyst mode.
3. **Hard guardrails** (prompt rules plus a post-validator, fail closed):
   - Every number in the answer must appear in a tool output of this turn (existing wave-17 pattern). A validator scans the numbers against the tool data. On a mismatch, regenerate once, then fall back to tool summaries only.
   - Every external fact is cited as `source + asOf date` (for example "Google Trends, week ending 2026-09-20"). Mock data is labelled **"sample data"** everywhere in the UI and the answer.
   - Show the confidence band on every recommendation.
   - **Refuse when thin:** if the signals the question needs are `insufficient` or low confidence, say what is missing ("I need at least 8 comparable Amazon listings; Amazon isn't connected") and give the own-data answer only. Never fall back to model knowledge about markets. The wave-17 rule "never cite outside market facts" becomes "only market facts from market tools".
   - Never name or link other sellers or listings, and never quote competitor listing text. Aggregates (median, percentile) only. This also protects the §4.6-style restrictions.
   - No promises ("will sell"); only estimates with arithmetic.
   - Trademark check on every design idea, keyword or niche name before it is shown. Blocked items are silently dropped and counted in logs.
   - Read-only: recommendations suggest; nothing changes prices or listings (scope item 13).
   - Spanish or English per the user (existing rule).

### Step 6: Feedback loop
1. **Store every recommendation** shown: `market_recommendations` (tenant table, RLS) with `rule`, `targetType/targetId` (design, listing, niche), `action`, `params` (for example the suggested price), `confidence`, `signalsSnapshot` (JSON of the numbers and sources), `baseline` (the last 28 days: units/day, net/day, price), `shownAt`, `conversationId`.
2. **Adoption detection** (daily job, deterministic):
   - A price rule counts as followed if the listing's price moved in the suggested direction by ≥ 3% within 14 days.
   - Cross-listing or seasonal prep counts as followed if a new active listing on the suggested channel appears within 21 days.
   - Design idea counts as followed if a new design in the niche appears within 30 days.
   - The user can also mark a recommendation "done" or "not useful" with one tap. That is the explicit signal, and it wins.
3. **Outcome** 28 days after adoption, a difference-in-differences:
   - Effect: `Δ = (net/day_after − net/day_before)_target − (net/day_after − net/day_before)_control`, where the control is the shop's other active designs in the same garment class.
   - Deseasonalize both sides by SI when available.
   - Label: `improved` if Δ > 0 and the target has ≥ 10 units after; `worse` if Δ < 0 with the same minimum; else `inconclusive`.
   - Not followed → `not_adopted`, still tracked as a natural control.
4. **Use it:**
   - Show the shop "what happened" on past recommendations; the assistant can cite it.
   - Monthly calibration per rule: the success rate by confidence band. If "high" succeeds less than 50% of the time over ≥ 20 adopted cases, raise that rule's thresholds.
   - Tuning uses **InvAI-native outcome labels aggregated per rule** (counts of improved and worse), not pooled marketplace data (Shopify §2.3.24, Amazon §4.4). The tuned parameters are rule thresholds, not a trained model [U: counsel to confirm this counts as outside "develop/train ML" under Shopify's terms].

---

## 4. MVP versus later, interface, jobs, cost

### 4.1 MVP slice (one wave; contract → backend → web)
Build now. Everything runs locally on mocks; no approvals or spend.
1. **The `market` backend module** (new; owner backend-engineer, with ai-engineer for the tools and prompt):
   - The signal engine (§3.1–3.6, pure functions with unit tests on fixed series).
   - Confidence scoring (§3 Step 4).
   - The niche taxonomy file with en/es labels.
   - A design → niche mapper (tag match plus Haiku fallback through the gateway, with a deterministic mock).
2. **Providers with mocks:**
   - `ownData`: real, from our DB.
   - `census`: real call behind `CENSUS_API_KEY` or keyless, plus a recorded fixture.
   - `googleTrends`, `pinterestTrends`, `amazonPricing`, `walmartPricing`: **mock only**, with deterministic series seeded from the keyword hash, plus built-in seasonal shapes (Q4 peak, Mother's Day, back-to-school), so evals are stable.
3. **Four read-only assistant tools** (contract enum change via architect, the same pattern as T-17-1):
   - `get_market_trend {designId|niche, range}`: trend and yoy per source, with confidence.
   - `get_seasonality {designId|niche}`: SI by month, peaks, act-by date.
   - `get_price_position {designId, channel}`: percentile, Q1/median/Q3, n, sources; "not available" for channels without a compliant source.
   - `simulate_price {designId, channel, prices?}`: the margin table from §3.5, own data only, always available.
4. **`market_recommendations` table** plus the adoption and outcome jobs (§3 Step 6) and a thumbs up/down.
5. **Prompt v5 delta:** the market-facts rule, the citation format, "sample data" labelling, refusal thresholds.
6. **Evals** (`ai-feature-with-evals`), for example:
   - Thin data leads to a refusal.
   - Disagreeing sources are named as disagreement.
   - No number without a source.
   - Trademarked niche ideas are dropped.
   - Injection inside keyword data is ignored.
   - A Spanish question gets a Spanish answer.
7. **Web:** tool chips and a "Market" starter question in en/es; a "sample data" badge when a mock source answered.

Later, each needing an OI entry first:

| Item | Needs | Est. |
|---|---|---|
| Google Trends real adapter | alpha application (owner submits), read the alpha terms | after acceptance |
| Amazon Pricing and Catalog real adapter | SP-API app approval (pending) | when approved |
| Amazon Brand Analytics | a brand-registered shop that grants the role | per shop |
| Walmart pricing insights real adapter | Walmart Solution Provider approval | when approved |
| Pinterest trends | Pinterest developer app and access tier | owner applies |
| Jungle Scout (or BYO key) | a written data licence for embedding, or a BYO-key legal check; $29–199/mo | owner and counsel |
| Cross-tenant ops benchmarks (§2.2) | ToS/DPA clause, ≥ 10 shops per cell | post-pilot |
| Etsy competitor price analytics | Etsy's written permission | owner decides whether to ask |

Avoid: all scrapers, eRank, EverBee and Alura (no API), TikTok Creative Center, Helium 10 (for now), and any cross-tenant use of marketplace-origin data.

### 4.2 Provider interface (matches the carrier and supplier adapters)
```ts
// src/integrations/market/types.ts
export type SignalSource =
  | "own" | "census" | "google_trends" | "pinterest_trends"
  | "amazon_pricing" | "amazon_brand_analytics" | "walmart_pricing" | "jungle_scout";
export type Licence = "first_party" | "official_api" | "public_dataset" | "licensed";

export type SeriesPoint = { period: string /* ISO week "2026-W38" or month "2026-09" */; value: number };
export type DemandSeries = {
  source: SignalSource; licence: Licence; query: string; geo: "US";
  granularity: "week" | "month"; scale: "absolute" | "relative_0_100" | "consistent_scaled";
  points: SeriesPoint[]; asOf: string; fetchedAt: string; mock: boolean;
};
export type PriceObservation = { landedPriceCents: number; isFeatured: boolean; offerCount: number | null };
export type Comparables = {
  source: SignalSource; licence: Licence; channel: Channel; ownRef: string /* own ASIN / item id */;
  observations: PriceObservation[]; asOf: string; fetchedAt: string; mock: boolean;
};

export interface DemandProvider {
  source: SignalSource;
  /** Keys are canonical niche queries from the taxonomy, never free text. */
  series(q: { queries: string[]; granularity: "week" | "month"; years: number }): Promise<DemandSeries[]>;
}
export interface PricingProvider {
  source: SignalSource;
  /** Per connection (seller-scoped); results never leave that tenant. */
  comparables(conn: Connection, own: { ref: string; keywords: string[]; garmentClass: string }[]):
    Promise<Comparables[]>;
}
```
- Selection follows `carriers/index.ts`:
  - `marketDemandProviders(scope)` returns the real providers whose key is set in `env` (add to `env.mocks`: `googleTrends`, `pinterest`, `census`, `jungleScout`), otherwise mocks.
  - `marketPricingProvider(scope, channel)` returns the real one only if the channel connection is live and approved.
  - A sample workspace always gets mocks.
- Every result carries `mock: true|false`; the UI and the prompt label mock data.
- Each real adapter has: timeouts (10 s), per-provider rate limiters (Amazon `getCompetitiveSummary` at 0.033 rps, burst 1, per selling partner; Jungle Scout plan quota; Google Trends alpha quota [U]), retry with jitter on 429/5xx, and `UnrecoverableError` on 401/403 (disable the source and raise a health alert).

### 4.3 Caching and jobs (heavy work goes to the queue)
- **`market.refreshDemand`** (nightly at 03:00 UTC, global, `withSystem`):
  - Collects the union of canonical niche queries used by any tenant and fetches each (query, source, granularity) once.
  - Stores in **`market_series_cache`**: global, not tenant data, keyed by canonical query; it holds no `company_id` and no tenant ids.
  - Needs a `record-decision` ADR, because CLAUDE.md rule 7 covers tenant tables. This table holds public-source data only, and queries come from the fixed taxonomy, so no tenant's free text reaches it.
  - TTL: 7 days (weekly series), 30 days (Census). Idempotent upsert on `(source, query, granularity, period)`.
- **`market.refreshPricing`** (per tenant and connection, daily, `withTenant`):
  - Stores comparables in **`market_price_snapshots`** (tenant table, RLS), keyed by `(company_id, channel, own_ref, as_of_date)`.
  - Keep 90 days, then roll up to monthly stats. Raw observations are never kept longer than the marketplace allows; Amazon non-PII per business need, per the DPP [3P].
  - Budget: 20 ASINs per call at 0.033 rps is about 2 calls per minute per seller, so ≤ 2,880 calls/day. A 500-listing shop at 21 ASINs per listing (own plus 20 comparables) needs about 525 calls ≈ 4.4 h, spread over the night.
- **`market.computeSignals`** (per tenant, after both refreshes, and on demand when a design is created):
  - Writes **`market_signals`** (tenant, RLS): one row per `(company_id, subject_type, subject_id, signal, source)` holding value, confidence, n, asOf and inputs hash.
  - Stable `jobId = market-signals:{companyId}:{date}`.
- **`market.trackRecommendations`** (daily, per tenant): adoption and outcome (§3 Step 6).
- **Assistant tools only read** `market_signals` and snapshots, never calling providers in the request path. If the signals are older than 2× the source TTL, the tool returns `stale: true` and confidence falls through `f`.
- **`market.benchmarks`** (monthly, later): §2.2, k and dominance enforced in SQL and asserted in tests.

### 4.4 Cost per tenant (estimate, list prices from `src/ai/models.ts`)
| Item | Basis | Per tenant per month |
|---|---|---|
| Census, Google Trends (alpha), Pinterest, SP-API, Walmart API | free today (the SP-API fees were cancelled 2026-05-12; the Trends alpha has no price published [U]) | $0 |
| Global demand fetches | cached per niche query, shared across tenants | about $0 (quota only) |
| Niche mapping (Haiku 4.5, $1/$5 per MTok) | about 600 tokens per new design; 50 new designs a month | about $0.02 |
| Extra assistant context for market questions (Opus 5, $5/$25 per MTok) | about 3 market tools × 1.5k tokens of input ≈ 5k tokens ≈ $0.025, plus about 400 output tokens ≈ $0.01; 40 market questions a month | about $1.40 |
| Jobs and storage | a few thousand rows per tenant | under $0.10 |
| **MVP total** | | **about $1–2** (dominated by AI; prompt caching lowers it) |
| Optional Jungle Scout (if licensed) | 20 niche queries × 4 per month = 80 requests at $0.029 (the $29 per 1,000 tier), overage $0.05 | + about $2.30–$4 (the platform plan is fixed: $29–199/mo) |
| Optional Keepa | from €49/mo platform-wide (20 tokens/min ≈ 860k tokens/mo) | amortized; about $0.50 at 100 tenants |

---

## 5. Open questions and risks
1. **Etsy live API terms text:** we could not fetch it (403). The compliance-officer should read it in a browser before the Etsy card, especially the analytics clause and the 6 h / 24 h freshness rules [U].
2. **Google Trends alpha terms:** unknown commercial-use terms and quotas. Read them after acceptance and before production use.
3. **Brand Analytics coverage:** probably few DTF shops are brand-registered, so don't design the MVP around it.
4. **CSV-imported marketplace data:** treated as marketplace-origin (no cross-tenant use) pending counsel.
5. **The `market_series_cache` global table:** needs an ADR, because rule 7 has a stated exception only for tenant tables.
6. **Signal quality:** the trend and seasonality thresholds (15% in 4 weeks, t ≥ 1.7, SI ≥ 1.3, k = 10, dominance 30%) are starting points. Tune them from the §3 Step 6 calibration, not by intuition.
7. **Pilot evidence:** SCR-001 noted 0 shops asked for this. Measure use of the four tools and the thumbs up/down from the first pilot week.

## Sources (accessed 2026-09-27)
- Etsy API docs, Commercial Access review criteria: https://developer.etsy.com/documentation/
- Etsy rate limits: https://developer.etsy.com/documentation/essentials/rate-limits
- Etsy API Terms (live, 403 to us): https://www.etsy.com/legal/api ; archived terms: https://www.etsy.com/legal/api-archived/ ; research 10 §Etsy "API Terms" (Aug 2026 Wayback reading)
- Etsy search analytics feature request: https://github.com/etsy/open-api/discussions/681
- Amazon SP-API Acceptable Use Policy: https://solutionproviderportal.amazon.com/solution-provider/policy?policyType=AUP&locale=en_US
- getCompetitiveSummary: https://developer-docs.amazon/sp-api/reference/getcompetitivesummary
- getItemOffersBatch rate change: https://developer-docs.amazon.com/sp-api/changelog/starting-may-1-2023-the-rate-for-the-getitemoffersbatch-operation-within-the-product-pricing-api-will-be-lowered
- SP-API role mappings: https://developer-docs.amazon/sp-api/docs/role-mappings
- Product Pricing use-case guide: https://developer-docs.amazon.com/sp-api/docs/product-pricing-api-v0-use-case-guide
- Brand Analytics reports: https://developer-docs.amazon/sp-api/docs/report-type-values-analytics
- SP-API fee cancellation: https://novadata.io/resources/news/amazon-sp-api-subscription-fees-2026 , https://ppc.land/amazon-drops-sp-api-fees-after-developer-pushback/
- Shopify API License and Terms of Use: https://www.shopify.com/legal/api-terms
- Walmart Pricing Insights: https://developer.walmart.com/us-marketplace/docs/get-pricing-insights-data-for-your-items ; Insights: https://developer.walmart.com/doc/us/mp/us-mp-insights/ ; terms: https://developer.walmart.com/global-marketplace/docs/terms-and-conditions
- TikTok Shop: https://partner.tiktokshop.com/docv2/page/get-shop-performance-202405 ; https://partner.tiktokshop.com/docv2/page/data-security-and-privacy-review ; https://seller-br.tiktok.com/university/essay?knowledge_id=3037474364589840
- Google Trends API: https://developers.google.com/search/apis/trends ; https://developers.google.com/search/blog/2025/07/trends-api ; https://www.searchenginejournal.com/google-trends-api-alpha-launching-breaking-news/551935/
- Pinterest Trends: https://developers.pinterest.com/docs/api/v5/trending_keywords-list/ ; https://developers.pinterest.com/docs/analytics-and-reports/trends/
- Census Monthly Retail Trade: https://www.census.gov/retail/ ; https://www2.census.gov/data/api-documentation/EITS_API_User_Guide_Dec2020.pdf
- Jungle Scout API: https://www.junglescout.com/products/jungle-scout-api/ ; https://support.junglescout.com/hc/en-us/articles/21641823937943-API-Endpoint-Descriptions ; MSA: https://www.junglescout.com/msa-for-agencies-private-equity/
- Keepa: https://keepa.com/api-docs/ ; https://keepa.com/api-docs/plans-tokens.html
- Helium 10 API: https://revenuegeeks.com/software/helium-10/api
- eRank ToS: https://erank.com/legal/terms-of-service ; EverBee: https://revenuegeeks.com/software/everbee
