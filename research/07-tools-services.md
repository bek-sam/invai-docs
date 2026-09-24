# InvAI third-party stack: costs for Pilot, Growth and Scale (researched 2026-09-23)

**How to read this report**
- **Scenarios:** Pilot is 3 shops, 27k labels/mo, $1k MRR. Growth is 20 shops, 240k labels/mo, $7k MRR. Scale is 100 shops, 1.2M labels/mo, $40k MRR.
- **Verification tags:**
  - **[V]** means I read the figure on the vendor's official pricing page today.
  - **[U]** means the figure is unverified: it comes from memory, a vendor's pricing calculator, or a street price. Confirm these before committing.
- **Research gaps:** web search hit the session cap early, so all research used direct WebFetch. Several pages returned 403, 404 or a certificate error: SendGrid pricing, Orb, Plausible pricing, Zebra/reseller hardware pages, and UPS developer (timed out).

---

## 1. Shipping label APIs (the biggest cost and the biggest revenue lever)

**Assumptions**
- 1 label per order.
- Address validation on every order is shown as a separate line; in practice run it only on flagged addresses.
- Tracking is included for labels bought through the provider.
- Average postage is about $5/label [U] (used only for the billing note at the end of this section).

| Option | Price basis (source) | Pilot | Growth | Scale | Pros | Cons | Fit |
|---|---|---|---|---|---|---|---|
| **EasyPost Suite / Forge** | Free up to 3,000 labels [V]. Per-label fee above that is not shown on the page; **$0.08/label assumed [U]**. Bring-your-own carrier accounts $20/mo [V]. Tracker $0.01–0.03 [V]. Insurance 1%, $1 minimum [V]. Forge is white-label with sub-accounts and **FlexRate markup** [V]. https://www.easypost.com/pricing, https://www.easypost.com/forge | (27,000−3,000)×0.08 = **$1,920** | 237,000×0.08 = **$18,960** | 1,197,000×0.08 = **$95,760** (list price; Forge is priced by sales, and a much lower rate is typical at this volume [U]) | Built-in markup via FlexRate. Code-free sub-accounts. ZPL 4x6, SCAN forms, returns, address verification, insurance, tracking webhooks. USPS Commercial and cubic rates [U]. | Per-label fee not public. FlexRate and USPS Claims **only work with Self-Managed Billing**, so you collect postage from shops yourself. | **9** |
| **Shippo API (Starter) + Platform Accounts** | 30 free, then $0.07/label [V]. US address validation $0.02 [V]. Tracking $0.02 [V]. Insurance 1.25% [V]. Headless "Managed Shippo Accounts" for marketplaces [V]. https://goshippo.com/pricing/api, https://docs.goshippo.com/docs/platformaccounts/platform_accounts/ | 26,970×0.07 = **$1,888** (+$540 if every order is validated) | 239,970×0.07 = **$16,798** (+$4,800) | 1,199,970×0.07 = **$83,998** (+$24,000). Premier plan is custom-priced. | Transparent pricing. Batch of 10k labels per call. Manifests. Platform accounts meet USPS/UPS marketplace rules [V]. | No documented markup feature (possible via Premier or partner terms [U]). Validation fees add up. | **8** |
| **ShipStation API (ShipEngine)** | Free plan: $0 platform fee with ShipStation's discounted carrier rates [V]. Advanced: $600/mo for 10k labels, then $0.06–0.075/label, BYO carriers [V]. Enterprise (API sub-account creation) is custom [V]. https://www.shipstation.com/shipping-api/pricing/ | Advanced: 600 + 17,000×0.06 = **$1,620**, or 600 + 17,000×0.075 = $1,875. Free plan: **$0** | 600 + 230,000×0.06 = **$14,400** | 600 + 1,190,000×0.06 = **$72,000** (you would negotiate Enterprise) | Lowest verified list price per label. Free tier on their carrier rates. Address validation, ZPL, manifests. | Creating sub-accounts through the API is Enterprise-only. No published markup mechanism [U]. | **8** |
| Veeqo (Amazon) | Free shipping software. Up to 5% back in credits [V]. https://www.veeqo.com/pricing | $0 | $0 | $0 | Very cheap rates for the merchant. | Built for a single merchant, not multi-tenant resale. You cannot add markup. | 3 |
| Stamps.com API | REST/SOAP, USPS only. Pricing not published [V]. https://developer.stamps.com/ | n/a [U] | n/a | n/a | USPS depth | USPS only. Pricing through sales. Weak platform model. | 4 |
| Pirate Ship | No public developer API. The site lists only integrations and spreadsheet import [V/U]. https://www.pirateship.com/ | n/a | n/a | n/a | Best retail USPS cubic rates | **No API.** Not usable. | 1 |
| USPS APIs v3 direct | Free API. Label APIs **require USPS Ship enrollment, an Enterprise Payment System (EPS) account and separate approval** [V]. https://developers.usps.com/getting-started | $0 + development time | $0 | $0 | No per-label fee. Commercial and cubic pricing. | Heavy compliance work. Reselling postage as a platform is legally murky. Single carrier. You build SCAN forms and returns yourself. | 4 |
| UPS API direct | Free. Merchant connects their own UPS account via OAuth [U: page timed out]. | $0 | $0 | $0 | Uses the shop's own negotiated rates | Markup on UPS rates is not allowed [U]. Single carrier. | 3 |

**Earning per label**
- Only **EasyPost Forge (FlexRate, verified)** documents a postage markup.
- With Shippo or ShipStation, charge a per-label "software fee" on your own Stripe invoice instead.
- Example: charge $0.15/label against EasyPost's assumed $0.08 fee:
  - Pilot: 27,000×0.15 − 1,920 = **$2,130/mo net**
  - Growth: 36,000 − 18,960 = **$17,040**
  - Scale: 180,000 − 95,760 = **$84,240**
- Treat per-label fees as **pass-through COGS**. Set the markup at or above the provider fee.

**USPS Ground Advantage cubic and commercial rates**
- EasyPost, Shippo and ShipStation all give USPS Commercial pricing.
- Cubic support for Ground Advantage should be confirmed with sales [U].

**Critical billing trap with self-managed billing**
- InvAI would collect all postage from shops: about 27k×$5 = $135k/mo at Pilot and $6M/mo at Scale [U].
- **Do not collect postage by card.** At Scale, 2.9% of $6M is about $174k/mo.
- Instead, use prefunded wallets topped up by **ACH debit (0.8%, capped at $5)** [V]. For example, 3 shops topped up weekly is 12 pulls × $5 = $60/mo.
- The alternative is EasyPost-managed billing, which loses FlexRate markup.

**Recommendation:** EasyPost Forge. Negotiate the per-label fee before Growth.
**Runner-up:** ShipStation API, or Shippo Platform Accounts.

---

## 2. Silent printing from the browser to thermal printers

**Assumptions**
- 2 prints per order (label + packing slip or DTF ticket): 54k / 480k / 2.4M prints per month.
- Sub-accounts = number of shops.
- Printers: 10 / 60 / 300.

| Option | Price basis (source) | Pilot | Growth | Scale | Pros | Cons | Fit |
|---|---|---|---|---|---|---|---|
| **PrintNode Integrator** | Standard $60/mo: 100k prints, 20 sub-accounts, overage $0.60 per 1k prints and $3 per extra account. Large $500/mo: 500k prints, 200 accounts, overage $0.50 per 1k [V]. https://www.printnode.com/en/pricing | Standard (54k is within the included 100k) = **$60** | Standard: 60 + 380×0.60 = **$288** (Large would be $500) | Large: 500 + 1,900×0.50 = **$1,450** (Standard: 60 + 80×3 + 2,300×0.6 = $1,680) | Printing is **pushed from the server**, so no browser needs to be open. Runs on Windows, macOS, Linux and Raspberry Pi. Raw ZPL. Per-tenant sub-accounts. | Cost grows with print count. Needs a client on a PC or Pi at each station; it cannot run on iPad or Android. | **9** |
| **QZ Tray** | LGPL and free (community, self-signed). Premium Support $749/yr. Company Branded $3,499/yr [V]. https://qz.io/ | 749/12 = **$62.42** | **$62.42** | **$62.42** (Branded: $291.58) | Flat price. Works with any printer. Raw ZPL. Silent printing. | Printing depends on the browser. Certificate and signing setup. Desktop only. | 8 |
| Zebra Browser Print | Free, obtained through a request form. Windows and macOS (USB and network), Android (Bluetooth) [V]. https://www.zebra.com/us/en/support-downloads/software/printer-software/browser-print.html | $0 | $0 | $0 | Free and official | **Zebra printers only.** Rollo and MUNBYN are excluded. Limited support. | 5 |
| JSPrintManager | Page shows **$24,990** each for the Web App and Web Server licenses, perpetual [V as displayed, looks unusually high; confirm]. https://www.neodynamic.com/products/printing/js-print-manager/buy/ | ~$694/mo over 36 months | same | same | Mature | Very expensive for this use | 2 |
| WebUSB (native) | Free | $0 | $0 | $0 | No agent to install | Chrome/Edge only. On Windows the printer driver must be replaced with WinUSB (Zadig). Fragile. | 4 |

**Recommendation:** PrintNode Integrator. Server-push printing fits an automated pipeline.
**Runner-up:** QZ Tray Premium, which is cheaper at Scale.

---

## 3. Hardware (one-time, paid by the pilot shops; all prices are street estimates [U])

The Zebra reseller pages returned 403 and the Rollo/MUNBYN pages showed no prices.

| Item | Est. price [U] | Notes | Fit |
|---|---|---|---|
| Zebra DS2208 USB kit (2D, corded) | $120–160 | Industry standard. Reads screen barcodes. | 9 |
| Honeywell Voyager 1470g (2D) / 1250g (1D) | $130–160 / $90–110 | Solid | 8 |
| Tera HW0002 / D5100 (2D wireless) | $45–65 | Excellent value. Bluetooth HID works with tablets. | 8 |
| Netum C750 / NT-1228BL | $30–50 | Cheapest option; build quality varies | 6 |
| **Zebra ZD421d 203dpi USB** | $450–550 | Handles 300+ labels a day. Native ZPL. | 9 |
| Rollo X1040 wired / Wireless | $180–200 / $260–280 | Good for small shops; limited ZPL | 6 |
| MUNBYN RW401 / wireless | $100–150 | Cheap; ZPL emulation varies | 6 |
| Samsung Galaxy Tab A9+ / iPad 11" (A16) | $220 / $349 | Tablets for scan stations. Printing goes through a PrintNode host. | 8 |
| Raspberry Pi 5 kit or mini PC (PrintNode host) | $100 / $180 | One per shop | 8 |

**Recommended kit per pilot shop:** 3 ZD421 (~$1,500) + 4 Tera HW0002 (4×55 = $220) + 2 Galaxy Tab A9+ ($440) + 1 Pi ($100) = **about $2,260**.
- For 3 shops that is **about $6,780**.
- A budget kit with MUNBYN printers and Netum scanners comes to about $1,085/shop, or $3,255 for 3 shops.
- Label stock is roughly $0.02–0.03/label [U], borne by the shops.

---

## 4. Transactional email (20k / 150k / 800k per month) and SMS

| Option | Price basis (source) | Pilot 20k | Growth 150k | Scale 800k | Pros | Cons | Fit |
|---|---|---|---|---|---|---|---|
| **AWS SES** | Essentials plan $0.16 per 1k (new 2026 plan structure). Pro $105 minimum. Dedicated IP $15 [V]. https://aws.amazon.com/ses/pricing/ | 20×0.16 = **$3.20** | 150×0.16 = **$24** | 800×0.16 = **$128** | Cheapest | You handle bounces, templates and reputation | **9** |
| Resend | Pro $20 (50k), $35 (100k), overage $0.90 per 1k. Scale $350 (500k), overage $0.70 per 1k [V]. https://resend.com/pricing | **$20** | 35 + 50×0.90 = **$80** | 350 + 300×0.70 = **$560** | Best developer experience, react-email | Expensive at Scale | 8 |
| Postmark (Pro) | 10k $16.50, overage $1.30 per 1k [V]. Higher volume tiers are cheaper [U]. https://postmarkapp.com/pricing | 16.5 + 10×1.3 = **$29.50** | 16.5 + 140×1.3 = **$198.50** | 16.5 + 790×1.3 = **$1,043.50** (upper bound) | Best deliverability | Priciest | 7 |
| Mailgun | Basic $15 (10k, +$1.80 per 1k). Scale $90 (100k, +$1.10 per 1k) [V]. https://www.mailgun.com/pricing/ | 15 + 18 = **$33** | 90 + 50×1.1 = **$145** | 90 + 700×1.1 = **$860** | Mature | Overage-heavy | 6 |
| SendGrid | Page not fetchable. From memory: Essentials $19.95 (50k), Pro $89.95 (100k), about $499 (700k) [U] | ~$20 | ~$140 | ~$580 | Popular | Unverified; support issues | 5 |

**Twilio SMS** ([V] https://www.twilio.com/en-us/sms/pricing/us)
- Rate: $0.0083/segment + about $0.0035–0.0045 carrier fee, so about $0.0123 per SMS.
- Number: $1.15/mo. 10DLC fees are extra [U, about $2/mo campaign fee].
- Assumed SMS volume: 2k / 20k / 100k per month (exception alerts only).
- Pilot: 2,000×0.0123 + 1.15 + ~2 = **~$28**
- Growth: 246 + 3 = **~$249**
- Scale: 1,230 + 3 = **~$1,233**

**Recommendation:** SES. **Runner-up:** Resend, which is worth it for developer speed at Pilot.

---

## 5. SaaS billing (MRR $1k / $7k / $40k; 3 / 20 / 100 invoices a month)

| Option | Price basis (source) | Pilot | Growth | Scale | Pros | Cons | Fit |
|---|---|---|---|---|---|---|---|
| **Stripe Billing + Payments + Tax Basic (API)** | Billing 0.7% pay-as-you-go. Cards 2.9% + 30¢. ACH 0.8%, $5 cap. Tax Basic $0.50 per transaction via API [V]. https://stripe.com/billing/pricing, https://stripe.com/tax/pricing | Cards 29 + 0.90 = 29.90. Billing 7. Tax 1.50. **$38.40** (ACH instead: 8.00 + 7 + 1.5 = $16.50) | 203 + 6 = 209. Billing 49. Tax 10. **$268** (ACH: 56 + 49 + 10 = $115) | 1,160 + 30 = 1,190. Billing 280. Tax 50. **$1,520** (ACH: 300 + 280 + 50 = $630) | Usage-based billing for label fees. ACH wallets for postage. Ecosystem. | You handle sales-tax filing yourself; Tax Complete is $90+/mo | **9** |
| Paddle (merchant of record) | 5% + 50¢ [V]. https://www.paddle.com/pricing | 50 + 1.5 = **$51.50** | 350 + 10 = **$360** | 2,000 + 50 = **$2,050** | Paddle handles all tax | Costly. Poor fit for per-label usage or postage flows. | 6 |
| Lemon Squeezy | 5% + 50¢ plus extras. Moving to "Stripe Managed Payments" in 2026 [V]. https://www.lemonsqueezy.com/pricing | $51.50 | $360 | $2,050 | Merchant of record | Product in transition | 4 |
| Polar (merchant of record) | Starter 5% + 50¢. Pro $20 + 3.8% + 40¢. Growth $100 + 3.6% + 35¢. Scale $400 + 3.4% + 30¢. Payout fee $2 + 0.25% + 25¢ [V]. https://polar.sh/docs/merchant-of-record/fees | Starter 51.50 + payout ~4.6 = **~$56** | Pro 266 + 8 + 20 = 294, + payout ~19 = **~$313** | Growth 1,440 + 35 + 100 = 1,575, + payout ~98 = **~$1,673** | Cheapest merchant of record | Young company | 6 |
| Chargebee Flow | "$0 + 0.80%, includes $66K monthly invoicing volume at no cost", then $99 + 0.65% [V, wording ambiguous]. Plus Stripe processing. https://www.chargebee.com/pricing/ | 29.90 + $0 (or +$8) = **$29.90–37.90** | 209 + 0–56 = **$209–265** | 1,190 + 0–320 = **$1,190–1,510** | Strong billing logic | Adds a second vendor | 6 |
| Orb | Enterprise pricing; site had an expired certificate [U, typically $700+/mo] | n/a | n/a | n/a | Usage billing | Overkill | 2 |
| Lago (open source, self-hosted) | Free + Stripe processing + about $20–40 hosting [U] | 29.90 + 30 = **~$60** | **~$239** | **~$1,220** | No Billing % fee | Ops burden for a solo developer | 5 |

**Recommendation:** Stripe Billing, pushing shops to ACH. US B2B customers do not need a merchant of record.
**Runner-up:** Polar or Paddle, if you want sales tax fully offloaded.

---

## 6. Observability and product analytics

**Assumptions**
- About 10 analytics events per order: 270k / 2.4M / 12M per month.
- Session replays: 1k / 6k / 30k.
- Logs: 5 / 40 / 200 GB.
- Hosts: 2 / 4 / 10.

| Option | Price basis (source) | Pilot | Growth | Scale | Pros | Cons | Fit |
|---|---|---|---|---|---|---|---|
| **Sentry** | Developer free (1 user, 5k errors). Team $26/mo. Business $80/mo (annual) [V]. Overage [U]. https://sentry.io/pricing/ | **$0** | **$26** | ~$80–120 [U] | Best error tracking | Quota management needed | **9** |
| **PostHog** | Free each month: 1M events, 5k replays, 1M flag requests, 100k exceptions, 10GB logs [V]. Per-unit prices (from memory): $0.00005/event for 1–2M, $0.0000343 for 2–15M; replays $0.005 each for 5k–15k, $0.0035 for 15k–50k [U]. https://posthog.com/pricing | **$0** | Events 50 + 1.4M×0.0000343 = 48 → 98? Corrected: 1M×0.00005 = 50, 0.4M×0.0000343 = 13.72, replays 1k×0.005 = 5, **≈ $69** | Events 50 + 10M×0.0000343 = 393. Replays 10k×0.005 + 15k×0.0035 = 102.5. **≈ $496** | Analytics, replay, flags and errors in one tool | Autocapture drives cost up | **9** |
| **Axiom (logs)** | Free: 500GB/mo ingest, 30-day retention. Cloud $25 minimum including 1TB [V]. https://axiom.co/pricing | **$0** | **$0** | **$25** | Huge free tier | Logs only | 9 |
| Better Stack | Free: 10 monitors, 100k exceptions. Telemetry bundles $30–1,750. Responder seat $29 [V]. https://betterstack.com/pricing | $0 | ~$30–60 | ~$105–250 [U] | All-in-one | Bundle pricing is opaque | 7 |
| Grafana Cloud | Free: 10k series, 50GB logs, 50GB traces, 3 users. Pro $19 + logs $0.55/GB [V]. https://grafana.com/pricing/ | $0 | $0 | 19 + 150×0.55 = **~$102** | Generous free tier | Steep learning curve | 7 |
| New Relic | Free: 100GB, 1 full user. $0.40/GB after [V]. https://newrelic.com/pricing | $0 | $0 | 100×0.40 = **$40** | Cheap, full APM | Clunky UI | 7 |
| Datadog | Infra Pro $15/host + APM $31/host. Logs $0.10/GB ingest + $1.70 per million indexed events [V]. https://www.datadoghq.com/pricing/list/ | 2×46 + ~9 = **~$101** | 184 + 72 = **~$256** | 460 + 360 = **~$820** | Best-in-class | Priciest; billing surprises | 4 |
| Highlight → LaunchDarkly | Highlight was acquired and folded into LaunchDarkly [U] | n/a | n/a | n/a | — | Product is being sunset | 2 |
| Plausible (marketing site only) | Starter $9 for 10k pageviews [V, homepage]. 100k tier ~$19 [U] | $9 | $9–19 | $19 | Privacy-friendly | Web analytics only | 6 |

**Recommendation:** Sentry + PostHog + Axiom. That costs **$0 / $95 / ~$621** for the three scenarios.
**Runner-up:** New Relic free tier plus PostHog.

---

## 7. Search and PDF generation

**Assumptions:** records are orders kept 90 days (81k / 720k / 3.6M). Searches: 30k / 200k / 1M per month.

| Option | Price basis (source) | Pilot | Growth | Scale | Fit |
|---|---|---|---|---|---|
| **Postgres full-text search (tsvector + pg_trgm)** | Included in the database | **$0** | **$0** | **$0** (use a GIN index, partition by tenant or month) | **9** |
| Meilisearch Cloud | From $20/mo. Calculator example: 100k docs = $30 usage-based or $23 resource-based [V]. https://www.meilisearch.com/pricing | ~$23–30 | ~$60–120 [U] | ~$250+ [U] | 7 |
| Typesense Cloud | Dedicated clusters from 0.5GB; prices only in the calculator [V]. About $22/mo for the smallest, ×3 for high availability [U]. https://cloud.typesense.org/pricing | ~$22 | ~$60–90 [U] | ~$200–400 [U] | 7 |
| Algolia Grow | 10k searches and 100k records included, then $0.50 per 1k searches and $0.40 per 1k records [V]. https://www.algolia.com/pricing | 20×0.5 = **$10** | 190×0.5 + 620×0.4 = **$343** | 990×0.5 + 3,500×0.4 = **$1,895** | 4 |

**PDF generation**
- Use pdf-lib or PDFKit, or @react-pdf/renderer for packing slips.
- Gotenberg (self-hosted Chromium) or Playwright for HTML-to-PDF.
- Carrier APIs return 4x6 ZPL/PDF labels natively, so labels do not need generating.

**Recommendation:** Postgres full-text search. **Runner-up:** Typesense or Meilisearch, if fuzzy multi-field search becomes necessary.

---

## 8. Customer support and in-app chat (1 seat at Pilot and Growth, 2 at Scale)

| Option | Price basis (source) | 3 customers | 20 customers | 100 customers | Fit |
|---|---|---|---|---|---|
| **Crisp** | Free: 2 seats, chat. Mini $45 (email inbox). Essentials $95 (10 seats, knowledge base, automation). Flat price per workspace [V]. https://crisp.chat/en/pricing/ | **$0** | **$45** | **$95** | **9** |
| Plain | Foundation $35/seat (Slack, email, in-app). 50% startup discount [V]. https://www.plain.com/pricing | $35 | $35 | $70 | 8 (well suited to B2B support over Slack Connect) |
| Chatwoot | Cloud: Hacker free (2 agents, 500 conversations). Startups $19/agent. Self-hosting free + ~$10–20 VPS [V/U]. https://www.chatwoot.com/pricing | $0 | $0–19 | $38 | 7 |
| Intercom | Essential $29/seat + Fin AI $0.99 per outcome. Assumes 5 / 40 / 200 outcomes [V price, U volume]. https://www.intercom.com/pricing | 29 + 5 = **$34** | 29 + 40 = **$69** | 58 + 198 = **$256** | 5 |

**Recommendation:** Crisp. **Runner-up:** Plain.

---

## 9. Uptime, status page and on-call

| Option | Price basis (source) | Pilot | Growth | Scale | Fit |
|---|---|---|---|---|---|
| **Better Stack** | Free: 10 monitors + 1 status page. Responder (phone/SMS on-call) $29/mo annual. +50 monitors for $25 [V]. https://betterstack.com/pricing | $0 ($29 with phone alerts) | **$29** | 29 + 25 = **$54** | **9** |
| UptimeRobot | Free: 50 monitors at 5-minute intervals. Solo $12–13. Team $39–46 [V]. https://uptimerobot.com/pricing/ | $0 | $13 | $46 | 8 |
| Instatus | Free: 15 monitors, 2 on-call members, 200 subscribers. Pro/Business prices not shown [V]; about $20 and $300 [U]. https://instatus.com/pricing | $0 | ~$20 | ~$20–300 | 7 |
| Checkly | Hobby free. Starter $24. Team $64 [V]. https://www.checklyhq.com/pricing/ | $0 | $24 | $64 | 7 (for synthetic checks of the label and print flow) |

**Recommendation:** Better Stack. **Runner-up:** UptimeRobot.

---

## Summary: recommended picks and monthly cost

| Category | Pick | Pilot | Growth | Scale |
|---|---|---|---|---|
| Printing | PrintNode Integrator | 60 | 288 | 1,450 |
| Email | AWS SES | 3.20 | 24 | 128 |
| SMS (optional) | Twilio | 28 | 249 | 1,233 |
| Billing | Stripe Billing + Payments (cards) + Tax Basic | 38.40 | 268 | 1,520 |
| Errors, analytics, logs | Sentry + PostHog + Axiom | 0 | 95 | 621 |
| Search | Postgres full-text search | 0 | 0 | 0 |
| Support | Crisp | 0 | 45 | 95 |
| Uptime / on-call | Better Stack | 0 | 29 | 54 |
| **Stack subtotal** | | **$129.60** | **$998** | **$5,101** |
| As % of MRR | | 13.0% | 14.3% | 12.8% |
| Shipping platform fee (passed through) | EasyPost Forge at $0.08/label [U] | 1,920 | 18,960 | 95,760 |
| Label revenue at $0.15/label | | +4,050 | +36,000 | +180,000 |
| **Net label margin** | | **+$2,130** | **+$17,040** | **+$84,240** |
| One-time hardware (pilot shops) | ZD421 + Tera + Galaxy Tab + Pi | ~$6,780 total | — | — |

**How the subtotals add up**
- Pilot: 60 + 3.2 + 28 + 38.4 = 129.6
- Growth: 288 + 24 + 249 + 268 + 95 + 45 + 29 = 998
- Scale: 1,450 + 128 + 1,233 + 1,520 + 621 + 95 + 54 = 5,101

**Levers to cut cost**
- Push subscription payments to ACH. This saves about $22 / $153 / $890 per month.
- Drop SMS. This saves $28 / $249 / $1,233.
- Switch printing to QZ Tray Premium at a flat $62/mo. This saves $1,388 at Scale.

**Key risks to verify first**
1. EasyPost's per-label fee after 3,000 labels, and Forge contract terms.
2. Whether FlexRate markup forces self-managed billing, and therefore postage collection by ACH.
3. USPS Ground Advantage cubic support on the chosen API.
4. The ShipStation Free plan's suitability for multi-tenant use: sub-account creation is Enterprise-only.
5. The JSPrintManager price as displayed.
6. PostHog per-unit prices and all hardware prices (street estimates).
