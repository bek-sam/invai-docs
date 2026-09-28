# 16. Growth opportunities: what to add next for shops, their business and the platform

- Date: 2026-09-28. Author: product-manager. Why: the owner asked (2026-09-28) for "more research about new ideas to improve the customers' work, their business, and our platform. What to add, how, etc.", then added two questions: can InvAI automate "take top Etsy sellers' designs, put them on a shirt and post the listing", and how to handle ready-made designs that shops buy (PNG/SVG downloads).
- **This is research and ranking only.** Nothing here is in scope. New scope goes through `scope-change-request` and, where it touches cost or risk, the owner (`owner-inbox.md` OI-17). `product/scope.md` is unchanged.
- Builds on (not repeated here): `research/01` (shop workflow), `02` (competitors, Sep 2026 baseline), `03` (ranked pains), `10` (marketplace, carrier and DTF rules), `14` (market signals), `15` (weekly digest); decisions `0006` (v1 cuts) and `0014` (market and digest fences); backlog B-01 to B-142.
- **Method.** Four research passes on 2026-09-28 (customer pain, competitors, industry shifts, design rights and licensing), about 260 searches and page reads in total. Every fact has a URL; all were accessed 2026-09-28.
- **Tags:** **[O]** official or primary (a marketplace, carrier, government, court or vendor's own page). **[P]** press or law-firm analysis. **[3P]** third-party blog, agency or tool vendor. **[vendor]** a vendor making claims about its own market. **[U]** unverified or single-source; confirm before relying on it.
- **Limits, stated plainly:**
  - Reddit refused both fetches and search, again (as in research 03). T-Shirt Forums redirects to a paywall host. Etsy Community posts show titles only without a login. Facebook groups need a login.
  - So the seller voice comes from Amazon Seller Forums, Shopify Community, Trustpilot, Shopify App Store and Capterra reviews, trade press (Impressions, Apparelist, Modern Retail, Retail Brew), TikTok Seller University and vendor blogs.
  - Several fee changes (TikTok 8%, Amazon's on-time delivery bar, Walmart's apparel fee cut) come only from [3P] sources because the seller centers need a login. The owner should confirm them in the real seller centers.
  - **There is still no pilot evidence.** `customers/` is empty. Every score below is from desk research, so confidence is capped at 0.8. The first 2–3 pilots should re-rank this list.

---

## 0. The answer in brief

1. **The biggest new facts since research 02/03:**
   - **"Label printed" is no longer "shipped" anywhere.** TikTok counts late dispatch from the first carrier scan (enforcement back since 2026-04-06). Amazon deactivates listings for missing acceptance scans. Amazon also moved every seller-fulfilled SKU to per-SKU handling times on 2026-06-29.
   - **Costs moved against shops all at once:**
     - USPS removed the ounce tiers on 2026-07-12, so every tee under 1 lb bills at 15.99 oz.
     - The USPS peak surcharge runs 2026-10-04 to 2027-01-17.
     - TikTok reportedly raised its referral fee to 8% [3P] and, from June 2026, moved buyer-remorse return shipping onto sellers.
     - Tariffs changed three times in 2026.
     - SanMar now holds Bella+Canvas exclusively.
   - **Competitors are converging on our wedge:**
     - Pythias added Kohl's and Target Plus, invoicing and AI forecasting.
     - A new gang-sheet app (AutoGangSheet) claims Etsy, Amazon and TikTok intake plus hot folders.
     - Veeqo made labels free and added TikTok and reship.
     - Inktavo became Taivo (11,000 clients) and promises AI.
2. **Top 10 to consider, by score** (§6). Four of them fit current scope; six need a scope change:

   | Rank | Idea | Why |
   |---|---|---|
   | 1 | G-01 Dispatch-scan guard | Catches "label bought, never scanned" before it becomes a late dispatch |
   | 2 | G-03 Design license record | Most shops print bought designs; nobody tracks caps or rights |
   | 3 | G-11 Carrier adjustments and claims in profit | Surprise bills months later; EasyPost now sends the event |
   | 4 | G-04 Q4 margin guard | Peak surcharges, fee and blank-cost changes erase margin quietly |
   | 5 | G-02 Handling-time advisor | Amazon's 2026-06-29 rule; real press-to-ship times per SKU |
   | 6 | G-10 Agent-ready listings | AI shopping agents read structured attributes |
   | 7 | G-05 Remake and reship | TikTok moved return costs to sellers; lost packages mean refund plus remake |
   | 8 | G-06 Capacity planner | Pressing is the bottleneck; plan the week before it breaks |
   | 9 | G-15 Design risk gate | Image-level similarity plus trademark check on every design, bought or made |
   | 10 | G-09 Cash-flow view | Reserves and payout delays while blanks are already paid for |
3. **The owner's design question** (§5):
   - **Copying top sellers' designs: do not build.** It is infringement at scale, breaks Etsy's API terms (putting our Etsy access, and so every shop's order import, at risk) and fits the one theory of vendor liability the courts still recognize: inducement.
   - **The same outcome done legally is buildable:** trend signal → *original* AI design from a niche brief → similarity and trademark gate → mockup → listing draft → batch approval → publish. Expect about $0.06–0.20 per design, plus $0.20 per Etsy listing.
   - "Immediately" is realistic only on Shopify (seconds) and Etsy (after Commercial Access). Amazon, TikTok and Walmart review listings for hours to days.
   - It reopens the "AI design generation" cut in decision 0006, so it goes to the owner as SCR-007. The recommended order is G-03 and G-15 first; they are useful on their own and are the safety gate the generator needs.
4. **Don't build** (§7): design copying, competitor scraping, a transfer-selling gang-sheet storefront, a full B2B decorator suite, AI buyer messaging, demand-forecast ML, per-person productivity ranking by default, printer hardware drivers, auto-repricing.

---

## 1. Customer pain: what is new since research 03

Research 03's ranked list still stands. These are the new or sharper pains. F = frequency and S = severity, each 1–5; both are my judgement.

### 1.1 Shipping and marketplace metrics
- **"A label is not a shipment" (F4, S5).** This sharpens pain #1.
  - Amazon forum: "Merely printing a label does NOT count… You MUST have a carrier acceptance scan… on or before the ship date"; the seller's listings were deactivated for low Valid Tracking Rate. https://sellercentral.amazon.com/seller-forums/discussions/t/e79fa8dc-b9c1-432b-9f2b-0c6c821cb714 [O forum]
  - A carrier missed pickup two days running, and one seller's late-shipment rate hit 23.08%. https://sellercentral.amazon.com/seller-forums/discussions/t/b408c910-a7aa-42d2-8e6f-2927fbe639b1 [O forum, older]
  - TikTok: an order must be "In Transit" (carrier scan) within 2 business days. Late-dispatch rate must stay at or under 4%, and above 10% TikTok caps order volume. Unshipped overdue orders now count. Enforcement returned 2026-04-06. https://seller-us.tiktok.com/university/essay?knowledge_id=3668989549299511 [O], https://www.geekseller.com/blog/tiktok-shop-update-late-dispatch-rate-ldr-enforcement-returns-april-6-2026/ [3P]
- **Amazon handling time moved to SKU level (2026-06-29).**
  - Seller-fulfilled SKUs must use Automated Handling Time or accurate manual per-SKU values; otherwise Amazon sets them.
  - Automated Handling Time gives 180 days of late-shipment protection. Custom and handmade SKUs are exempt.
  - Sources: https://novadata.io/resources/news/amazon-handling-time-fbm-june-29-2026 [3P, cites Seller Central notices], https://www.ecomcrew.com/amazon-tightens-handling-time-rules-for-seller-fulfilled-listings/ [3P]
- **Etsy moved processing time to the variation level.** Slow shipping history now lengthens the delivery estimate buyers see, which affects search. https://blog.ordoro.com/2026/09/24/etsy-holiday-hq-2026/ [3P], https://www.etsy.com/seller-handbook/article/1404283886419 [O]
- **Carrier bills arrive months later (F3, S3).**
  - "$104 shipping adjustment fee three months after the package shipped." https://community.shopify.com/t/i-was-incorrectly-charged-an-adjustment-fee/331556 [O forum, 2024]
  - ShipStation reviewers report adjustments "6–9 months retroactively." https://checkthat.ai/brands/shipstation/reviews [3P]
  - EasyPost added a `shipment.invoice.updated` event on 2026-08-29 (research 10 §8), so we can now see these.
- **Lost packages cost twice (F3, S3).** Sellers say USPS has "refused every claim so far this year" since Ground Advantage. https://forums.collectors.com/discussion/1103009/any-successful-ground-advantage-insurance-claims [forum, date not visible]

### 1.2 Returns and remakes
- **TikTok moved return cost to sellers in June 2026 (F4, S4).**
  - Sellers pay 100% of buyer-remorse return shipping, and items under $10 are refunded without a return. https://vn.link-trans.com/surviving-tiktoks-june-return-policy-update/ [vendor]
  - TikTok customer service can issue partial refunds for the buyer (from 2026-06-02). Residential or unverified return addresses are banned from 2026-08-05, which hits home-based shops. https://seller-us.tiktok.com/university/essay?knowledge_id=6747273381791534&lang=en [O]
  - Apparel returns on TikTok are claimed at 18–25%. https://www.webgility.com/blog/guide-on-tiktok-shop-return [vendor, U]
- **Walmart now enforces a Negative Feedback Rate (from April 2026),** so print-quality complaints count against the account. https://marketplacelearn.walmart.com/guides/Policies%20&%20standards/Performance/Seller-performance-standards [O]
- **Reprint and waste cost is rarely tracked.** Consumable waste runs 5–10%, and shops add a 5–10% contingency. https://coldesi.com/dtf-printing/screen-print-vs-dtf-break-even-analysis-calculator/ [vendor]

### 1.3 Cash flow (new cluster)
- **Reserves and payout delays while blanks are already paid for (F4, S4).**
  - Etsy reserves can hold about 25% of sales for about 45 days. https://alerioprint.com/blogs/blog-posts/etsy-payment-reserve-explained [vendor, U]
  - Etsy Community thread titles: "Payout on Hold for No Reason", "Star seller but reserve and hold remain". https://community.etsy.com/t5/Technical-Issues/Star-seller-but-reserve-and-hold-remain/td-p/146923208 [O forum, titles only]
  - Etsy's own reserve triggers include "sudden order spikes", "late shipments" and "missing tracking". https://www.valueaddedresource.net/etsy-responds-to-seller-concerns-about-payment-reserves/ [P, 2023]
  - TikTok pays 1–31 days after delivery, depending on the settlement tier, and a reserve can add 30 days. https://seller-us.tiktok.com/university/essay?knowledge_id=3995852763531009 [O]

### 1.4 Labor and production
- **Pressing is the bottleneck, and operators are hard to hire and keep (F4, S4).**
  - Impressions: automation matters "for shops struggling to hire and retain production employees"; a warning sign is "transfer accumulation exceeding application capacity." https://impressionsmagazine.com/build-your-business/automated-heat-pressing-high-volume-dtf-production/170637 [P, 2026-09-22]
  - "Tight labor markets and rising operating costs are accelerating the shift toward automation." https://impressionsmagazine.com/news/year-in-review-2025-decorated-apparel-industry-in-the-eyes-of-industry-leaders-1-of-3/167978/ [P, 2025-12-16]
  - A free "Heat Press Labor Calculator" (pieces per hour, labor per piece) suggests shops don't know these numbers. https://dtfprinting.com/tutorials-how-to/heat-press-labor-calculator-article [vendor, 2026-03-19]
  - Pay: heat-press operators $15–25/hr. https://www.ziprecruiter.com/Jobs/Heat-Press-Operator [3P]
- **Orders are getting smaller, more frequent and more urgent.**
  - Marshall Atkinson: "frequent, smaller orders that must be personalized and are often urgent"; he proposes "Value Per Hour" as the metric to watch. https://impressionsmagazine.com/build-your-business/marshall-atkinson-custom-decorated-apparel-shop-print-on-demand-production-efficiency/169223/ [P, 2026]
  - Survey of 73 decorators: 55% name tariffs and 55% cost inflation as top challenges. Over 50% already offer print-on-demand, and 63% get over 10% of profit from it. https://www.apparelist.com/2025/11/07/state-of-the-decorated-apparel-industry-2025-key-trends-risks-and-opportunities-revealed/ [P]
- **Printer downtime.** White-ink clogs are "the number one issue"; printheads cost $900–2,000. https://www.little6llc.com/2026/04/15/the-30-damper-replacement-that-saves-your-2000-printhead-complete-dtf-guide-little-6-industries/ [vendor]
- **No evidence found** on Spanish-speaking floors or on tracking individual employees' errors. Treat both as unproven until pilot interviews.

### 1.5 Costs and supply
- **Blank supply consolidated (F4, S4).**
  - SanMar closed its Bella+Canvas purchase on 2026-06-29 and is the exclusive national distributor; S&S sells B+C only until stock runs out. https://www.prnewswire.com/news-releases/bellacanvas-completes-acquisition-by-sanmar-continues-as-independent-brand-led-by-megan-spire-302813585.html [O]
  - Gildan closed its HanesBrands purchase on 2025-12-01. https://gildancorp.com/en/media/news/gildan-completes-acquisition-of-hanesbrands/ [O]
  - SanMar raised prices 3.5% and added a 3% card surcharge (2025-06-01). https://www.deconetwork.com/announcement-sanmar-tariff-price-changes-for-june-1/ [3P]
- **Tariffs changed three times in 2026:**
  - The Supreme Court struck down the IEEPA tariffs on 2026-02-20, with refunds through CBP's CAPE system. https://www.hklaw.com/en/insights/publications/2026/02/supreme-court-strikes-down-ieepa-tariffs [P]
  - A 10% Section 122 tariff followed on 2026-02-24.
  - Section 301 tariffs of 10–12.5% on 60 economies took over on 2026-07-24; qualifying CAFTA-DR apparel is exempt. https://ustr.gov/sites/default/files/files/Press/Releases/2026/FLIP%20301%20Investigation%20Final%20Action%20FRN%207-23-26%20FINAL.pdf [O]
  - DTF film, ink and powder are mostly China-sourced and pay the stacked duties. https://www.deconetwork.com/surviving-2025-print-shop-tariff-hikes-lets-get-printing/ [3P]
- **Tool prices keep rising.**
  - ShipStation: API $9.95 → $99 (2025-05-28); 1,000 shipments $149.99. https://ship-audit.com/shipstation-review/ [3P]
  - Printify Premium $29 → $39 (2026-02-17). https://mydesigns.io/blog/printify-pricing-changes-2026/ [vendor]

### 1.6 Marketplace policy
- **Etsy suspends print-on-demand shops, and appeals barely work (F3, S5).** "Permanently suspended without warning", appeal denied "within 5 minutes." https://community.etsy.com/t5/Technical-Issues/My-Shop-Was-Permanently-Suspended-Without-Warning-Hoping-for-a/td-p/148158278 [O forum, snippet]
- **Etsy's Creativity Standards (rewritten 2025-06-10)** require the seller's original design and production-partner disclosure. https://www.etsy.com/legal/creativity/ [O]
- **TikTok policy swings.** A forced move to TikTok-only logistics was announced, then paused on 2026-02-17 after backlash. https://www.modernretail.co/operations/tiktok-halts-plan-to-end-independent-shipping-for-u-s-sellers-after-backlash/ [P]
- **Amazon Merch** flags designs "for trademark issues that would've passed two years ago." https://www.bebolddigital.com/blog/amazon-merch-on-demand [3P]

### 1.7 Growth, B2B and transfer selling
- **Shops that sell transfers are in a price war.**
  - Gang sheets sell at $0.017–0.025 per sq in, against a loaded cost of about $0.02–0.03. https://dtfgangsheetapp.com/blog/dtf-print-shop-margins-pricing-strategy [vendor]
  - "Pricing has been sliding… as more shops enter the market." https://dtfprinting.com/tutorials-how-to/how-to-price-dtf-printing [vendor, 2026-07-30]
- **Waiting on customers to approve proofs stalls bulk and team orders** "by a week or more." https://www.onehourtees.com/resources/design-mockups-proofs/ [vendor]
- **TikTok creator samples:** sellers face "hundreds of pending sample requests." TikTok added a Sample Integrity Policy on 2026-06-18. https://seller-us.tiktok.com/university/essay?knowledge_id=6118437723506474&lang=en [O]
- **"Where is my order?" messages are 25–40% of support volume** [vendor, https://alhena.ai/blog/wismo-ai-order-tracking/]. Etsy Purchase Protection requires a reply to Help-with-Order messages within 48 hours. https://help.etsy.com/hc/en-us/articles/7471925990807-Etsy-s-Purchase-Protection-Program [O]

---

## 2. Competitors: what changed against the Sep 2026 baseline (research 02)

| Product | Change since baseline | Source |
|---|---|---|
| **Pythias** | Kohl's and Target Plus channels ("18+ marketplaces"); Stripe customer invoicing; AI production forecasting for staffing; AI mockups; Brother GTX and folding-machine integrations; badge login and shift management (all claims). Paid onboarding: remote $3,000, on-site from $15,000. Tiers: $199 (500 orders, 2 integrations), $599 (3,000, 5), $1,499 (15,000), $3,000 (unlimited); overage $0.25–0.08 per order. Founding cohort discounts of 25%/20%/10%. No public reviews found. | https://pythiastechnologies.com/fulfillment-cloud [O vendor] |
| **AutoGangSheet** (new) | Claims Shopify, Etsy, Amazon and TikTok intake, ShipStation, AI nesting, hot folder/RIP, packing slips. No published price. **The closest new threat, coming from the gang-sheet side.** | https://autogangsheet.com/ [O vendor] |
| **Build A Gang Sheet** | Adds order automation and a print queue; claims 4,600 shops and 13,000+ sheets a day | https://buildagangsheet.io/ [vendor] |
| **CADlink Digital Factory v12** | Rebuilt gang-sheet generator, hot folders, barcode automation. No public job-status API found | https://dtfgears.com/cadlink-v12-what-it-is-and-why-it-matters-for-your-dtf-printing/ [3P] |
| **Veeqo** (Amazon) | TikTok Shop (Nov–Dec 2025); Reship from the original order (2026-07-17); Buy Shipping protection on API labels (2026-06-01). Labels stay free; new $19 inventory and $350 high-volume plans | https://www.veeqo.com/pricing [O], https://releasebot.io/updates/veeqo [3P] |
| **Taivo** (was Inktavo) | Launched 2026-09-22 as parent of Printavo, InkSoft, OrderMyGear, GraphicsFlow and others: 11,000+ clients, "AI-enhanced capabilities" promised. Printavo lists Power Scheduler (capacity), Mockup Creator, **labels at $0.01 each via EasyPost** and a QuickBooks export | https://www.prnewswire.com/news-releases/taivo-launches-as-new-parent-company-bringing-prominent-branded-merchandise-technology-brands-together-302885095.html [P], https://www.printavo.com/pricing/ [O] |
| **YoPrint** | Shopify integration (2026-05-23), Mockup Creator (2026-05-28), customer portal rebuild. $69/$149, no transaction fees | https://www.yoprint.com/updates [O] |
| **MyDesigns** | "Scout AI" agent finds niches and generates designs (Pro, claim). Trustpilot 2.9/5: "they lost all my designs" (2026-07-17) | https://mydesigns.io/pricing [O], https://www.trustpilot.com/review/mydesigns.io [3P] |
| **STAHLS' Fulfill Engine** | Dye sublimation via Vapor Apparel (Mar 2026). Still Shopify-only. $500/mo plus $0.50 per item | https://fulfillengine.com/pages/pricing [O] |
| **ShipStation** | Trustpilot 3.5 (699 reviews): "recurring authentication issues" (2026-09-04), "Constantly loses connection" (2026-09-18) | https://www.trustpilot.com/review/shipstation.com [3P] |

**Features competitors have that we lack**, by how many products have them:
1. Mockup creation (5 products). We have flat tee mockups only.
2. Customer invoicing and payments (5).
3. Quotes, proof approval and customer portal (5; B2B-oriented).
4. B2B, team or merch web stores (5).
5. QuickBooks sync (4).
6. RIP hot-folder handoff (3, and all three are DTF-specific).
7. AI design plus demand research (MyDesigns; strongly praised).
8. Capacity scheduling and staffing forecasts (Printavo, Pythias).
9. Reship from the original order (Veeqo).
10. Printer and machine integrations (Pythias).

Nobody offers a returns portal, AI buyer messaging, piece-rate pay or TikTok sample management.

**So what:**
- The wedge (marketplace orders → order-labeled sheets → scan-checked floor) is still ours at mid-market prices, but the gap is closing from two sides: gang-sheet apps adding intake, and Pythias adding breadth.
- Two moves protect it:
  - make the floor measurably better than a print queue: dispatch-scan guard, capacity and labor data;
  - make the RIP handoff at least as good as the gang-sheet apps' (G-17).
- **Pricing note for OI-1 (not a feature):** Printavo charges $0.01 per label and Veeqo nothing. Our code's 2–5¢ label fee and the concept's 10¢ will be compared with those. Pythias at $599 for 3,000 orders prices mid shops above our $349 Growth plan. This belongs in a `pricing-experiment`; the owner decides prices.

---

## 3. Industry and platform shifts (2025–2026), ranked by impact on a mid-size in-house shop

| # | Shift | Effective | Source | So what |
|---|---|---|---|---|
| 1 | Amazon per-SKU handling time; Automated Handling Time gives 180-day late-shipment protection; on-time delivery bar reportedly 97% → 93.5% [3P] | 2026-06-29 | novadata, ecomcrew (above) | Handling time must come from real press-to-ship times (G-02) |
| 2 | USPS: ounce tiers removed for commercial Ground Advantage (everything under 1 lb bills at 15.99 oz), dim divisor 166 → 139, about +11.8% [3P]. Peak surcharge 2026-10-04 to 2027-01-17, $0.40+ | 2026-07-12 | https://about.usps.com/newsroom/national-releases/2026/0511-usps-recommends-competitive-price-changes-for-july-2026.htm [O], https://www.easypost.com/blog/peak-season-surcharges-2026/ [3P] | Profit must use the bought label cost and show the surcharge (G-04) |
| 3 | Tariffs: IEEPA struck down (refunds via CAPE), Section 122 at 10%, then Section 301 at 10–12.5% on 60 economies | 2026-02-20 / 02-24 / 07-24 | USTR (above) [O] | Blank and film costs change; margins need a refresh, not a fixed cost (G-04) |
| 4 | SanMar owns Bella+Canvas; S&S phases it out. Gildan owns Hanes | 2026-06-29; 2025-12-01 | above [O] | Bella 3001 shops need SanMar plus several suppliers per blank (G-08) |
| 5 | TikTok: late dispatch counted from the carrier scan; referral 6% → 8% [3P]; forced logistics paused; return shipping on sellers | 2026-04-06; 2026-08-04 [3P]; 2026-02-17; June 2026 | above | Dispatch-scan guard (G-01), remake and reship cost (G-05), channel profit |
| 6 | Agentic commerce: Etsy items buyable in ChatGPT, Gemini, Google AI Mode and Copilot; Google's Universal Commerce Protocol (2026-01-11); Shopify turned UCP on for every store (Summer '26) | 2025-09 to 2026-06 | https://blog.google/products/ads-commerce/agentic-commerce-ai-tools-protocol-retailers-platforms/ [O], https://www.shopify.com/editions [O], https://techcrunch.com/2026/05/05/etsy-launches-its-app-within-chatgpt-as-it-continues-its-ai-push/ [P] | Listing attribute completeness now affects sales (G-10) |
| 7 | De minimis ended; Etsy requires DDP for cross-border sellers | 2025-08-29; 2026-07-09 | https://www.cbp.gov/sites/default/files/2025-08/factsheet_suspension_of_duty-free_de_minimis_treatment.pdf [O] | Overseas print-on-demand competitors are weaker, which favors US in-house shops (tailwind for our market) |
| 8 | Etsy Creativity Standards and production-partner disclosure enforced; Etsy agreed to sell Depop to eBay | 2025-06-10; 2026-02-15 | https://www.etsy.com/legal/creativity/ [O], https://investors.etsy.com/news-events/press-releases/detail/217/ebay-to-acquire-depop-from-etsy [O] | Original design and "made by" data matter (§5, B-14) |
| 9 | USPS finances (about $25B lost over 3 years; cash warning) and slower rural network | 2026 | https://www.cnn.com/2026/03/18/us/us-postal-service-financial-crisis-hnk [P] | Delivery estimates less reliable; a second carrier is insurance |
| 10 | UPS and FedEx general rate increase 5.9%, peak surcharges from 2026-09-27/28 | 2025-12-22 / 2026-01-05 | https://www.fedex.com/content/dam/fedex/us-united-states/services/surcharge_and_fee_changes_2026.pdf [O] | USPS stays the default for tees |

Also noted, not ranked:
- Amazon's SP-API developer fee was proposed, then cancelled on 2026-05-12 [P, https://ppc.land/amazon-introduces-fees-for-third-party-developer-api-access-in-2026/]. Design for low GET volume in case it returns.
- Amazon Seller Assistant is becoming agentic and gives free AI listing help, so our AI listing value has to be cross-channel plus the trademark check. https://www.cnbc.com/2025/09/17/amazon-ai-agent-sellers.html [P]
- The 1099-K threshold is back to $20k/200 [O IRS].
- Whatnot live selling passed $8B [O Whatnot].
- Temu's Local Seller Program is open to US sellers [P].
- Hybrid DTG/DTF printers (Epson F1070, Brother GTX DTF) and roll-to-roll auto-cutters are spreading [O/P]. Auto-cut sheets need cut marks (B-79).

---

## 4. Ideas across three lenses

Effort: **S** = one card, **M** = 2–3 cards (about one wave), **L** = more than a wave. "Scope" says whether an idea fits `scope.md` as written or needs an SCR.

### Lens A: the customer's daily work (floor efficiency, fewer errors)

**G-01. Dispatch-scan guard ("bought is not shipped").**
- **Pain and evidence:** pain #1 sharpened (§1.1): TikTok counts from the carrier scan; Amazon deactivates listings for missing acceptance scans.
- **Segment:** mid and large (daily pickups); small shops benefit too.
- **How it works:**
  - The shipping module watches each label from purchase to first carrier scan, using EasyPost tracker events (B-66) and the mock.
  - When a label has no acceptance scan by the shop's pickup cutoff (a setting), or by the channel's dispatch deadline minus a margin, raise a Today alert: "12 labels bought yesterday have no carrier scan. Pickup missed?".
  - Show the at-risk dispatch count per channel in the Order Hub.
  - End-of-day SCAN form (B-25) as the fix.
- **Repos:** backend (shipping, today), contracts (alert kind), web (Today, Orders).
- **Data:** label bought at, first tracker event, channel dispatch rule (`CHANNEL_RULES`), shop pickup cutoff.
- **Effort:** M. **Scope:** fits items 1 ("at-risk alerts") and 7 ("tracking"); record a clarification when specced.
- **Dependencies:** B-66 (EasyPost tracker webhooks); a real EasyPost key for live data (mock until then).
- **Revenue and retention:** protects the metric shops fear most; a daily reason to open InvAI.

**G-02. Handling-time and processing-time advisor.**
- **Pain:** Amazon's per-SKU handling time (2026-06-29) and Etsy's per-variation processing time (§3 #1, §1.1).
- **Segment:** mid and large sellers on Amazon or Etsy.
- **How it works:**
  - The production module already records scan timestamps (`on_sheet` → `pressed` → `packed` → `shipped`).
  - Compute the 90th-percentile import-to-ship time per design × blank × channel over the last 28 days, add the shop's buffer, and recommend a handling time per SKU.
  - Export a CSV for Amazon's handling-time template and Etsy's processing profiles.
  - It **suggests; it never writes** listings, the same rule as fence "no automatic listing changes".
  - Show "peak mode" suggestions when the backlog grows (pain #11).
- **Repos:** backend (production, orders, catalog), contracts, web (Catalog or Orders settings).
- **Data:** item transitions, ship-by rules, SKU map.
- **Effort:** M. **Scope:** new, **SCR-004**.
- **Dependencies:** none (CSV); direct writes would need SP-API and Etsy approval (Later).
- **Revenue:** a concrete, marketable 2026 compliance feature; it also feeds G-06.

**G-05. Remake and reship after shipment.**
- **Pain:** TikTok return-cost shift (June 2026), lost packages and USPS claim denials, Walmart's Negative Feedback Rate (§1.1, §1.2). Research 03 pain #12. Veeqo shipped Reship on 2026-07-17.
- **Segment:** all.
- **How it works:**
  - From a shipped order, "Remake" creates new units linked to the original. Each unit reuses the original print file, lands on the next gang sheet tagged REMAKE, and goes through the floor scan like any unit.
  - A reship label follows.
  - Reason codes: `lost_in_transit`, `damaged`, `print_defect`, `wrong_item`, `buyer_size`.
  - Remake cost (blank, film, label) posts to profit against the original order, design and channel.
  - An optional carrier-claim tracker (filed / paid / denied).
  - Today's reprint flow (B-87) covers only pre-ship defects.
- **Repos:** contracts (new transition shipped → remake units), backend (orders, production, shipping, finance), web, floor (REMAKE tag).
- **Effort:** M. **Scope:** **SCR-005** (a new state path).
- **Dependencies:** none. Real claims filing is manual; no carrier claims API is assumed.
- **Revenue:** makes the true cost of returns visible, which strengthens profit (item 8).

**G-06. Capacity planner (press and printer load board).**
- **Pain:** pressing bottleneck and hiring (§1.4); peak season (pain #11). Competitors: Printavo Power Scheduler, Pythias staffing forecast.
- **Segment:** mid and large.
- **How it works:**
  - Per day, units due to ship vs press capacity (presses × pieces per hour, measured from scans, G-07) and printer capacity (sq ft per hour, planned from the lower spec number, research 10 §8).
  - Minus a morning maintenance block (B-35).
  - Shows red days 3–10 days ahead and suggests actions: pull sheets forward, add a shift, lengthen processing time on a channel (links to G-02).
  - A descriptive projection from open orders only. **No demand-forecast model** (fence).
- **Repos:** backend (production, today), contracts, web (Production).
- **Effort:** M. **Scope:** **SCR-006**.
- **Dependencies:** settings for presses and printers; better with G-07 data.
- **Revenue:** a Growth/Pro plan differentiator; pairs with the digest.

**G-07. Labor per piece and station throughput ("value per hour").**
- **Pain:** §1.4 (the labor calculator, Marshall Atkinson's "Value Per Hour"). Profit currently uses a flat labor estimate (`finance/profit.ts` `laborCost`).
- **How it works:**
  - Pieces per hour per station and per shift from scan gaps, excluding idle gaps over a threshold.
  - Measured labor cents per piece replaces the estimate in profit.
  - Per-person views are **off by default**; the owner turns them on, with a note for staff. Employee-monitoring rules vary by state, so compliance must review this.
- **Segment:** mid and large. **Effort:** M. **Scope:** item 8 covers labor cost as an input; per-person views need an SCR. **Risk:** staff privacy and trust.
- **Revenue:** real cost per piece is what shops can't compute today.

**G-17. RIP handoff that matches the gang-sheet apps.**
- **Pain:** competitors' hot-folder feature (§2); CADlink looks up jobs by job name or barcode (research 10 §8).
- **How it works:**
  - Phase 1 (S): the sheet file name and header barcode carry the sheet id (B-79); a per-vendor naming template; one-click "download today's sheets" as a zip in print order.
  - Phase 2 (L): a small desktop sync agent that drops sheets into a RIP hot folder. That is a new repo and a signed installer, so it waits for pilot demand.
- **Scope:** item 4 (PNG and PDF) covers phase 1; phase 2 is an SCR.
- **Revenue:** defends the wedge against AutoGangSheet and CADlink v12.

**G-13. Pack photo proof.**
- **Pain:** returns and arbitration (TikTok), USPS claims ask for photos (§1.1, §1.2).
- **How it works:** the pack station takes one photo of the folded shirt with its order label, stored 90 days and attached to the order for disputes.
- **Effort:** M (camera flow in the floor app, S3 retention). **Scope:** SCR. **Risk:** storage cost, and photos must show no buyer PII (the shipping label must be out of frame). **Score:** lower until a pilot asks.

### Lens B: the customer's business (margin, cash, growth)

**G-04. Q4 margin guard (cost-change radar).**
- **Pain:** §3 #2, #3, #5 (USPS tier removal and peak surcharge, tariffs, TikTok fee); research 03 pain #6.
- **Segment:** all.
- **How it works:**
  - Profit already uses the bought label cost.
  - Add a digest and Today detector: "Margin on design D1042 on TikTok fell from 38% to 22% in 2 weeks: label +$0.55 peak surcharge, fee 6% → 8%".
  - Nightly blank cost refresh from the S&S price API into blank costs (with the old cost kept) and an alert when a design's margin drops below the shop's target.
  - Suggestions only; nothing changes prices (fence).
  - Fee tables per channel with an effective date (extends B-13).
- **Repos:** backend (finance, inventory, digest detectors), web.
- **Effort:** M. **Scope:** fits items 6, 8 and 17 (digest detectors); no SCR.
- **Dependencies:** a real S&S key for live prices; confirm the TikTok 8% before encoding it.
- **Revenue:** makes the "true profit" promise concrete in Q4.

**G-09. Cash-flow view.**
- **Pain:** §1.3 (reserves, TikTok settlement tiers); Etsy says missing tracking and late shipments trigger reserves.
- **Segment:** small and mid.
- **How it works:**
  - A 4-week view: expected payouts by channel, from order dates plus each channel's payout rules and any reserve the shop enters or imports from the payout CSV.
  - Against committed spend: open POs, the label run-rate, the plan fee.
  - Flags "reserve risk" when late or no-tracking counts rise.
- **Repos:** backend (finance, new payout rules table), web (Profit).
- **Effort:** M. **Scope:** SCR (new area).
- **Confidence:** medium. We haven't confirmed which payout and reserve fields each channel's CSV carries; check that first with an `import-dry-run` on a pilot's files.
- **Revenue:** a reason for the owner to open InvAI weekly; ties into the digest.

**G-03. Design license record.** See §5.3 (owner topic). S effort.

**G-15 and G-14.** Design risk gate and original AI designs. See §5.2 (owner topic).

**G-16. Manual and wholesale orders with a proof-approval link.**
- **Pain:** §1.7. Most decorators also take local and team orders; every decorator tool has quotes and approvals.
- **How it works:**
  - Create an order by hand (customer, lines, blanks, art) with a "wholesale" channel.
  - Send a signed proof link (the `/l/:token` pattern from decision 0016): the customer sees a mockup and clicks approve.
  - Then the normal pipeline: sheets, floor, labels, profit.
  - **No invoicing or payments in phase 1**; a payments phase needs Stripe Connect and is an owner decision.
- **Segment:** small and mid shops with side B2B work.
- **Effort:** M. **Scope:** SCR (a new channel type). **Risk:** outbound email to non-users, needing CAN-SPAM checks and OI-13 sending-domain work.
- **Revenue:** fills idle press time; a reason not to keep Printavo alongside.

**G-18. TikTok creator sample tracker.**
- **Pain:** §1.7. **Blocked:** the TikTok API isn't approved, and it's a niche need. Later.

### Lens C: our platform (retention, expansion, moat, onboarding, integrations)

**G-10. Agent-ready listings.**
- **Pain and trend:** §3 #6. AI shopping agents rank structured attributes, and Shopify turned UCP on for every store.
- **How it works:**
  - Listing drafts gain required attributes per channel: material, fit, size chart, care, color names, processing time from G-02.
  - The validator scores completeness, and the drafts export them.
- **Repos:** backend (ai validators, catalog), contracts, web (Listings).
- **Effort:** S. **Scope:** fits item 10 ("validators"). **Confidence:** medium; we don't know yet how many DTF-shop sales come through agents.
- **Revenue:** cheap; keeps our listing tool ahead of Amazon's free assistant.

**G-11. Carrier adjustments and claims in profit.**
- **Pain:** §1.1 (bills months later).
- **How it works:** consume EasyPost `shipment.invoice.updated` (research 10 §8); update the label cost and profit line (restating the period); show adjustments per week in the digest; flag repeat offenders by package preset (dimensions matter since USPS's divisor 139).
- **Repos:** backend (integrations carriers webhook, shipping, finance), web.
- **Effort:** S. **Scope:** fits items 7 and 8 (profit must be correct).
- **Dependencies:** a real EasyPost key and webhook (mock event until then).
- **Revenue:** profit you can trust.

**G-08. More than one supplier per blank, plus SanMar.**
- **Pain and new evidence:** SanMar exclusively holds Bella+Canvas since 2026-06-29 (§1.5). Bella+Canvas 3001 is a core Etsy blank (research 01 §0).
- **How it works:**
  - A blank SKU can have several supplier SKUs, with a preferred supplier.
  - POs are split per supplier, each toward its $200 free-freight minimum.
  - A SanMar PromoStandards adapter, mock first (B-36 exists).
- **Effort:** L. **Scope:** reopens "SanMar" in decision 0006, so it needs an SCR with this new evidence. It is not in the top 5 SCRs because shops can buy SanMar by hand ("mark placed manually", B-86) meanwhile.
- **Dependencies:** a SanMar account and integration approval (owner).
- **Revenue:** onboarding fit for every Bella shop.

**G-12. Switch-from importers (onboarding).**
- **Pain:** §2. Shops leave ShipStation, Printavo and spreadsheets; research 02 §8 lists 5–8 tools.
- **How it works:** guided imports for SKU maps (from ShipStation product CSVs and spreadsheets), blank costs, design files (bulk upload with a code from the file name), and package presets, with an `import-dry-run`-style report.
- **Effort:** M. **Scope:** item 14 (onboarding) covers the checklist; importers need an SCR. **Revenue:** activation and self-serve for small shops (a segment rule).

**G-19. Amazon Buy Shipping labels.**
- On-time delivery protection only applies to Buy Shipping and Veeqo labels (§3, SFP) [3P].
- **Blocked** on SP-API (decision 0006), so it sits on the Later list.

---

## 5. The owner's design questions

### 5.1 Part 1: "Take top Etsy sellers' designs and post them automatically" (the literal version)

**What the law says**
- Copyright protects expression, not ideas (17 USC 102(b)) [O] https://www.law.cornell.edu/uscode/text/17/102.
  - "A retro sunset with a cat" is a free idea.
  - Another seller's specific art, or something substantially similar, is infringement.
- **Statutory damages:** $750–30,000 per work, up to **$150,000 per work if willful** (17 USC 504(c)) [O] https://www.law.cornell.edu/uscode/text/17/504. Infringement is strict liability; innocence only lowers the minimum to $200. https://www.vondranlegal.com/when-does-the-innocent-infringement-defense-apply-in-copyright-law [3P]
- **Counterfeit trademarks on apparel:** up to **$2,000,000 per mark per type of goods if willful** (15 USC 1117(c)) [O] https://www.law.cornell.edu/uscode/text/15/1117.

**What has happened to print-on-demand sellers and platforms**
- **Harley-Davidson v. SunFrog:** a $19.2M award against a print-on-demand platform. https://abovethelaw.com/2018/04/what-harley-davidsons-19-2m-throttling-of-sunfrog-really-means-and-its-not-the-money/ [P]
- **Ohio State v. Redbubble (6th Cir., 2021):** a print-on-demand marketplace can be a direct infringer. https://law.justia.com/cases/federal/appellate-courts/ca6/19-3388/19-3388-2021-02-25.html [O]
- **Neutral intermediaries can win** (Atari v. Redbubble jury verdict 2021; Atari v. Printify fizzled, 2024). https://www.morganlewis.com/pubs/2021/11/jury-finds-for-online-marketplace-over-atari-in-trademark-infringement-case [P]. Sellers of the copies get no such shield.
- **"Schedule A" suits** in the N.D. Illinois: about 2,846 cases in 2013–2023, with sealed filings and asset freezes on marketplace and payment accounts. https://millerjohnson.com/ndil-shreds-the-schedule-a-playbook-specificity-required/ [P]
  - Courts narrowed them from mid-2025 (one freeze over 252 sellers was dissolved). https://irwinip.com/2025/06/ndil-hits-pause-schedule-a-suits-face-new-scrutiny/ [P]
  - They remain a live tactic, for example for the NFL. https://www.vondranlegal.com/nfl-ip-defense [3P]
- **Automated copy-and-list has already been tried and exposed.** In December 2019, bots that auto-listed images from "I want this on a shirt" replies were baited by artists into listing "this site sells STOLEN artwork" and Disney logos. https://waxy.org/2019/12/how-artists-on-twitter-tricked-spammy-t-shirt-stores-into-admitting-their-automated-art-theft/ [P]

**What the marketplaces do**
- **Etsy:**
  - The IP policy terminates repeat infringers and refuses service to a banned seller's new shops. https://www.etsy.com/legal/ip/ [O]
  - The Creativity Standards (2025-06-10) require the seller's original design. https://www.etsy.com/legal/creativity/ [O]
  - Etsy's API terms forbid automated access to "analyze, or scrape" listings and collecting content "for analytics, machine learning, training AI models" without written permission. https://www.etsy.com/legal/api/ [O; wording from the page snippet, since it returns 403 to us]
- **Amazon Merch on Demand:** creators must hold all rights; violations mean removal, suspension or a ban. https://merchbanao.com/blog/amazon-merch-ai-policy/ [3P; the official page is login-only]
- **TikTok Shop:** an IP policy with account penalties. https://seller-us.tiktok.com/university/essay?knowledge_id=6837901778306818 [O]. The reported July 2026 move to a 0–1,000 Account Health Rating is [U].

**Liability for InvAI as the vendor**
- After *Cox v. Sony* (US Supreme Court, 2026-03-25), contributory copyright liability needs **inducement** or **a service tailored to infringement**. https://www.sidley.com/en/insights/newsupdates/2026/03/us-supreme-court-clarifies-standard-for-contributory-copyright-liability [P]; see also *MGM v. Grokster* (2005) [O].
- A feature whose purpose is "find other sellers' bestsellers and republish them" meets both prongs. A general design tool does not.
- I found no case against a SaaS vendor for exactly this [U]; that is a gap in the evidence, not a safe harbor.

**It breaks our own fences**
- "No scraping, ever".
- "No Etsy competitor data until Etsy agrees in writing" (OI-10).
- "No automatic listing changes" and human approval on AI listings (item 10).
- AI design generation is out of the MVP (decision 0006).
- **The existential part:** losing Etsy Commercial Access would break order import for every customer.

**Verdict: do not build it, in any form.** The shops would carry strict, per-work liability and account bans. InvAI would carry inducement exposure and lose its marketplace access. No price or speed advantage is worth that. Record it in the "don't build" list (§7) and in the SCR-007 fences.

### 5.2 Part 2: the legitimate version (same speed, original designs)

**The outcome the owner wants:** go from "this niche is rising" to a live listing in minutes, without copying anyone.

**Pipeline (each step uses what we have, plus three new pieces):**

1. **Trend and niche brief (exists).** Sources:
   - Market signals (item 16): the shop's own sales trend and seasonality, Census, and Google Trends or Pinterest when approved (OI-9).
   - The seasonal calendar (R1 rules).
   - The shop's own best sellers.
   - Output: a *brief* ("retro 70s camping, dad humor, earth tones, text-led"), never a competitor image. The niche taxonomy is already trademark-clean by construction (`product/market-niches.md`).
2. **Original design generation (new, G-14).**
   - An image model generates 2–4 candidates from the brief plus the shop's style settings. Text-led designs suit Ideogram; flat or vector designs suit Recraft.
   - Output at 12 × 16 in at 300 DPI (3600 × 4800 px) after upscaling in `invai-imaging`, with the background removed.
   - The prompt refuses brand, character, celebrity, team and "in the style of <living artist>" requests. Prompt and output are stored for audit.
3. **Design risk gate (new, G-15; also runs on uploaded and bought designs):**
   - OCR text plus the existing trademark check (`modules/ai/trademark.ts`, class-25 marks, Claude judge on ambiguous hits).
   - USPTO TSDR lookup for live marks (free API, 60 requests/min) [O] https://data.uspto.gov/apis/api-rate-limits.
   - Web image similarity through a lawful paid API:
     - Google Cloud Vision Web Detection: 1,000 per month free, then $3.50 per 1,000 [O] https://cloud.google.com/vision/pricing.
     - TinEye: from $200 for 5,000 searches [O] https://blog.tineye.com/new-image-search-pricing/.
     - Bing Visual Search was retired on 2025-08-11 [O].
   - Perceptual hash against the shop's own catalog, to avoid duplicate listings.
   - The result is a risk score with reasons, using the B-46 thresholds: 60 or more blocks; 25–59 needs a recorded human review.
4. **Mockups (exists, extend).** `invai-imaging/app/mockups.py` draws a flat tee tinted by blank color. Add a hoodie silhouette and back print (M, imaging).
5. **Listing draft (exists).**
   - The AI listing pipeline (item 10) with validators and trademark check.
   - Etsy disclosure fixed to describe the *design* as AI-assisted and "Designed by" the seller (B-14; Etsy allows seller-prompted AI art with disclosure [O] creativity page).
   - `production_partner_ids` when the shop outsources transfers.
6. **Approval (exists, extend).**
   - A batch review screen: design, similarity hits, trademark result, mockup and copy side by side.
   - Approve one or approve all clean ones in a batch. Human approval is mandatory; it also adds the human creative contribution the Copyright Office looks for.
   - A per-shop daily cap, for example 25 per day, to avoid spam and listing-flooding flags (Etsy prohibits spam and duplicates [O] https://www.etsy.com/legal/sellers/).
7. **Publish (partly exists; approvals gate it):**
   - **Shopify:** `productCreate` is immediate. After 50k variants, creation is throttled to 1,000 variants/day on non-Plus stores [O] https://shopify.dev/changelog/api-call-limits-will-be-applied-to-variant-creation.
   - **Etsy:** create as draft (no fee), then activate ($0.20 per listing per 4 months) [O] https://developer.etsy.com/documentation/tutorials/listings. **Needs Etsy Commercial Access (OI-3, B-108).** Until then: CSV export.
   - **Amazon:** `putListingsItem` is asynchronous (accepted is not live) [O]. Needs SP-API (deferred).
   - **TikTok:** 24–72 h product review [3P]. **Walmart:** up to 6 h, or 48 h in manual review [O] https://developer.walmart.com/us-marketplace/docs/item-setup-sla-and-exceptions.
   - **So "immediately" means:** on Shopify, live seconds after the human clicks approve. On Etsy, the same once approved. On the others, submitted immediately and live in hours to days.

**Models and their commercial terms** (prices from `research/08` and the vendors' pages)

| Service | Commercial use on merch | IP indemnity | Price per image |
|---|---|---|---|
| OpenAI GPT Image (1.5 / 2) | Yes | "Copyright Shield" for API output; **excludes trademark claims** and known infringement [O] https://openai.com/policies/service-terms/ | about $0.015 (mini) to $0.05 (medium) |
| Google Imagen 4 on Vertex / Gemini image | Yes | Vertex generative-AI indemnity; void if used to infringe on purpose [O] https://cloud.google.com/terms/generative-ai-indemnified-services | $0.02–0.06; no alpha channel |
| Adobe Firefly | Yes; licensed training data; Content Credentials | Enterprise plans only [O] https://business.adobe.com/products/firefly-business/firefly-ai-approach.html | Enterprise quote [U] |
| Ideogram 3 | Paid plans are commercial [O] https://ideogram.ai/legal/tos/ | None found [U] | $0.03–0.09; best text; transparent output |
| Recraft V4 | Commercial | None found [U] | Raster $0.035; SVG $0.08 [O] https://www.recraft.ai/docs/api-reference/pricing |
| FLUX (BFL API) | Commercial; **the customer indemnifies BFL** [O] https://bfl.ai/legal/flux-api-service-terms | Reverse | about $0.03/MP |
| Midjourney | Paid plans; companies over $1M revenue need Pro | None; being sued by Disney and Universal [P] | No public API: **not usable** |
| Stability SD 3.5 | Free under $1M revenue, then enterprise licence [O] https://stability.ai/license | None | Self-host |

**Copyright status of AI designs:** the Copyright Office (Part 2, 2025-01-29) says prompts alone are not authorship [O] https://www.copyright.gov/ai/Copyright-and-Artificial-Intelligence-Part-2-Copyrightability-Report.pdf, and *Thaler v. Perlmutter* (D.C. Cir., 2025-03-18) requires a human author [O]. So a purely AI design can be copied by others without recourse. Shops protect themselves through human edits and trademarks. **The UI must say this plainly;** we must never imply a shop "owns" an unedited AI design.

**Cost per approved design:**
- 3 candidates at about $0.04 each: $0.13.
- Upscale plus background removal: about $0.01.
- Web similarity: $0.004–0.04.
- USPTO: $0.
- Claude copy and trademark judge: $0.01–0.02.
- **Total: about $0.15–0.20, or about $0.06 with one candidate.** The marketplace fee comes on top ($0.20 on Etsy).
- At 200 designs a month per shop that is about $30–40, so it must be metered as AI credits (billing item 15). Credit pricing is the owner's call.

**Architecture in InvAI (no new repo):**
- `invai-contracts`: `design.generate` / `design.riskCheck` procedures, a `design_generation` record, and new AI routes in the route enum.
- `invai-backend`:
  - `src/integrations/imagegen` (provider interface plus a deterministic mock, like carriers and market);
  - `src/integrations/similarity` (Vision, TinEye, mock);
  - `src/modules/ai` (the brief builder from market signals, the generation job on the `ai` queue, the risk gate, credits);
  - `src/modules/catalog` (the design created from an approved candidate).
  - Heavy work goes on the queue. There is a spend breaker per tenant and globally (B-15).
- `invai-imaging`: upscale (Real-ESRGAN-class), background removal, pHash, hoodie mockup; the pixel caps from B-19 apply.
- `invai-web`: an "Ideas" screen (brief → candidates → gate → mockup → draft) and the batch approval queue.
- Evals: one eval set for the brief-to-prompt step, including refusal cases (brands, characters, living artists), per decision 0007.

**Effort:** L, about 2 waves: (1) G-15 gate plus G-03 license record, (2) G-14 generator plus the Ideas screen and batch approval. Publishing beyond Shopify waits on approvals.

**Scope:** reopens the "AI design generation" cut (decision 0006, reason: IP risk and Etsy Creativity Standards). The new evidence (**SCR-007**):
- Etsy's 2025 Creativity Standards now explicitly allow seller-prompted AI designs with disclosure, which answers half of the original reason.
- Competitors have made it table stakes: MyDesigns Dream and Scout, Printify's AI generator, and Pythias AI mockups.
- The IP half of the risk can now be mitigated with image similarity plus trademark gates and indemnified models, which didn't exist as priced APIs in our v1 research.
- The owner asked for it directly (2026-09-28).
- This is owner-level: new recurring spend, IP risk and outside accounts.

### 5.3 Part 3: ready-made designs that shops buy (PNG/SVG downloads)

**What typical licenses say**

| Source | Terms | Source link |
|---|---|---|
| Creative Market | Personal: "End Products Not For Sale". Commercial: "up to 5,000 end products for sale". Extended: "up to 250,000". No warranty or indemnity text | https://creativemarket.com/licenses [O] |
| Creative Fabrica | Basic POD vs Full POD (unlimited sales "as-is"). **Subscription downloads may be sold only while subscribed:** "when your subscription ends, you will have to stop selling". Single purchases are lifetime | https://www.creativefabrica.com/subscription-license/ [O, snippet], https://help.creativefabrica.com/hc/en-us/articles/360031036351 [O] |
| Design Bundles | Print-on-demand needs the paid "POD Add-On". Designs may **not** be used as-is on print-on-demand sites; they must be edited into a "new and unique transformative design" | https://designbundles.net/license [O], https://fontbundles.freshdesk.com/en/support/solutions/articles/42000103254 [O] |
| Etsy commercial-license listings | Often capped around 500 physical items per design, no digital resale; "the license seller is not responsible for IP violations" | e.g. https://www.etsy.com/listing/1285079719/commercial-use-license-physical-items [O listing] |

**Why a bought license doesn't protect the shop**
- A seller can't license rights it doesn't hold. Designs with Disney characters, NFL or NCAA marks, celebrities or "inspired by" brands are unlicensed at the source.
- The shop that sells the physical shirt is the direct infringer. Innocence only lowers damages, and license sellers disclaim indemnity.
- Enforcement examples:
  - Disney actions against Etsy and Amazon sellers of Disney-themed goods. https://creatorslawfirm.com/2023/01/12/hot-legal-news-for-2023/ [3P]
  - NFL marketplace complaints and Schedule A suits (§5.1).
  - I found no court docket naming a specific Creative Fabrica file [U].
- **A second, Etsy-specific problem:** under the 2025 Creativity Standards, a purchased graphic used as-is can be removed from Etsy *even with a valid license*, because it isn't the seller's original design. https://www.listadum.com/blog/etsy-creativity-standards [3P]. It can be fine on Shopify, TikTok or wholesale if the license allows it.

**Safer sources, in order**
1. The shop's own art, or commissioned art under a written assignment.
2. Indemnified AI generation (Firefly enterprise, Vertex Imagen, OpenAI; OpenAI excludes trademark claims).
3. Large marketplaces with explicit print-on-demand terms: Creative Fabrica Full POD single purchase, Creative Market Extended, Design Bundles with the POD add-on *and* transformation. The terms are clear, but there is still no indemnity.
4. Small Etsy license sellers (lowest confidence).

Every source still goes through the same trademark and similarity gate.

**G-03. Design license record (the feature)**
- **What:** per design, a license record:
  - source (own, commissioned, Creative Fabrica, Design Bundles, Creative Market, Etsy seller, AI model, other);
  - seller name or URL;
  - license type;
  - unit cap (or unlimited);
  - subscription-bound, with an end date;
  - "as-is allowed" yes or no;
  - allowed channels;
  - proof file (receipt or license PDF, S3 upload through the existing files module).
- **Counter:** units sold against the cap, from our own order items (one item = one unit), all channels together.
  - Warn at 80% of the cap. Block adding the design to a new gang sheet at 100%; an owner override is logged.
  - Also block when a subscription-bound license has ended, or when the listing channel isn't allowed (for example Etsy for an as-is purchased graphic).
- **Checks:** the trademark check (text plus OCR) runs on purchased designs at upload, not only on AI listings. G-15 adds image similarity.
- **Flags:** in Catalog (design list badge: "No license on file", "82% of cap"), in the listing flow (validator warning), and in the digest (a D-series detector: "3 designs near their license cap").
- **Repos:** contracts (license schema on the design), backend (catalog table and counter job, production sheet-build guard, ai validators), web (Catalog, Listings).
- **Effort:** S–M (one wave card for backend plus contracts, one for web).
- **Scope:** it touches items 3 (SKU mapper and design data), 8 (units per design) and 11 (trademark check), but a license table and a blocking rule at sheet build are new behavior, not a small tweak. It needs a small SCR, **SCR-003**. It adds no spend and lowers risk, so the PM could accept it. It goes to the owner with the others because the owner asked for it and because blocking a sheet affects floor flow.
- **Revenue and retention:**
  - Unique: no competitor found tracks license caps.
  - It lowers the chance a shop loses its Etsy account, the one event that ends our subscription too.
  - A clear marketing line, reviewed by compliance before any public claim.

---

## 6. Scores

Formula: **impact (1–5) × reach (1–5) × confidence (0.2–1.0) ÷ effort (S = 1, M = 2, L = 4)**.
- Impact is measured against the ranked pains (research 03 plus §1).
- Reach is the share of target shops (mid first) that have the pain.
- Confidence is capped at 0.8 with no pilot evidence, and lowered for [3P]/[U] sources or unknown data availability.
- Items blocked on an outside approval rank below every usable item (the `prioritize-backlog` rule), whatever their score.

| Rank | ID | Idea | Lens | Impact | Reach | Conf. | Effort | Score | Scope | Blocked on |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | G-01 | Dispatch-scan guard | A | 5 | 5 | 0.8 | M | **10.0** | items 1, 7 | — (B-66 first; mock works) |
| 2 | G-03 | Design license record | B/C | 4 | 4 | 0.6 | S | **9.6** | SCR-003 | — |
| 3 | G-11 | Carrier adjustments and claims in profit | C | 3 | 4 | 0.7 | S | **8.4** | items 7, 8 | — (real key for live) |
| 4 | G-04 | Q4 margin guard | B | 4 | 5 | 0.8 | M | **8.0** | items 6, 8, 17 | — (S&S key for live) |
| 5 | G-02 | Handling-time advisor | A | 5 | 4 | 0.7 | M | **7.0** | SCR-004 | — (CSV) |
| 6 | G-10 | Agent-ready listing attributes | C | 3 | 4 | 0.5 | S | **6.0** | item 10 | — |
| 7 | G-05 | Remake and reship | A/B | 4 | 4 | 0.7 | M | **5.6** | SCR-005 | — |
| 8 | G-06 | Capacity planner | A | 4 | 4 | 0.6 | M | **4.8** | SCR-006 | — |
| 9 | G-15 | Design risk gate (image similarity + trademark on every design) | C | 4 | 4 | 0.6 | M | **4.8** | SCR-007 phase 1 | small spend (Vision/TinEye account; owner) |
| 10 | G-09 | Cash-flow view | B | 4 | 4 | 0.5 | M | **4.0** | SCR | — |
| 11 | G-07 | Labor per piece and station throughput | A | 3 | 4 | 0.6 | M | 3.6 | item 8 / SCR (per person) | — |
| 12 | G-12 | Switch-from importers | C | 4 | 3 | 0.6 | M | 3.6 | SCR | — |
| 13 | G-08 | Several suppliers per blank + SanMar | C | 4 | 4 | 0.8 | L | 3.2 | SCR (reopens 0006) | SanMar account (owner) |
| 14 | G-16 | Manual and wholesale orders with proof link | B | 3 | 3 | 0.5 | M | 2.25 | SCR | sending domain (OI-13) |
| 15 | G-17 | RIP handoff (naming, zip; desktop agent later) | A | 3 | 3 | 0.5 | M | 2.25 | item 4 / SCR (agent) | — |
| 16 | G-13 | Pack photo proof | A | 3 | 3 | 0.5 | M | 2.25 | SCR | — |
| 17 | G-14 | Original AI designs from a niche brief | B | 4 | 3 | 0.5 | L | 1.5 | SCR-007 phase 2 (reopens 0006) | image-model key and spend (owner); Etsy approval to publish there |
| — | G-19 | Amazon Buy Shipping labels | C | 4 | 3 | 0.6 | M | (3.6) | Later | SP-API approval |
| — | G-18 | TikTok creator sample tracker | B | 2 | 2 | 0.4 | M | (0.8) | Later | TikTok Partner approval |

**Wedge check** (`prioritize-backlog` step 6): the top 5 hold two wedge items. G-01 protects the floor-to-label step, and G-02 is fed by floor scans. G-03 and G-15 protect the listing side of the wedge (IP takedowns are pain #2). None of the top 10 adds a new channel or a new product line.

**Why the owner's design generator ranks 17th, and how to reach it anyway:** it is large, needs new spend, reopens a decision, and only Shopify can publish instantly today. Its two safety parts (G-03, G-15) rank 2nd and 9th and are worth building for purchased and uploaded designs alone. Building them first means the generator later ships on a tested gate. Recommended sequence: G-03 → G-15 → a G-14 pilot on Shopify with one pilot shop.

---

## 7. Don't build (and why)

| Idea | Why not |
|---|---|
| Copy or "remix" top sellers' designs automatically | Infringement at scale, strict liability for shops, inducement exposure for us, and breaches Etsy's API terms and our "no scraping" fence (§5.1). Permanent |
| Scrape Etsy, Amazon or TikTok bestseller or trend pages | Permanent fence (`scope.md`, decision 0014); risks Etsy Commercial Access and SP-API |
| A storefront gang-sheet builder to sell transfers to other decorators | Crowded (Build A Gang Sheet claims 4,600 shops; Antigro, Kixxl, DTFGSA), a price war below cost (§1.7), and off our wedge (marketplace sellers). Revisit only if 2 pilots already sell transfers and ask |
| A full B2B decorator suite (quotes, invoices, team and web stores) | Taivo, Printavo, DecoNetwork and InkSoft own it with 11,000+ clients. We take only the thin slice (G-16) |
| AI buyer messages or auto-replies | Cut in decision 0006; Etsy's rules say never email Etsy buyers (B-14); Etsy API v3 has no conversations endpoint. Alerts only |
| A demand-forecast model | Fence in `scope.md` (decision 0006 stands); capacity planning (G-06) uses open orders only |
| Per-person productivity ranking on by default | Trust and state monitoring-law risk; no evidence shops want it (§1.4). Station-level first, per person opt-in (G-07) |
| Printer and heat-press hardware drivers (Brother GTX, IoT presses) | Few shops per model; the RIP is the stable interface (G-17) |
| Automatic repricing | Fence: suggest only |
| A tariff-refund (CAPE) helper | Most shops buy from distributors and aren't the importer of record |
| New channels now (Whatnot, Temu, Kohl's, Target Plus) | Breadth before the wedge is excellent; no pilot asks |
| Amazon Buy Shipping before SP-API | Blocked (decision 0006); on the Later list |

---

## 8. Scope-change requests drafted (top 5 needing scope)
- `product/scope-changes/SCR-003-design-license-record.md` (G-03)
- `product/scope-changes/SCR-004-handling-time-advisor.md` (G-02)
- `product/scope-changes/SCR-005-remake-and-reship.md` (G-05)
- `product/scope-changes/SCR-006-capacity-planner.md` (G-06)
- `product/scope-changes/SCR-007-original-design-pipeline.md` (G-15 + G-14; reopens decision 0006)

All five are "sent to owner" as **OI-17**. The in-scope items (G-01, G-11, G-04, G-10) need no SCR. They go into the next `prioritize-backlog` run with specs. Backlog rows B-143 to B-161 are in `waves/backlog.md` under "Proposed (not approved)".

## 9. Open questions
1. Pilot interviews (owner): do shops lose Amazon or TikTok metrics to missed pickups (G-01)? What share of their designs are bought, and from where (G-03)? Do they take wholesale work (G-16)?
2. Confirm in the seller centers (owner): the TikTok 8% referral fee, Amazon's on-time delivery bar, and Walmart's apparel fee cut.
3. Customer-success: in an `import-dry-run`, which payout and reserve fields do the Etsy and TikTok payout CSVs carry (G-09)?
4. Compliance: a review of the state employee-monitoring rules before any per-person view (G-07), and of any public claim about license tracking (G-03).
5. Data-analyst: add the label-fee comparison ($0.01 Printavo, $0 Veeqo) to the OI-1 pricing experiment.
