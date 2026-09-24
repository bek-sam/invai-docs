# How small US apparel print shops that sell on marketplaces actually run, from blanks to shipped orders

**Method.** I ran about 45 web searches and 20 page fetches before the session's shared web-search budget ran out. Every claim below either has a source URL or is marked **[practice, unsourced]**, meaning it is standard industry practice I'm confident in but couldn't pin to a source in this session. Vendor blogs are marketing and their numbers run optimistic; I say so where it matters.

---

## 0. Supplier market in 2026: recent changes a product has to handle

- **S&S Activewear bought alphabroder.** The deal closed on Oct 3, 2024. alphabroder's API traffic was redirected to S&S endpoints on May 30, 2025, and users had to move to S&S API keys, S&S REST or PromoStandards within 3 months. Only alphabroder's EDI inventory, shipment, price and carton files continue.
  - https://members.asicentral.com/news/industry-news/october-2024/ss-activewear-completes-the-acquisition-of-alphabroder/
  - https://cdn.ssactivewear.com/images/sns/2025/integration/flyer/Technical-Transition-Flyer-US-3.pdf
- **Gildan bought HanesBrands.** It closed Dec 1, 2025, at about $4.4B enterprise value.
  - https://www.sec.gov/Archives/edgar/data/1061894/000106189426000004/exhibit991annual2025newsre.htm
- **S&S is now the exclusive US wholesaler for Gildan's brands.** From Dec 28, 2025 that covers Gildan, Comfort Colors, American Apparel and Champion. Hanes went S&S-exclusive in June 2025.
  - https://members.asicentral.com/news/industry-news/august-2025/gildan-names-ss-activewear-as-exclusive-wholesale-distributor-for-american-apparel/
  - https://dtfdallas.com/blogs/news/bella-canvas-leaving-ss-sanmar-update
- **SanMar bought Bella+Canvas.** The deal was announced May 18, 2026 and closed June 29, 2026. SanMar is now the exclusive national distributor, and S&S is phasing out B+C as its stock sells through.
  - https://members.asicentral.com/news/industry-news/june-2026/sanmar-completes-acquisition-of-bellapluscanvas/
  - https://www.bellacanvas.com/bella-canvas-sanmar-acquisition-complete
- **What this means for the platform:** a typical Etsy shop's core blanks (Gildan 64000/5000/18000/18500, Comfort Colors 1717, Bella+Canvas 3001) now come from **two different distributors**: S&S for the Gildan family and SanMar for B+C. Each has its own API, its own $200 free-freight minimum and its own cutoffs. Buying from both is now the normal case, and you should expect more of these ownership changes.

## 1. Buying blanks

**Who they buy from**
- **S&S Activewear:** 18 distribution centers, 1-day delivery to 44 states and 2-day to 99% of the US. Free ground shipping on orders over $200 in the continental US. Orders placed before the distribution center's cutoff ship the same day.
  - https://www.ssactivewear.com/helpcenter/shipping
- **SanMar:** 8 US distribution centers, 1–2 day delivery to most of the country. Free freight over $200 by ground. Its PSST program ("Pack Separately, Ship Together") has a 1 pm cutoff for same-day shipping. SanMar picks the warehouse closest to the destination ZIP.
  - https://www.printavo.com/blog/how-to-get-free-shipping-from-san-mar/
  - https://www.sanmar.com/resources/locationsshipping/warehouses
- **Smaller wholesalers and resellers:** BlankStyle, ShirtSpace, Jiffy, The Park Wholesale and local cash-and-carry shops. They sell single pieces without a resale account, at higher prices.
- **Accounts:** distributors want a business account and a resale certificate to waive sales tax (https://www.sanmar.com/resalecertificate). Wholesale prices are hidden until you log in.

**Blank prices seen in 2025–26 (these vary by color and size, and 2XL and up costs more)**

| Style | Low price seen | Other prices seen |
|---|---|---|
| Gildan 64000 | ~$2.50–$2.95 at bulk resellers | S&S "from $6.96" (public list price) |
| Bella+Canvas 3001 | ~$3.85 | — |
| Next Level 3600 | ~$4.25 | — |
| Comfort Colors 1717 | $8.23–$8.27 at resellers | S&S list "from $13.04" |

- Sources: https://www.ssactivewear.com/p/gildan/64000, https://www.blankstyle.com/1717-comfort-colors-garment-dyed-heavyweight-t-shirt, https://arklavo.com/blogs/custom-apparel-guide/custom-t-shirts-under-10-no-minimum-2026
- **Flag:** list prices and logged-in account prices differ a lot. Tariffs in 2025 put upward pressure on prices (https://www.deconetwork.com/t-shirt-tariffs-how-to-navigating-uncertainty/).

**Supplier APIs**
- **S&S REST API v2** (https://api.ssactivewear.com/v2/)
  - Endpoints: Categories, Styles, Products, Inventory, Specs and Brands. Orders (GET, POST, DELETE), Payment Profiles, Invoices, Returns, CrossRef, DaysInTransit and TrackingData.
  - Login is account number plus API key. Limit is 60 requests per minute.
  - Product data refreshes nightly; inventory refreshes about every 15 minutes (https://www.ssactivewear.com/marketing/edi).
  - It also offers PromoStandards (https://promostandards.ssactivewear.com/).
- **SanMar** (https://www.sanmar.com/resources/electronicintegration/integrationofferings)
  - Offers PromoStandards, flat files over FTP, and direct SOAP web services for product, inventory, invoices, purchase orders and shipment notices.
  - Inventory queries take style + color + size and return **at most 500 per warehouse**. The PromoStandards version returns a consolidated total, also capped at 500.
  - Integration contact: sanmarintegrations@sanmar.com.
  - https://www.sanmar.com/medias/sys_master/root/h5b/hde/10127344533534/SanMar-Web-Services-Integration-Guide-v18.8.pdf
- **PSRESTful** (https://psrestful.com/integrated-suppliers/) wraps 500+ PromoStandards suppliers, including S&S and alphabroder, in REST/JSON.

**How the SKU matrix works [practice, unsourced]**
- Each variant is style × color × size. Size runs are usually S–5XL, and each style has dozens of colors.
- One marketplace listing (design X) fans out to hundreds of blank variants. The shop keeps a mapping from listing variation to supplier variant.
- Distributors use their own codes (S&S has its own SKU and GTIN per variant), so the variation text from the marketplace ("Comfort Colors – Pepper – L") has to be translated into a supplier SKU.

**Reordering [practice, largely unsourced]**
- Shops keep a small stock of top sellers: black, white and sport grey, sizes S–XL.
- They reorder daily or weekly to stay above the $200 free-freight line. Printavo explicitly recommends setting weekly order deadlines to reach it.
- Last-minute orders use same-day distributor shipping, or local will-call pickup where SanMar or S&S has a nearby distribution center.
- Stockouts cluster in peak season (Q4, back-to-school) and on popular colors. The sources advise lining up backup blanks ahead of time.
- Existing inventory tools are general-purpose: Craftybase and Stocksmith (bills of materials; blanks tracked by style and size), Veeqo, Sellercloud. None of them models "design consumes a blank."
  - https://craftybase.com/embroidery-shop-management-software

## 2. Taking in orders from each marketplace

**Etsy**
- **Manual path:** Shop Manager → Settings → Options → Download Data → "Order Items" CSV.
  - https://help.etsy.com/hc/en-us/articles/360000343328
- **API v3:** personalization comes back in the transaction's `variations` array with `property_id` 54. You add tracking with `createReceiptShipment`, which emails the buyer.
  - https://developer.etsy.com/documentation/tutorials/fulfillment/
- **New personalization format (from Feb 2026):** up to **5 questions** per listing. Text answers max out at 120 characters, dropdowns have 1–30 options, and file uploads allow 1–10 files, which appear as URLs. The field name may be something the seller set, not "Personalization."
  - https://developers.etsy.com/documentation/tutorials/personalization-migration/
- **Processing time:** sellers can set anywhere from 1 business day to 10 weeks.
- **Star Seller** requires 95% or more of orders shipped on time with tracking.
  - https://www.etsy.com/seller-handbook/article/1020956976086
  - https://www.alura.io/docs/article/guide-to-etsys-processing-times-and-ship-by-dates
- **If transfers are outsourced, Etsy requires a production partner disclosure on the listing.**
  - https://help.etsy.com/hc/en-us/articles/360000336547

**Amazon**
- **Amazon Custom** puts a "Customized-URL" link in order reports, which downloads a ZIP.
  - Text or option customizations arrive as a JSON or XML file (fonts, colors, text).
  - Image customizations arrive as the customer's image files plus an SVG showing placement.
  - The JSON schema changed on 11/8/24.
  - Through the Orders API, `BuyerCustomizedInfoDetail` gives the ZIP location.
  - https://sellercloud.com/help/omnichannel-ecommerce/amazon-custom
  - https://sellercentral.amazon.com/seller-forums/discussions/t/dac17d0f-c2cf-4b4d-9dea-a843478e9678
- **Add-ons exist just to parse this:** Custom Order Station ($29.99/mo for 1,000 items, $59.99 for 3,000, $119.99 for 10,000) and DataAutomation push the data into ShipStation.
  - https://customorderstation.com/
- **Performance targets:** Late Shipment Rate under 4% and Valid Tracking Rate of 95% or more. Late shipment counts from when shipment is **confirmed in Seller Central**, not when the box leaves.
  - https://sellercentral.amazon.com/help/hub/reference/external/G200285190

**Walmart**
- Requires 99% on-time shipment (measured by the carrier's first scan) and 99% valid tracking.
- An order is auto-cancelled if it isn't marked shipped with tracking by the expected ship date plus 4 days.
  - https://marketplacelearn.walmart.com/guides/Policies%20&%20standards/Shipping%20&%20fulfillment/Shipping-and-fulfillment-policy

**TikTok Shop**
- Orders must be dispatched within 2 business days, or within the seller's configured handling time plus 1 day for made-to-order. Late Dispatch Rate must stay under 4%, with enforcement above 10%.
  - https://seller-us.tiktok.com/university/essay?knowledge_id=3668989549299511
- **Flag, uncertain:** one third-party source (https://amzprep.com/tiktok-seller-shipping-ends-2026-what-next/) says TikTok discontinued traditional Seller Shipping in the US by Mar 31, 2026, in favor of TikTok Shipping, Fulfilled by TikTok or Collections by TikTok. TikTok's own Seller University page still documents Seller Shipping. **Check this directly before designing the TikTok integration.**

**Batching [practice]**
- Shops usually run one or two cutoffs a day, for example pulling orders at 9 am and 1 pm.
- They group orders by method (DTF, DTG, sublimation), by blank style/color/size for picking, and by ship-by date.
- Rush and upgraded-shipping orders go first.

## 3. Print prep

**What a DTF gang sheet is**
- One strip of film holding many designs. Standard width is **22"** (about 56 cm) and length is anything from 1–2 ft up to 20 ft or full rolls.
- Ninja Transfers' fixed sizes are 22"×2/5/10/15/20 ft. Others price by the inch or square inch:
  - about $0.40 per linear inch (a 22×60 sheet for about $24)
  - $0.014–$0.025 per square inch
  - https://ninjatransfers.com/a/faq
  - https://www.teddytransfers.com/gang-sheet/
- Ninja's quoted prices:
  - Earlier sheet prices: 22×24 for $35, 22×120 for $92.
  - Single transfers: 2"×2" from $2 down to $0.70; 11"×11" from $10 down to $3.50 (1–14 pieces vs. 250+).
  - Another source lists 1 ft at $16.99, 2 ft at $19.99 and 5 ft at $49.99.
  - https://ninjatransfers.com/pages/how-much-does-dtf-printing-cost
- Other 22×60 sheets range from about $24 to $50 (Shore Transfer $49.99).

**File requirements vendors expect**
- Transparent PNG at 300 DPI is the de facto standard. Ninja also accepts PSD, PDF, AI, JPG and SVG, and prefers vector.
- Design at the final print size, leave cutting space between designs, don't overlap, and keep glows and shadows away from neighbors.
  - https://dtfwestcoast.com/blogs/news/dtf-gang-sheet-guide-setup-spacing-file-requirements-and-layout-tips
- Ninja recommends the Adobe RGB (1998) color profile.
- Pre-built sheets are uploaded as one PNG or PDF at 22" × length.

**Order numbers on sheets**
- Recommended practice is to put the client name and **order number in the slug or margin area** next to each group of designs, keep each order's artwork together, and group by garment or placement size.
  - https://www.ziddu.com/dtf-gang-sheet-ordering-when-to-split-one-large-job-into-separate-sheets/
  - https://dtfprinthouse.com/blogs/news/arrange-designs-dtf-gang-sheet
- Some tools print order info on the sheet: Antigro's builder lets you customize file names and choose what information to include on the sheet (https://gangsheetbuilder.com/gang-sheet-builder-features-2/), and CADlink v12 prints job labels (below). Beyond that, I found no product that turns marketplace orders into order-labelled gang sheets automatically.
- Today this is done by hand in Photoshop, Illustrator or Canva, or bought as a service: Etsy "gang sheet build services," or emailing files with the order number in the subject line (e.g., build@uploaddtf.com).

**Gang sheet builders**

| Tool | What it does | Price |
|---|---|---|
| Antigro Gang Sheet Builder / Admin Gang Sheet Builder | Shopify app; auto-nests, flags low DPI and overlaps, customizable file names and sheet info. Its Designer product syncs with Etsy, WooCommerce and eBay. | Free to install |
| DTF Gang Sheet App | AI nesting (claims 85–95% sheet use vs. 60–70% by hand); exports PNG at 72/300/600 DPI, PDF, TIFF with a white channel; Shopify and WooCommerce | $40–$799/mo, or $0.15 per 22×36 sheet |
| DesignO, Tally, PixelFlow, DTF Transfer Studio, PrintXpand | Customer-facing Shopify builders for print shops | — |

- Sources: https://apps.shopify.com/antigro-gang-sheet-builder, https://dtfgangsheetapp.com/, https://www.designnbuy.com/dtf-gang-sheet-builder/
- **What's missing in this list:** these tools are built for DTF *print shops selling transfers*, not for *apparel sellers* who need marketplace order → SKU → design file → labelled sheet.

**RIP software (for shops that print their own DTF)**
- **CADlink Digital Factory v12:** hot folders, auto-nesting in the print queue, **print labels and barcodes/QR codes for production**, multi-side job labels, pull-cut indicators, print-length tracking.
  - https://www.dtfgears.com/cadlink-v12-digital-factory-the-1-rip-software-for-dtf-printing-businesses/
- **Inèdit neoStampa (Delta):** color management, white ink control, nesting, gang layouts, 700+ printer models.
  - https://www.inedit.com/en/productos/neostampa/
- **Kothari Print Pro:** a DTG/DTF RIP known for automatic white underbase. I couldn't confirm its gang-sheet specifics.
- Also used: AcroRIP and other bundled RIPs.

**Costs of printing DTF in-house**
- A setup costs $5,000–$20,000. An Epson F2270 24" hybrid runs about $15,495 and prints about 17 m²/hr; white ink needs a DTF kit.
- Consumables per print: ink $0.15–$0.35 for a chest print, film $0.08–$0.12, powder $0.10–$0.20.
  - https://dtfdatabase.com/printers/epson/
  - https://aestheticbk.com/blogs/news/how-much-does-dtg-printing-cost
- Most shops outsource until they pass roughly **100+ transfers a week** (https://aaprintsupplyco.com/blogs/news/how-to-start-tshirt-printing-business-dtf). Per the DTF Dallas guide, sellers switch from single transfers to gang sheets at about 50 or more orders a week.

**DTG**
- **Brother GTX Pro** costs about $18–22k. It needs pretreatment for dark garments (about $0.35–$0.50 per shirt) and ink costs roughly $0.10–$0.28 on light shirts vs. $0.75–$1.62 on dark.
- Brother's SDK creates **ARXP** files and runs a **barcode-per-garment workflow**: scan the ticket and the printer loads that job's settings. Brown Digital Linx connects shopping carts to pretreat, print and cure settings.
  - https://brotherdtg.com/support/automation/
- Throughput: DTG does about 60–100 garments per 8-hour shift on one GTX Pro, vs. 150–200 for DTF with 2 presses (vendor figures). Kornit is the industrial tier.

**Other methods**
- **Screen-printed (plastisol) transfers** are for best sellers. One-color costs about $0.15 each plus about $25 setup; full-color about $1.25 each plus about $65 setup. They beat DTF on cost at around 100 or more of the same design.
  - https://www.fmexpressions.com/pages/full-color-screen-print-transfers
- **Sublimation** needs 65% or more polyester and light garments, so it doesn't work on cotton tees.
  - https://printify.com/blog/best-shirts-for-sublimation/
- **Vinyl (HTV):** simple name and text personalization, cut on a Cricut or plotter **[practice]**.

## 4. Production

**Staged workflow [practice, partly sourced]**
1. Receive the transfers, or print and cure them in-house.
2. Cut the sheet apart, by hand, with a trimmer, or with an auto-cutter.
3. **Sort the cut transfers by order.** Use the order numbers printed in the margin, a printed order ticket or packing slip clipped to the transfer, or put everything in totes, bins or cubbies numbered by order.
4. Pull blanks from shelves using a pick list aggregated by style, color and size. ShipStation pick lists show SKU, description, warehouse location and quantity (https://help.shipstation.com/hc/en-us/articles/360026157971).
5. Press.
6. QC against the ticket: size, color, design, spelling of the personalization, placement.
7. Fold, bag, and pack with the packing slip.

**Barcodes:** barcodes or QR codes on tickets are recommended for scanning jobs through each stage (https://irisdtf.com/blogs/dtf-operations-management/...). CADlink can print barcodes on the sheet, and Brother DTG uses one barcode per garment.

**Press settings**
- DTF runs at 300–325°F for 10–15 seconds with medium-to-high pressure, after a 2–3 second pre-press. Peel hot or cold depending on the film, then do a second press of 5–15 seconds under parchment.
- Ninja's settings: 310°F, 13 seconds, then a 15-second finishing press.
- https://dtfdallas.com/blogs/news/optimal-dtf-heat-press-settings-guide

**How many shirts per hour**
- Vendor claims range from 100–180 an hour manually up to 300–500 an hour with automated ROQ or ColDesi AP360 lines.
  - https://impressionsmagazine.com/build-your-business/automated-heat-pressing-high-volume-dtf-production/170637
  - https://coldesi.com/heat-press-machines/automatic-dtf-heat-press-...
- A more realistic mixed-order POD figure is "60–90 seconds plus handling" per garment (https://dtfprinting.com/tutorials-how-to/dtf-for-print-on-demand-guide), which works out to about **30–60 per hour per operator on one press**.
- Pressing becomes the bottleneck once you can print film faster than you can press it.
- **Flag:** the 180+/hour figures assume same design, same size, long runs. Mixed marketplace orders are much slower because of pick and match overhead.

## 5. Packing and shipping

**Label tools**

| Tool | Marketplace support | Price |
|---|---|---|
| ShipStation | Widest integrations, including Etsy and Amazon; custom fields and automation rules | $9.99–$14.99/mo Starter (50 shipments); $29.99 Standard (about $149.99 at 1,000/mo); $99.99 Scale; $349.99 Premium. 20% off annual. |
| Pirate Ship | Etsy, Shopify, eBay, WooCommerce, BigCommerce integrations; marks orders shipped. No confirmed native Amazon or TikTok integration. | Free, cheapest USPS/UPS rates |
| Veeqo (Amazon-owned) | Native Amazon, Etsy, Walmart, TikTok Shop, Shopify | — |
| Etsy Labels / Amazon Buy Shipping / TikTok labels | Built into each marketplace | — |
| EasyPost / Shippo | APIs to build shipping into your own product | — |

- Sources: https://costbench.com/software/shipping-software/shipstation/, https://www.pirateship.com/integrations/shipping, https://www.veeqo.com/blog/shipstation-vs-pirateship-comparison

**Carrier and postage**
- The standard service for a tee is **USPS Ground Advantage** in a poly mailer, printed on 4×6 thermal labels.
- **From July 12, 2026, USPS commercial Ground Advantage under 1 lb is one price per zone**, no longer priced by the ounce. A 1 lb package costs about $7.61 commercial vs. $9.55 retail.
- Shipments to rural ZIP codes are now charged at the 15.99 oz rate.
- Pirate Ship still offers below-commercial rates tiered at 4, 8 and 12 oz for non-rural destinations.
  - https://support.pirateship.com/en/articles/15453569-july-2026-usps-rate-and-rule-changes
  - https://www.ship.com/post/usps-ground-advantage-vs-priority-mail-2026
- Packaging costs $0.50–$2.00 per order.

**Tracking upload:** buying a label through an integration marks the order shipped and pushes tracking back automatically. Because each marketplace's metrics (Amazon Late Shipment Rate and Valid Tracking Rate, Walmart's 99% targets, TikTok's Late Dispatch Rate, Etsy Star Seller) depend on that confirmation arriving by the ship-by date, late confirmation is a real account-health risk.

## 6. Returns, misprints and customer service

- Personalized items are usually declared **non-returnable**. Sellers reprint or refund only for real defects, misprints or seller mistakes (wrong size or color sent), with photo proof, typically within 30 days.
- Etsy allows return policies per listing (since Oct 2022). Etsy Purchase Protection and cases still apply to seller error.
  - https://printify.com/blog/how-to-make-the-best-etsy-shop-policies/
  - https://podinsights.net/etsy-return-policy-updates-print-on-demand-returns-strategy/
- **Common failure points [practice]:**
  - wrong size or color picked
  - transfer applied to the wrong order after cutting (the main reason to put order numbers on sheets)
  - personalization typos (a design-prep error)
  - transfer lifting or cracking from bad press settings
  - buyer chose the wrong size (usually not refunded)
- **Reprints [practice]:** add the item to the next gang sheet (usually tagged "REPRINT") and cover the blank from stock. Outsourced vendors handle their own misprints case by case (Ninja FAQ).
- **I found no reliable published misprint or reprint rate.** Treat any figure as unknown.

## 7. Economics

**Cost per shirt**
- A typical single-order DTF tee costs roughly **$3–$8** for the blank (up to about $8–13 for Comfort Colors), **$1.50–$5** for an outsourced chest transfer (less on a dense gang sheet), $0.50–$2 for packaging, $4.50–$8 for USPS postage, plus labor.
- Ninja's estimate for pre-printed transfers: about $15 per shirt at 10 shirts, about $9 at 100, under $6 at 1,000.
  - https://ninjatransfers.com/pages/how-much-does-dtf-printing-cost

**Retail prices and margins**
- Typical retail is $22–$38 per shirt, using a 2–3× cost multiplier.
- Claimed gross margin is 50–60% on single retail orders and 35–45% on batches of 6–24.
  - https://weprintupress.com/blogs/dtf-transfer-tips/try-our-helpful-custom-shirt-calculator (vendor source)

**Marketplace fees**

| Marketplace | Fee |
|---|---|
| Etsy | 6.5% transaction + payment processing (about 3% + $0.25) + $0.20 listing, + Offsite Ads when triggered |
| Amazon | About 15–17% referral for clothing |
| TikTok Shop | About 8% for apparel + $0.30 per order |
| Walmart | 6–15% referral, by category |

- Source: https://www.webgility.com/blog/marketplace-fees-amazon-ebay-etsy-walmart. **Flag:** exact percentages vary by category and date.

**Volumes and staffing (weakly sourced)**
- Home shops typically handle 50+ shirts a day in their first 12–18 months. Mid-tier DTF printers such as the Prestige R2 Pro (about $8,500) handle 50–200 shirts a day.
- Typical roles **[practice]**:
  - owner/designer handling listings and artwork
  - order processor or prep person doing mapping, gang sheets and customer service
  - 1–3 pressers
  - 1–2 packer/shippers
  - in larger shops, a picker/receiver for blanks
- At roughly 100–300 orders a day, a shop usually has 3–8 people.
- **Flag:** no hard data found. Validate with customer interviews.

## 8. Gaps a founder could target

1. **The chain from marketplace order to labelled gang sheet is missing in all the tools I found.** Existing builders serve DTF print shops, not apparel sellers.
   - Needed: pull orders from Etsy (new 5-question personalization), Amazon Custom (ZIP/JSON/SVG), Shopify, TikTok and Walmart.
   - Map variation → design file + blank SKU, render the personalization text, auto-nest onto 22" sheets with **order number, line item and size/color printed in the margin next to each design**.
   - Export a 300 DPI PNG or PDF per vendor spec, or feed a CADlink or neoStampa hot folder.
2. **Blank inventory tied to design SKUs.** Each sale consumes a blank; reorder suggestions should batch to reach **both** $200 minimums (S&S and SanMar) and pull live stock through the S&S REST and SanMar/PromoStandards APIs.
3. **A scan-driven production floor.** Barcode order tickets, a tote per order, per-stage status and pick lists grouped by style, color and size.
4. **SLA monitoring across marketplaces.** Track ship-by dates against Amazon's Late Shipment Rate and Valid Tracking Rate, Walmart's 99% targets, TikTok's Late Dispatch Rate and Etsy Star Seller, and upload tracking automatically, or integrate ShipStation, Veeqo or EasyPost.
5. **Reprint and misprint tracking** tied back to cause (picking, pressing, design, vendor).

**Open questions to check directly:**
- whether TikTok Shop still allows seller-bought labels in 2026
- exact logged-in wholesale prices
- actual reprint rates and staffing levels, which need customer interviews in the target city
