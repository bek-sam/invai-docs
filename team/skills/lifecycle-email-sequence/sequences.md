# Lifecycle sequences (starting design)

Delays are from the trigger. Every email: one goal, one CTA to the exact screen, EN + ES, exit rules applied
before each send. Event names are placeholders until data-analyst defines them (`define-metric`); mark missing
ones "(to be created)".

## Activation path (small shop, self-serve)
1. Account created, email verified (email verification is backlog B-09)
2. First orders in: CSV import or Shopify connected
3. SKUs mapped (no orders stuck in "needs mapping")
4. First gang sheet built
5. First press scan on the floor app
6. First label bought
**Activated** = steps 2–6 inside the trial.

## A. Trial onboarding (transactional + light commercial)
| # | Trigger / delay | Goal | Subject idea | Exit |
|---|---|---|---|---|
| A1 | sign-up, 0 min | verify email, start step 2 | "Your InvAI account: first step" | verified + orders in |
| A2 | no orders after 1 day | import today's orders | "Bring in today's Etsy orders (CSV, 2 minutes)" | orders in |
| A3 | orders in, unmapped SKUs after 1 day | map SKUs | "12 orders need a blank: map them once" | no unmapped orders |
| A4 | mapped, no sheet after 1 day | first gang sheet | "Turn today's orders into one gang sheet" | sheet built |
| A5 | sheet built, no floor scan after 2 days | set up a station | "Put the floor app on a tablet at the press" | scan done |
| A6 | trial ends in 3 days `[owner: trial length]` | choose a plan (commercial: full CAN-SPAM) | "Your trial ends <date>" | plan chosen / unsubscribed |

## B. Activation nudges (commercial; weekly cap: 2 emails)
| # | Trigger | Goal | Exit |
|---|---|---|---|
| B1 | activated but profit never opened after 7 days | see true profit | profit page viewed |
| B2 | listings never tried after 14 days | try an AI listing draft with the trademark check | draft created |
| B3 | only 1 user after 14 days | invite office/floor staff | 2+ users |

## C. Win-back (commercial)
| # | Trigger | Goal | Exit |
|---|---|---|---|
| C1 | trial ended without plan, +3 days | ask why (one-question reply) | reply / plan |
| C2 | +14 days | show what changed since (from release notes, `release-notes`) | plan / unsubscribe |
| C3 | cancelled paid plan, +30 days | offer data export reminder and return path; no pressure | plan / unsubscribe |
Stop after C3. Replies go to customer-success's issue log (`invai-docs/customers/`), answered by the owner.

## Email file format (`emails/<nn>-<slug>.md`)
```
# A2 — Bring in today's orders
Type: transactional / commercial.  Audience: owner, admin.  Trigger: … Delay: …  Exit: …
Subject (≤ 50 chars):     Preview (≤ 90 chars):
## EN
<body, ≤ 120 words, one CTA: "Import orders" → /orders>
## ES
<same>
## Footer (commercial): sender, postal address [owner], unsubscribe link, why you got this
Claims: C-…
```
