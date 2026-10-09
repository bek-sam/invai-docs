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

## OI-6: Allow spend/risk to explore external market signals for the assistant (Etsy/Amazon trends, competitor prices)?   status: answered
- From: product-manager, 2026-09-26. Deadline: before any wave picks this up. Default if no answer: deferred; not built.
- Context: wave 17's assistant spec flagged this as out of scope. It would need either a paid market-data API (unbudgeted recurring cost) or scraping Etsy/Amazon/TikTok/Walmart, which breaks their terms and could jeopardize the pending Etsy Commercial Access and Amazon SP-API applications. No pilot or ticket has asked for it yet (0 shops confirmed; see `product/scope-changes/SCR-001-assistant-external-market-signals.md`).
- Options: A) Defer; revisit only after a live pilot asks for it and a compliant paid data source is priced. B) Approve budget to evaluate a paid, ToS-compliant market-data API now. C) Reject outright.
- Recommendation: A. The risk to pending marketplace approvals outweighs an unconfirmed pain, and we have no pilot evidence yet.
- Cost of waiting: none currently blocked; no wave depends on this.
- Answer: (owner, 2026-09-27) Approved, overriding the defer recommendation. The business analytics should use all the data it can to help the shop's business. Build it if it helps the customer's business: research first, write a clear step-by-step market-analysis algorithm, plan, then implement. Guardrails set by the team when recording this: only ToS-compliant sources (official APIs, first-party data, licensed data). No scraping. Every provider gets a mock. Any real paid data subscription or key comes back here before it is bought.

## OI-7: Approve a scheduled weekly "business review" digest from the assistant (new recurring AI spend + new outbound surface)?   status: answered
- From: product-manager, 2026-09-26. Deadline: before any wave picks this up. Default if no answer: deferred; not built. The on-request "weekly business review" starter question ships in wave 17 regardless.
- Context: this is a scheduled, unattended push (email/notification) of the same content the on-request assistant already produces in wave 17. It's a different shape than scope item 13's "read-only tools" (pulled by the owner), adds a new recurring per-tenant AI cost line, and sends AI-generated content to a shop with no human check first. See `product/scope-changes/SCR-002-assistant-weekly-digest.md`.
- Options: A) Defer until pilot usage of the on-request starter question shows real demand. B) Approve as its own spec now, with an eval gate before any unattended send. C) Reject.
- Recommendation: A. Wave 17 already ships the on-request version; let pilot usage prove demand before adding scheduled spend and an unattended-send risk.
- Cost of waiting: none currently blocked; no wave depends on this.
- Answer: (owner, 2026-09-27) Approved: "that's actually a good idea." Research deeply how to implement it, whether better approaches exist, and how the app should do it; then build it. Guardrails set by the team: its own spec, opt-in/opt-out, an eval gate before any unattended send, and a spending cap per tenant.

## OI-8: Run the AI evals once against the real Claude model (needs an Anthropic API key and a small spend)?   status: open
- From: tech-lead, 2026-09-26. Deadline: before a pilot shop uses the assistant or AI listings. Default if no answer: evals stay mock-only; AI quality is unmeasured.
- Context: every eval so far ran on the mock provider (`evals/baseline.json`: `mode: "mock"`, `qualityPass: null`). Wave 17 adds four analyst tools and assistant prompt v4 (analyst mode, Spanish, injection cases). Mock runs prove the plumbing, not the answers. See `waves/17/reports/T-17-2.md` and `T-17-3.md`, "Known gaps".
- Options: A) Provide a key with a spend cap; the ai-engineer runs all four eval sets once (about 80 cases) and reports quality, cost per call and latency. B) Wait until a pilot starts. C) Never; rely on mock evals.
- Recommendation: A. It's a one-time cost of a few dollars at Opus list price, and it's the only way to know whether the assistant's advice is right before a shop sees it.
- Cost of waiting: the assistant and listing drafts could give wrong or badly worded answers to the first real shop, and prompt-injection resistance is untested on a real model.
- Answer:

## OI-9: Apply for the Google Trends API alpha?   status: open
- From: product-manager, 2026-09-27. Deadline: 2026-11-30 17:00 America/Phoenix (so a real trend source could be live before the 2027 Mother's Day season). Default if no answer: don't apply; the market signals keep using the mock Google Trends source, labelled "sample data".
- Context: market signals (scope item 16, `specs/market-signals.md`) use outside search-demand data for trends and seasonality. Google's Trends API is the best official source, but it is an invite-only alpha: someone must apply with a description of the use, and its terms for use in a paid product aren't published (`research/14-market-signals.md` §1.2). Applying is an outside submission, so it's yours. Nothing in wave 18 waits on it.
- Options: A) Apply now, describing InvAI's use (seasonality and trend signals for a shop's own design niches, cached, no resale of raw data); read the alpha terms before any real use. B) Wait until a pilot uses the market tools, then apply. C) Don't use Google Trends; rely on own data and Census.
- Recommendation: B. The tools run on the mock and own data today; apply once a pilot shows the tools are used, so the application can describe real use.
- Cost of waiting: trend and seasonality answers rely on own history and Census only; young shops get "not enough data" more often.
- Answer:

## OI-10: Ask Etsy in writing whether InvAI may show a shop other sellers' public listing prices?   status: open
- From: product-manager, 2026-09-27. Deadline: none fixed; decide before the Etsy Commercial Access application is sent (B-108, OI-3). Default if no answer: don't ask; no Etsy competitor data is used, ever, until Etsy agrees in writing.
- Context: Etsy's API terms restrict using the API for "analytics" and require minimum data; we couldn't read the live text (403). Showing "your price vs similar Etsy listings" would pull other sellers' public listings (`research/14-market-signals.md` §1.1). Asking Etsy is itself a signal in the pending Commercial Access review, so whether and when to ask is your call. Most target shops are Etsy-first, so this is the biggest gap in price position for small shops.
- Options: A) Ask now, in a separate message from the application. B) Ask only after Commercial Access is granted. C) Never ask; Etsy price position stays unavailable.
- Recommendation: B. Don't put the application at risk; ask once approved, with the compliance-officer's draft.
- Cost of waiting: Etsy-only shops get margin-at-price but no price position against the market.
- Answer:

## OI-11: License a paid market-data source (Jungle Scout) for use inside InvAI?   status: open
- From: product-manager, 2026-09-27. Deadline: none fixed; decide after 4 pilot weeks of market-tool use data. Default if no answer: no paid source; the Jungle Scout provider stays a mock.
- Context: Jungle Scout's API gives Amazon keyword search volume ($29–199/month plus usage), but its terms forbid making its data available to third parties without approval, so embedding it for our shops needs a written data licence (`research/14-market-signals.md` §1.3). Keepa is similar (from about €49/month, licence unreadable). It would be new recurring spend.
- Options: A) Ask Jungle Scout for an embedding licence and a price now. B) Decide after pilots show the market tools are used (target ≥ 15% of assistant conversations). C) "Bring your own key": a shop connects its own Jungle Scout account (needs a legal check of their terms).
- Recommendation: B. Demand is unproven (0 shops asked); spend only once use is measured.
- Cost of waiting: Amazon demand signals come from the mock and own data only.
- Answer:

## OI-12: What postal address goes in the footer of InvAI's digest emails?   status: open
- From: product-manager, 2026-09-27. Deadline: before the first real digest email to a pilot shop (wave 19 builds it locally; no real email is sent before this is answered). Default if no answer: digests stay in-app only for pilots; email works locally in Mailpit with a placeholder address.
- Context: the weekly digest (`specs/weekly-digest.md`) emails people who opt in. US law (CAN-SPAM) requires a valid physical postal address in commercial email, and we include one even if the digest counts as account information, because it's cheap insurance (`research/15-weekly-digest.md` §2). We have no address on file.
- Options: A) A business street address. B) A registered PO box or commercial mail-receiving agency address. C) Keep digests in-app only.
- Recommendation: B if you don't want a home or office address public; it's valid under CAN-SPAM.
- Cost of waiting: pilots get the digest in-app only, not by email.
- Answer:

## OI-13: Which email provider and sending domain should digest emails use?   status: open
- From: product-manager, 2026-09-27. Deadline: before the first real digest email to a pilot shop. Default if no answer: no real sending; locally Mailpit, pilots in-app only.
- Context: the digest is a recurring email, the kind people sometimes mark as spam. To protect password-reset and invite emails, digests should go from a separate subdomain or stream (e.g. updates.<our domain> vs accounts.<our domain>) with SPF, DKIM and DMARC set (`research/15-weekly-digest.md` §2, §4.7). This needs a provider account and DNS changes: platform-sre prepares, you approve and create the account.
- Options: A) Amazon SES (already planned for the AWS deploy, B-58) with a separate configuration set and subdomain. B) A dedicated provider (Postmark or Resend) with a separate message stream. C) Delay email until after public launch.
- Recommendation: A, since SES is already in the deploy plan; the separate subdomain keeps account emails safe.
- Cost of waiting: no email digests for pilots; in-app still works.
- Answer:

## OI-14: Have counsel confirm the digest email counts as account information (transactional) under CAN-SPAM?   status: open
- From: product-manager, 2026-09-27. Deadline: before the first real digest email to a pilot shop. Default if no answer: treat it as commercial email anyway (opt-in only, one-click unsubscribe, postal address, no promotions), which the spec already does; send nothing real until OI-12 and OI-13 are answered.
- Context: messages that are only account statements are mostly exempt from CAN-SPAM, but one promotional line can change that; penalties are up to $53,088 per email (`research/15-weekly-digest.md` §2). The spec keeps the digest free of promotions and still follows the commercial rules. The compliance-officer will prepare a one-page note for counsel with the email's content.
- Options: A) Send the compliance-officer's note to counsel before the first pilot email. B) Skip counsel and follow the commercial-email rules (already built). C) Keep email off.
- Recommendation: A. It's a short review, and the answer also covers future product emails.
- Cost of waiting: none for the build; only the first real send waits.
- Answer:

## OI-15: How should the team plant "canary" bugs to measure review quality?   status: open
- From: tech-lead, 2026-09-27. Deadline: before wave 20 planning (about 2026-09-30). Default if no answer: no canaries; review quality is measured only from escaped defects (bugs found after approval).
- Context: the team rules (`team/operating-system.md`, review rules) say the tech lead plants a known bug every few waves to measure the reviewers' catch rate; none has ever been planted. In wave 18 the tech lead asked a builder to commit one hidden defect (to be reverted before any push), and the session's permission system denied it. We didn't try another way.
- Options: A) You allow it explicitly: a canary is committed by the path's owner, recorded in a sealed note outside the repos, and reverted before the gate; B) Canaries only in a throwaway copy of a repo that is never pushed (reviewers review the copy); C) Drop canaries and rely on escaped-defect counts.
- Recommendation: B. It measures the same thing without ever putting a known bug on `main`'s path, so the permission concern goes away.
- Cost of waiting: none for the build; the wave metrics show "canary: not planted".
- Answer:

## OI-16 (FYI, decided): T-18-2 failed its second review round on a new, narrow date bug   status: answered (tech lead)
- From: tech-lead, 2026-09-27. The rule says 2 failed review rounds escalate; this records the decision, like OI-5.
- Context: round 1 of T-18-2 (market data providers) found 3 issues, all fixed in round 2. Round 2's reviewer found one new bug in that fix: in years whose 1 January is Friday to Sunday (2027, 2028) a weekly data date lands a week early, so weekly sources look a week older than they are. Evidence: `waves/18/reviews/T-18-2-reviewer-r2.md`. Mock data only today; no real source is connected.
- Decision: one round 3, limited to this fix plus a round-trip test over 2020–2030; the same reviewer checks it. Anything else found goes to a new card, not another round. No action needed from you.
- Answer: decided by tech lead (reversible).

## OI-17: Which of five proposed scope additions (SCR-003 to SCR-007) do you approve?   status: open
- From: product-manager, 2026-09-28. Deadline: 2026-10-02 18:00 PT (before wave 21 planning). Default if no answer: none approved. Only the four ideas already inside scope (dispatch-scan guard, carrier adjustments in profit, Q4 margin guard, agent-ready listing attributes) go to the normal ranking. No new spend, no new outside accounts, AI design generation stays cut.
- Context:
  - You asked for new ideas; the research is `research/16-growth-opportunities.md`. Top 10 in §0, scores in §6, "don't build" in §7. Proposed backlog rows B-143 to B-161 are not approved.
  - **Your design question:** copying top Etsy sellers' designs must not be built in any form. It means statutory damages up to $150,000 per copied work for the shop, Etsy repeat-infringer bans, liability for us as the tool built for it, and a breach of Etsy's API terms that could cost every shop its Etsy order import (§5.1).
  - The same speed done legally is SCR-007: a niche brief, an original AI design, a similarity and trademark gate, a mockup, a listing draft, a human click, publish. It costs about $0.06–0.20 per design, and it is live in seconds on Shopify, but only after approval on Etsy and in hours to days on Amazon, TikTok and Walmart (§5.2).
  - **Bought designs:** a license bought on Etsy or Creative Fabrica doesn't protect the shop if the file infringes, and the caps (for example 500 or 5,000 units, or "only while subscribed") are real. SCR-003 tracks this (§5.3).
- Options (tick any):
  - A) **SCR-003** design license record: small, no spend.
  - B) **SCR-004** handling-time advisor for Amazon's 2026-06-29 rule: medium, no spend.
  - C) **SCR-005** remake and reship after shipment: medium, no spend, changes the golden path.
  - D) **SCR-006** capacity planner: medium, no spend.
  - E) **SCR-007 phase 1** design risk gate: medium, needs a Google Cloud Vision or TinEye account at a few dollars a month per shop.
  - F) **SCR-007 phase 2** original AI designs: large, needs an image-model API account and about $30–40 a month for a shop making 200 designs, sold as AI credits. Reopens decision 0006.
- Recommendation:
  - A, B and C now. D after B. E with a spend cap you set.
  - F deferred until E is live and one pilot shop agrees to test it on Shopify.
  - This keeps the wedge first and puts the safety gate in place before any generator.
- Cost of waiting: none of the in-scope work is blocked. Amazon's handling-time rule has applied since 2026-06-29 and Q4 starts now, so B loses value each week it waits.
- Answer:

## OI-18: Which gated parts of "analytics v2" do you approve (goals, anomaly alerts, customer analytics, cash view, scheduled report emails)?   status: open
- From: data-analyst, 2026-09-28. Deadline: 2026-10-09 17:00 America/Phoenix (before wave A3 would be planned). Default if no answer: none of the five is built. The in-scope parts (waves A1–A2: profit ladder, losing orders, leakage, shipping margin, why-profit-changed, operations and inventory health, new assistant tools, new digest detectors, Today actions) go to the PM's normal ranking and need no answer here.
- Context:
  - You asked (2026-09-28) for business analytics "to the 100% possible level". The plan is `specs/business-analytics-v2.md`; 20 metric definitions with tested queries are in `metrics/definitions/`. Backlog rows B-168 to B-183.
  - On the demo shop, labels cost about $5 an order more than buyers paid for shipping (about a third of net profit), 3% of orders lose money, and $2,233 of blanks haven't moved. Seed data, mock postage: it shows the kind of answer, not a real shop's number.
  - Five parts go beyond the current scope. Draft request: `metrics/scope-change-draft-analytics-v2.md` (the PM files it). The cash view is the same as the PM's B-152, already listed in OI-17's research.
  - Customer analytics is the only risky one: Amazon buyer data may only be used to ship the order, so Amazon is left out entirely; Etsy's API terms forbid "collecting data for analytics", and counsel should say whether a seller's own repeat-buyer count counts.
- Options (tick any):
  - A) Goals and targets with pace: small, no spend.
  - B) Anomaly alerts on daily numbers (after 8 weeks of history per shop): medium, no spend.
  - C) Customer analytics (repeat buyers, cohorts, lifetime profit, groups): large, no spend; Shopify first, Amazon never, others only after the compliance-officer's review.
  - D) Cash view (with the PM's B-152): medium, no spend; always labelled a projection, not a forecast.
  - E) Monthly report emails to people you name: small; waits for your answers to OI-12, OI-13 and OI-14.
- Recommendation: A, B and D now. C only after the compliance-officer's review, Shopify first. E after OI-12/13/14.
- Cost of waiting: nothing in waves A1–A2 is blocked. Each week without D is a week closer to Q4 blank buying without a cash view.
- Answer:

## OI-19: Engage counsel to review the terms, privacy policy, DPA and sub-processor list drafts?   status: open
- From: compliance-officer, 2026-09-28. Deadline: 2026-10-12 17:00 America/Phoenix. Default if no answer: drafts stay unreviewed and unpublished; every in-app legal page keeps its "Draft, pending legal review" banner (wave 21 fence).
- Context:
  - First drafts of the four documents are ready for counsel at `invai-docs/legal/{terms,privacy,dpa,subprocessors}.md`, each with a complete Spanish translation in `invai-docs/legal/es/`. Every document opens "DRAFT for counsel review. Not in force." and marks every value only counsel or the owner can supply (company legal name, address, governing law, prices, liability cap, notice periods) as `[[OWNER: ...]]` or `[COUNSEL: ...]` — nothing is invented.
  - Every data-handling claim in the privacy policy and DPA is backed by a file:line citation checked against the running code today (30-day buyer PII purge, 18-month non-PII redaction sweep, field-level AES-256-GCM encryption, RLS, PII stripped before any AI call, Shopify's three GDPR compliance webhooks already built, tenant export/deletion within 30 days). See `invai-docs/waves/21/reports/T-21-1.md` for the full evidence table.
  - Real gaps are stated as gaps, not glossed over: no MFA on PII-access accounts, no centralized 12-month security log, the AWS KMS key is provisioned but unused, no chosen email provider (blocks OI-13), no RDS backup-retention figure confirmed, no error-tracking/analytics vendor in the code.
  - This does not ask you to publish or sign anything — only whether to spend money having a lawyer review these drafts, and when.
  - Added by the tech lead, 2026-10-09 (wave 28): when counsel is engaged, also have them check the keep list of `decisions/0026-amazon-non-pii-retention.md` (item titles, refund and staff notes, tracking numbers kept past 18 months as bookkeeping records). Same question, no new decision needed now.
- Options: A) Engage counsel now, in parallel with closing the remaining DPP/security gaps, so the documents are ready the moment a real sub-processor (Stripe, a chosen email provider) or a live marketplace approval lands. B) Wait until the DPP evidence pack and the open OI-13 (email provider) are closed, so counsel reviews a more finished picture in one pass. C) Hold until a paying shop is imminent.
- Recommendation: B — the drafts are complete and internally consistent today, but §7 (fees), the email sub-processor and several security controls are still open; one counsel pass after those close avoids a second billed review for the same document.
- Cost of waiting: no shop-facing legal page can leave its "Draft, pending legal review" banner (wave 21 fence) and no DPA can be offered to a real customer until this is answered and acted on; this does not block any other wave-21 or wave-22 work.
- Answer:

## OI-20: The Mac's disk is nearly full (3.8 GB free); may the team clear Docker's build cache, or will you free space?   status: open
- From: tech-lead, 2026-09-28. Deadline: 2026-09-29 12:00 America/Phoenix. Default if no answer: the team deletes nothing outside InvAI; it drops its own test databases, runs one agent at a time for heavy checks, and pauses a gate if free space drops below 2 GB.
- Context: during wave 20 the data volume hit 100% and Docker (Postgres, Valkey, MinIO) stopped mid-run; it came back after a restart. `docker system df`: images 17.6 GB (13.7 GB unused, mostly other projects: Supabase and "wardrobe" images), build cache 3.2 GB (unused). InvAI's own data volumes are about 7.4 GB and must stay.
- Options: A) the team runs `docker builder prune` (build cache only, 3.2 GB, rebuilt on demand); B) you remove the unused Supabase/wardrobe images yourself (about 13 GB), or other files; C) both.
- Recommendation: C. The build cache is safe to clear; other projects' images are yours to judge.
- Cost of waiting: gates need about 2 GB of scratch space; another full disk stops every agent and Docker again.
- Answer:

## OI-21: How should CI read the other private InvAI repos for the E2E job?   status: open
- From: tech-lead, 2026-09-29. Deadline: 2026-10-06 18:00 CDT. Default if no answer: the E2E workflows stay manual-only (`workflow_dispatch`) and the regular CI keeps using today's two read-only deploy keys.
- Context: T-23-7 adds an end-to-end CI job in backend, web and floor that checks out the sibling repos. All 8 repos are private. Today only `CONTRACTS_DEPLOY_KEY` and `UI_DEPLOY_KEY` exist, so the E2E job can't check out backend, imaging, web, floor or infra. The security review (`waves/23/reviews/T-23-7-security-reviewer-r1.md`) advises against adding more per-repo SSH keys. Setting a secret is yours: agents can't and won't.
- Options: A) A GitHub App on the 8 repos with Contents: Read only; CI mints short-lived tokens (`actions/create-github-app-token`), and you add its app id and private key as org/repo secrets. B) One fine-grained personal access token, read-only on these repos, with a 90-day expiry, stored as a secret. C) Keep E2E manual-only and rely on the local `pnpm gate` before each push.
- Recommendation: A. It has one place to revoke access, short-lived tokens and read-only scope. B is acceptable if you want it done in 5 minutes.
- Cost of waiting: E2E doesn't run automatically on push. The local pre-push gate (T-23-6) still runs it before every push, so no untested code is pushed.
- Answer:

## OI-22: May T-23-6 (pre-push gate) have a third review round to redesign its push check?   status: answered
- From: tech-lead, 2026-09-29. Deadline: 2026-10-01 12:00 CDT. Default if no answer: T-23-6 stays unpushed; the live push check stays as it is (it over-blocks one push form and misses two path forms, and is no weaker than before it existed); pushes keep following the integration-gate rule.
- Context: The team rule sends a card to you after two failed review rounds. All 5 round-1 findings are fixed. Round 2 (`waves/23/reviews/T-23-6-reviewer-r2.md`) found 2 more, both in the push check: (1) a push with a `2>&1` redirect is wrongly refused even with a valid pass, and (2) paths written with `~` or `{}` aren't checked at all. The security review (`T-23-6-security-reviewer-r1.md`, S-42 Medium) found a third: a push wrapped in `$(...)` skips the check. All three are in the same guesswork about which folder a command runs in; no existing guard is weakened.
- Options: A) Allow round 3 as a simpler redesign: the hook accepts a push of a code repo only in one exact form (`git -C /abs/path/<repo> push origin <ref>`, alone in its command) and refuses every other form, so there's no folder guessing. Same reviewer plus security. B) Accept as is and log both as known gaps (the stamp is a speed bump, not a security boundary). C) Drop the push block and keep only the `pnpm gate` script.
- Recommendation: A. Point patches found three new holes in two rounds; one allowed form is simpler to prove. About an hour of work.
- Cost of waiting: none for product work; only the automatic push check waits.
- Answer: (owner, in chat, 2026-10-01) A: approve the recommended redesign. The push check allows exactly one push form. Also: push `invai-infra`'s held commits once they're fixed. Runs as wave P8 card T-23-6 r3 (`waves/P8/wave.md`).

## OI-23: May T-P7-4 (guard hook gaps) have a third review round to fix one regression?   status: answered
- From: tech-lead, 2026-10-01. Deadline: 2026-10-03 12:00 CDT. Default if no answer: the live guard stays as installed after round 2 (stricter, not weaker; it also refuses some harmless commands, see below); T-P7-4 stays unapproved; nothing else changes.
- Context: Two review rounds by the security-reviewer, each with one blocking finding; the primary reviewer approved. Round 1's gap (full-URL `gh api` writes) is closed. Round 2 added a regression: a command that only writes a shell script through a redirect is refused as "written then run", and so is a heredoc that merely quotes such a command (it refused the tech lead's own inbox append). Agents can still write files with the Write and Edit tools. Evidence: `waves/P7/reviews/T-P7-4-security-reviewer-r2.md`, `T-P7-4-reviewer-r1.md`, report `waves/P7/reports/T-P7-4.md`.
- Options: A) Round 3 limited to that one fix (skip the word after a redirect when looking for a script to read) plus allow tests for the six forms the reviewer listed, reviewed by the security-reviewer. B) Roll the guard back to its pre-P7 copy (`invai-docs` history) and drop T-P7-4. C) Keep it as it is.
- Recommendation: A. The fix is one condition with tests already named by the reviewer; about 30 minutes. Everything else in T-P7-4 (secret and repo-setting blocks, scripts read before running, shell edits counted) passed both reviewers.
- Cost of waiting: none for product work; some shell commands that write scripts or quote them are refused, and agents use the Write tool instead.
- Answer: (owner, in chat, 2026-10-01) A: approve round 3, limited to the one over-strict rule that refuses harmless shell commands which create a script file. Runs as wave P8 card T-P7-4 r3 (`waves/P8/wave.md`).

## OI-24: May T-23-6 (push check) have a fourth round to close one hole the round-3 redesign left in the docs push?   status: answered
- From: tech-lead, 2026-10-01. Deadline: 2026-10-03 12:00 CDT. Default if no answer: T-23-6 stays unapproved; `invai-infra`'s held commits (including the approved S-45 fix) stay unpushed; the installed guard stays as it is (it already refuses every code-repo push form but one).
- Context: Round 3 (wave P8 card T-P8-3) did what you approved: code repos can be pushed in exactly one form, with a fresh gate pass. Both reviewers confirmed that part (110 hook tests pass; 110+ bypass forms refused). Both found the same new hole independently: the docs folder's push is allowed without a gate pass, and the check doesn't look at where that push goes, so a push started from the docs folder can be aimed at a code repo (`waves/23/reviews/T-23-6-reviewer-r3.md`, `T-23-6-security-reviewer-r2.md`, S-47 Medium). The fix is one rule: a docs push must be exactly `push origin main` (or `<sha>:main`), plus refusal tests.
- Options: A) Round 4 limited to that one rule, same two reviewers. B) Accept as is and log S-47 as a known gap. C) Stop here and keep the infra commits unpushed.
- Recommendation: A. It is a one-line rule the README already promises; about 20 minutes, and it unblocks the infra push you asked for.
- Cost of waiting: the S-45 fix and the gate script stay unpushed; no product work is blocked.
- Answer: (owner, via the coordinator, 2026-10-02) A: round 4 limited to S-47 (a docs push must be exactly `push origin main` or `<sha>:main`, with refusal tests), same two reviewers. Runs in wave P8 (`waves/P8/wave.md`).


## OI-25: Turn on real AI photo generation (OpenAI GPT Image) for lifestyle listing photos?   status: open
- From: tech-lead, 2026-10-02. Deadline: none (nothing waits on it). Default if no answer: lifestyle scenes keep using the built-in sample generator (free, clearly labelled "sample"); template photo sets (phase A) work fully without it.
- Context: you approved AI listing photos on 2026-10-02 (SCR-008, waves 26 and 27). Phase B can send a blank garment picture (never your design, never buyer data) to OpenAI's image API to draw a scene; InvAI then pastes your real design on and rejects any picture where the design changed. The team built it but may not switch on paid calls. It turns on only when `IMAGE_GEN_PROVIDER=openai` is set next to your `OPENAI_API_KEY` in `invai-backend/.env` (runbook "AI photos"). Limits already enforced before every call: 30 AI images per shop per day (`IMAGE_GEN_DAILY_CAP_PER_SHOP`), the platform daily AI spend cap, and credits (10 credits per AI scene image, 1 per template image; these credit prices are a starting point and yours to change).
- Cost estimate: the first estimate (research 16 §5.2) was $0.02–0.06 per image. **Updated 2026-10-03** from OpenAI's pricing page as checked by the builder (`waves/27/reports/T-27-1.md`): the provider uses `gpt-image-2` at medium quality, about $0.10–0.11 per image (a cheaper model with only per-token prices is a later upgrade). So about $0.60–0.66 per 6-image lifestyle set, and at most about $3.30/day for one shop at the 30/day cap.
- Options: A) Enable on your dev machine only, try a few sets, then decide for pilots. B) Enable for pilots with the 30/day cap. C) Keep the sample generator until a pilot asks.
- Recommendation: A. It costs cents, and it is the only way to judge real quality and drift-rejection rates before any shop sees it.
- Cost of waiting: none for phase A; lifestyle scenes stay sample pictures.
- Answer:

## OI-26: When the Shopify app is registered, include the new `write_products` permission (shops reconnect once)?   status: open
- From: tech-lead, 2026-10-03. Deadline: none (no Shopify app or keys exist yet). Default if no answer: the permission stays in the app config in the repo; nothing is sent to Shopify; pushing photos to Shopify works only on the mock.
- Context: wave 27 (T-27-4, backend 3f4deae) lets a shop push approved listing photos to a Shopify product. That needs Shopify's `write_products` permission, now added to `invai-backend/shopify.app.toml` and the requested scopes. Shops that connected before it see "reconnect needed" until they reconnect and approve. Registering or updating the app with Shopify is yours (OI-2 covers the wider Shopify App Store questions).
- Options: A) Keep `write_products` in the config you register. B) Remove photo push from Shopify and use the zip download only. C) Decide later with OI-2.
- Recommendation: A. It is the only way photos reach Shopify automatically, and one reconnect per shop is small; the zip stays as the fallback.
- Cost of waiting: none until the Shopify app is registered.
- Answer:

## OI-27: May listing photos use real photographs of blank garments as bases, not only code-drawn shirts (amend decision 0022 §3)?   status: open
- From: product-manager (research), 2026-10-03. Deadline: 2026-10-17 18:00 CDT. Default if no answer: bases stay code-drawn only; photos keep looking illustrated, and Amazon's adult-apparel main image (a real standing model) stays impossible.
- Context: research (`research/18-listing-images-and-gang-sheets.md`, "Three structural causes" and "Real photographs as bases") found our photos look fake because every shirt is drawn with code. Decision 0022 §3 says bases are "drawn by code, never downloaded stock art". The fix keeps the design lock exactly as is: your design is still pasted on by InvAI's own code and never touched by a model. Only the shirt underneath changes, from a drawing to a real photo (house shoot, a shop's own shoot, or licensed stock). `photos.py compose()` already does the pasting; only its source changes. The architect would also amend ADR 0023 §2 (the restore-blank-color step).
- Options: A) Allow real photo bases of all three kinds (house shoot, shop's own, licensed stock). B) Allow house and shop shoots only, no stock. C) Keep code-drawn bases only.
- Recommendation: A, with licensed stock used only if the compliance officer confirms the license allows reuse across many shops. It is the single change that makes photos look real, and design fidelity is unchanged.
- Cost of waiting: blocks wave IMG1 (photo-base library); every listing set made meanwhile looks illustrated.
- Answer:

## OI-28: Fund a one-time house photoshoot of top blank garments (about $500–2,000 per half day) for the shared photo library?   status: open
- From: product-manager (research), 2026-10-03. Deadline: 2026-10-24 18:00 CDT. Default if no answer: no shoot and no stock purchase; nothing is spent; the library starts with drawn bases (or AI bases if OI-29 is approved).
- Context: depends on OI-27. The report's recommended library is real photos for main images (Comfort Colors 1717, Bella+Canvas 3001, Gildan 5000 tees, hoodies and sweatshirts; flat, folded, standing model front and back, close-up; top 6–8 colors each, other colors recolored with a color-accuracy check) plus AI-made bases for secondary lifestyle slots. Real photos need no Etsy AI disclosure and are the safest Amazon/Walmart main image. A shoot needs model releases. Prices are from a vendor survey (Photoroom 2026), not quotes. Follow-up research 19 (`research/19-custom-photo-mockup-tools.md`) found no external mockup API fit to render per image (cost about $310/month for a mid shop, design files leave InvAI, Dynamic Mockups' general terms forbid commercial use); it suggests a free test with one real photo and pilot shops' own photos first, then about 35 studio photos (about $1,300–1,900 at $39/photo) once a model release covering all shops is ready.
- Options: A) Fund a half-day house shoot (get 2–3 quotes first). B) Buy licensed stock mockup photos instead (only if the license allows multi-shop SaaS use). C) No shoot; use AI-made bases only, with disclosure on every image.
- Recommendation: A. A few hundred to two thousand dollars once, shared by every shop, gives the most realistic and lowest-risk main images.
- Cost of waiting: main images stay illustrated or AI-disclosed; no money spent while waiting.
- Answer:

## OI-29: Use the real AI image provider to build the shared lifestyle base library once (about $50–110), and to sell per-design AI scenes as a paid extra?   status: open
- From: product-manager (research), 2026-10-03. Deadline: 2026-10-24 18:00 CDT. Default if no answer: mock scenes stay; no provider calls; no money spent.
- Context: builds on OI-25 (which asks only whether to turn the provider on, starting with a dev trial). The research found that paying per design is the expensive path: about $3.30–7.20 per design when every image is AI, vs $0.20–0.39 for the hybrid. The cheaper plan: InvAI calls the provider once per base (model, scene) at library-build time, every design reuses those bases, and disclosure is tracked per image by the base's origin. Per-design AI scenes remain a paid extra. Your design is never sent to the provider.
- Options: A) After the OI-25 dev trial, build the library once and offer per-design scenes as a paid extra. B) Build the library only; no per-design scenes. C) Keep mock scenes.
- Recommendation: A, after answering OI-25 with option A. One-time cost about $50–110; per-design scenes are paid for by credits (see OI-30).
- Cost of waiting: lifestyle slots stay sample pictures.
- Answer:

## OI-30: Change photo credit prices to: free previews, 3 credits per approved library set, 15 credits per AI scene, with credit packs at about $0.02 per credit?   status: open
- From: product-manager (research), 2026-10-03. Deadline: 2026-10-31 18:00 CDT. Default if no answer: today's prices stay (1 credit per template image, 10 per AI scene); credit-pack price stays unset.
- Context: research 18, section "Credits and gross margin". At today's prices a hybrid design in 3 colors uses about 32 credits, so a starter shop ($149, 500 credits) gets about 15 designs a month, which pushes shops away from the cheap, realistic path. Proposed margins at $0.02/credit: library set about 80%, AI scene 52–78%, opt-in upscale about 88%. Worst case: a pro shop spending all 6,000 credits on AI scenes costs about $57 (8% of $699). The bigger risk is text AI at 1 credit per 1,000 tokens, which can sell near cost on the top model; the monthly cost review should check it. These are estimates, not measured costs.
- Options: A) Adopt the proposed prices. B) Adopt them, but keep AI scenes at 10 credits on a cheaper model (about $0.05 or less per image). C) Keep today's prices.
- Recommendation: A, and re-check margins after the first month of real usage (data-analyst cost review).
- Cost of waiting: none until real photo bases exist (IMG1); after that, shops pay too much for the cheapest path.
- Answer:

## OI-31: Allow opt-in AI upscaling of low-resolution print files (an exception to "models never change design pixels")?   status: open
- From: product-manager (research), 2026-10-03. Deadline: 2026-11-07 18:00 CDT. Default if no answer: no upscaler; low-DPI files are only flagged and held, as today.
- Context: research 18, section "Gang sheets need better file checks". Low-res art is a top DTF complaint; paid tools (DTFWiz and others) upscale 4x with Real-ESRGAN for about $0.005 per file. An upscaler invents pixels in the design, which the principle behind decision 0022 forbids (0022 itself covers photos, not print files). Proposed guard: opt-in per file, before/after shown, original kept, the shop's approval recorded, always the "approve" autonomy level, and 2 credits per upscale. The other file checks (thin lines, small text, white boxes, color profile) are plain code and need no decision.
- Options: A) Allow opt-in upscaling with those guards. B) Allow it only for shops that turn it on in settings. C) No upscaling.
- Recommendation: A. It rescues orders that would otherwise print badly or wait on the buyer, and the shop always sees and approves the result.
- Cost of waiting: low-res orders stay held for manual fixing.
- Answer:

## OI-32: Add listing video to scope, starting with a simple non-AI slideshow made from the listing photos?   status: open
- From: product-manager (research), 2026-10-03. Deadline: 2026-11-07 18:00 CDT. Default if no answer: no video is built; listings use photos only.
- Context: video is out of scope today. Etsy allows 1 clip (5–15 s), and secondary sources cite Etsy saying listings with video are "40% more likely" to sell; TikTok Shop strongly favors 9:16 video. A slideshow (pan and carousel of the listing photos) costs almost nothing to render. AI video (Veo 3 Fast about $0.10/s, Kling about $0.14/s) would be about $0.80–1.12 per 8 s clip and would need its own scope change request, AI disclosure, and a price (proposed 150 credits).
- Options: A) Add the non-AI slideshow now; AI video only via a later scope change request. B) Add both slideshow and AI video. C) No video.
- Recommendation: A. Cheap, no disclosure needed, covers Etsy and TikTok; AI video can follow if shops ask.
- Cost of waiting: listings go without video.
- Answer:
