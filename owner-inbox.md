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

## OI-5 (FYI, decided): NUL-byte crash class, handled at the input boundary   status: answered (tech lead)
- From: tech-lead, 2026-09-26. The rule says 2 failed review rounds escalate; this records the decision.
- Context: a raw NUL byte in user text crashes Postgres writes. T-8-2 fixed the AI gateway and the assistant chat. The round-3 review found another path (listing-draft `brief`). Fixing paths one at a time doesn't close the class.
- Decision: T-8-2 is accepted for its scope. A new card, T-8-6, strips NUL (and other characters Postgres rejects) from **every string input** at the API contract boundary, as one shared schema transform, with tests. No action needed from the owner.
- Answer: decided by tech lead (reversible).

## OI-6: Allow spend/risk to explore external market signals for the assistant (Etsy/Amazon trends, competitor prices)?   status: open
- From: product-manager, 2026-09-26. Deadline: before any wave picks this up. Default if no answer: deferred; not built.
- Context: wave 17's assistant spec flagged this as out of scope. It would need either a paid market-data API (unbudgeted recurring cost) or scraping Etsy/Amazon/TikTok/Walmart, which breaks their terms and could jeopardize the pending Etsy Commercial Access and Amazon SP-API applications. No pilot or ticket has asked for it yet (0 shops confirmed; see `product/scope-changes/SCR-001-assistant-external-market-signals.md`).
- Options: A) Defer; revisit only after a live pilot asks for it and a compliant paid data source is priced. B) Approve budget to evaluate a paid, ToS-compliant market-data API now. C) Reject outright.
- Recommendation: A. The risk to pending marketplace approvals outweighs an unconfirmed pain, and we have no pilot evidence yet.
- Cost of waiting: none currently blocked; no wave depends on this.
- Answer:

## OI-7: Approve a scheduled weekly "business review" digest from the assistant (new recurring AI spend + new outbound surface)?   status: open
- From: product-manager, 2026-09-26. Deadline: before any wave picks this up. Default if no answer: deferred; not built. The on-request "weekly business review" starter question ships in wave 17 regardless.
- Context: this is a scheduled, unattended push (email/notification) of the same content the on-request assistant already produces in wave 17. It's a different shape than scope item 13's "read-only tools" (pulled by the owner), adds a new recurring per-tenant AI cost line, and sends AI-generated content to a shop with no human check first. See `product/scope-changes/SCR-002-assistant-weekly-digest.md`.
- Options: A) Defer until pilot usage of the on-request starter question shows real demand. B) Approve as its own spec now, with an eval gate before any unattended send. C) Reject.
- Recommendation: A. Wave 17 already ships the on-request version; let pilot usage prove demand before adding scheduled spend and an unattended-send risk.
- Cost of waiting: none currently blocked; no wave depends on this.
- Answer:
