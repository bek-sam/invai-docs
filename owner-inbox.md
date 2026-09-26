# Owner inbox

Questions and approvals that need the human owner. Agents add entries with the `escalate-to-owner` playbook. Drafts of outbound messages are added with `send-owner-draft`. The owner answers under the entry and sets the status.

Always add an entry for:
- deploys, real accounts or keys
- anything sent outside the team
- submissions and signatures
- spending or pricing
- real shop data outside local
- a High security finding or PII incident, immediately, with Amazon's 24-hour clock
- scope beyond the MVP
- reopening a decision
- two failed review rounds
- weakening a control or a test

Entry format:
```
## OI-<n>: <question>   status: open / answered / expired
- From: <role>, <date>. Deadline: <date>. Default if no answer: <what happens>
- Context: <2–4 lines>
- Options: A) … B) … C) …
- Recommendation: <option and why>
- Cost of waiting: <what is blocked>
- Answer:
```

---

## OI-1: Per-label fee and plan prices don't match between code, cost model and concept   status: open
- From: tech-lead, 2026-09-24. Deadline: before the first paying pilot. Default if no answer: the PM runs `pricing-experiment` with the concept's $0.10/label and keeps pilots free.
- Context: `PLAN_CATALOG` in the billing code charges 2–5¢ per label. `calc/cost_model.py` uses $0.15, and the concept recommends $0.10; EasyPost's cost to us is about $0.05–0.08 (unverified). At the code's fees, gross margin is about 3–6%; at $0.10 it's about 60%. The cost model also still counts the cut AI design generation, prices Scale at $1,499 (code: custom), and books revenue for free pilots.
- Options: A) Set the label fee to $0.10 and fix the model. B) Keep the low fee as a growth lever and make margin elsewhere. C) Let the PM test both with pilots first.
- Recommendation: C, with A as the default price in code, because label fees are the main margin line.
- Cost of waiting: pricing, the landing page and the Shopify listing can't be finalized.
- Answer:

## OI-2: Shopify App Store rules clash with Stripe billing and the standalone web app   status: open
- From: compliance-officer research, logged by tech-lead, 2026-09-24. Deadline: before planning the Shopify listing. Default if no answer: no App Store listing; shops connect Shopify through the existing OAuth adapter, and billing stays on Stripe.
- Context: Shopify's app requirements (checked 2026-09-24):
  - Rule 1.2.1: apps listed in the App Store must charge through Shopify's Billing API or App Pricing, not an outside processor.
  - Rules 1.1.1, 2.2.2 and 2.2.3: the app must be embedded in Shopify Admin with App Bridge and session tokens.
  - InvAI bills through Stripe and runs as a standalone web app. It is multi-channel, so Shopify is only one of five sources.
- Options:
  - A) Don't list; connect Shopify directly (unlisted distribution). Confirm with Shopify which distribution model allows this.
  - B) Build a thin embedded Shopify app that bills through Shopify for Shopify-first shops, and keep Stripe for everyone else.
  - C) Move all billing to Shopify (not viable for Etsy- or Amazon-first shops).
- Recommendation: A for pilots, then decide on B after pilots show how many shops are Shopify-first.
- Cost of waiting: the growth-marketer's app-store work and the Shopify part of B-06 can't be finalized.
- Answer:

## OI-3: Build the direct Etsy API adapter now (mock mode) instead of waiting for approval?   status: open
- From: tech-lead, 2026-09-24. Deadline: before wave 4 starts. Default if no answer: stay on CSV import for Etsy (decision 0006); B-108 waits.
- Context: most target shops sell mainly on Etsy. Decision 0006 keeps direct Etsy on CSV until Etsy approves our app. The Etsy Open API v3 (OAuth 2.0 with PKCE, receipts, tracking, ledger entries for fees) can be built and tested in mock mode now, then switched on with your API key. Personal access works on your own shop; other shops need Etsy's commercial-access approval, which can take weeks.
- Options: A) Build it now in mock mode (one wave card, about the size of the Shopify adapter), and you apply for an Etsy developer app in parallel. B) Wait for approval first. C) Keep CSV only, and add the Etsy tracking export file (B-68) as the stopgap.
- Recommendation: A plus C. B-68 helps every CSV channel either way, and the adapter is ready the day Etsy approves.
- Cost of waiting: Etsy shops keep uploading CSVs and typing tracking codes, which is the biggest daily pain for Etsy-first shops.
- Answer:

## OI-4: Download the marketplace tracking-upload templates   status: open
- From: tech-lead, 2026-09-26. Deadline: before the first Etsy, TikTok or Walmart pilot. Default if no answer: we keep our best-source approximations, which may need a fix on first upload.
- Context: T-7-1 builds the tracking export files. Etsy's, TikTok Shop's and Walmart's bulk-upload templates are only downloadable while signed in to a seller account, so our column names come from public docs and aren't verified against the live templates. Amazon's flat file is public and verified.
- Ask: from each seller dashboard, download the blank tracking or shipping-confirmation upload template and put it in `invai-docs/research/templates/`. The team then matches the columns exactly (a small card).
- Answer:
