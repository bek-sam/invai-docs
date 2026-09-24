# Legal document outlines

Outlines only: headings and what each section must state for InvAI. Fill from verified facts; mark unknowns
`[COUNSEL: …]`.

## Terms of Service (shops as customers)
1. Who we are, who the customer is (the shop's company account), acceptance `[COUNSEL: entity, address]`
2. The service: order hub, gang sheets, floor app, labels, profit, AI listings, vendor portal. "Beta/pilot"
   terms if applicable
3. Accounts and users: owner responsibility for staff, floor PINs and station tokens, vendor users
4. Marketplace connections: the shop authorizes us per channel; the shop stays bound by each marketplace's
   terms; we can't guarantee marketplace uptime or approvals
5. AI features: drafts need the shop's approval; trademark check is a risk score, not legal advice; the shop
   owns its designs and is responsible for rights
6. Labels and postage: carrier charges, refunds and voids follow carrier rules (USPS 30 days, UPS/FedEx 90)
   `[verify EasyPost billing model]`
7. Fees, plans, trials, taxes, per-label fees `[owner-approved prices only]`
8. Acceptable use: no infringing designs, no unlawful content, no reverse engineering, no scraping
9. Data: DPA incorporated; our role as processor for buyer data
10. Suspension and termination; data export window, deletion within 30 days after
11. Warranties disclaimer, liability cap, indemnity `[COUNSEL]`
12. Changes to terms; notice period `[COUNSEL]`
13. Governing law, disputes `[COUNSEL]`

## Privacy policy (our website and app users)
1. Scope: InvAI as controller for account, billing and website data; as processor for buyer data (point to the
   shop's own policy)
2. Data we collect: account (name, email, role), usage and device logs, billing ids (Stripe; no card numbers
   stored), support messages
3. How we use it: provide the service, security, billing, product improvement with aggregated data
   `[no marketplace data for model training]`
4. AI providers: which features send what; PII scrubbed before model calls; zero-retention setting `[verify]`
5. Sharing: sub-processors list link; no sale or sharing for cross-context ads (CCPA)
6. Retention: account data while active + `[period]`; logs ≥ 12 months (security); buyer PII 30 days after
   delivery
7. Security summary (verified controls only)
8. Rights: access, deletion, correction, opt-out; how to ask; clocks (GDPR 1 month, CCPA 45 days)
9. International transfers `[COUNSEL: SCCs]`
10. Cookies and analytics `[list only those actually used]`
11. Children: not for under-16s/13s `[COUNSEL]`
12. Contact, changes, effective date

## Data Processing Agreement (shop = controller, InvAI = processor/service provider)
Must contain the GDPR Art. 28(3) terms:
1. Subject matter, duration, nature and purpose; data categories (buyer name, address, email, phone, order
   details, personalization text); data subjects (the shop's buyers)
2. Processing only on documented instructions
3. Staff confidentiality
4. Art. 32 security measures (annex: verified controls only)
5. Sub-processors: general authorization, notice of changes `[period]`, right to object
6. Help with data-subject requests (Shopify webhooks and DSAR process) and with DPIAs
7. Breach notice to the shop without undue delay, target 24 hours
8. Deletion or return at the end; backup expiry window stated
9. Audits and information
10. International transfers `[COUNSEL]`
CCPA §7051 service-provider terms: specified business purpose; no selling or sharing; no retaining, using or
disclosing outside the direct relationship; no combining with other data; notice if we can no longer comply;
the shop's right to stop unauthorized use.
Annexes: data-flow summary; security measures; sub-processor list.

## Sub-processor list (public page)
| Sub-processor | Purpose | Data categories | Location | Status (in use / planned) | DPA / security report link |
|---|---|---|---|---|---|
| Amazon Web Services | hosting, database, storage, keys | all service data | US `[region]` | | |
| Anthropic | AI listing drafts, trademark judge, assistant | scrubbed text, no buyer PII | US | | |
| EasyPost | rates, labels, tracking | ship-to address, parcel data | US | | |
| Stripe | subscription billing | shop billing contact, payment ids | US | planned (mock today) | |
| Email provider `[name]` | transactional email | recipient email | | | |
| Error / analytics tools `[names]` | monitoring | pseudonymous usage data | | | |
Include "last updated" date and how customers get notice of changes.
