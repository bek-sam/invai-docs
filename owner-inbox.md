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
