---
name: lifecycle-email-sequence
description: Design and draft an InvAI lifecycle email sequence to shop users - trial onboarding, activation nudges, win-back - with triggers from real product events, exit rules, CAN-SPAM compliant footers and consent, EN/ES copy, and no buyer data. Use for "onboarding emails", "trial emails", "activation", "nudge", "win-back", "drip", "re-engagement".
---

# Lifecycle email sequence

Each sequence is triggered by real product events, stops as soon as the shop succeeds, obeys CAN-SPAM and
consent rules, and is sent only by the owner's tool setup.

## When to use
- Growth-marketer is active, or customer-success needs self-serve onboarding help for small shops (they must
  succeed without a call: `product/scope.md`).
- A trial or plan change is approved by the owner and needs emails.
- Churn-risk reviews or metrics show a drop-off step that an email could fix.

## Where it lives
`invai-docs/growth/email/<sequence>/` (created on first use): `sequence.md` (map, triggers, exits, metrics)
and `emails/<nn>-<slug>.md` (EN and ES copy per email).

## Steps
1. **Know the numbers you may use.** Trial and plans come from `PLAN_CATALOG` in
   `invai-backend/src/modules/billing/service.ts` and only as the owner approved them (`pricing-experiment`).
   Trial length and offers are the owner's call: mark `[owner to confirm]`.
2. **Map activation to real events.** The activation path from [sequences.md](sequences.md): first orders in
   (CSV import or Shopify connect) → SKUs mapped → first gang sheet → first press scan → first label. Each
   trigger names an event the product really records; if the event doesn't exist yet, write "(to be created)"
   and hand it to data-analyst (`define-metric`) and the owning engineer (`instrument-analytics-event`).
3. **Draft the sequence** from [sequences.md](sequences.md): per email the trigger, delay, audience (role:
   owner/admin/office), one goal, subject, preview text, body, one CTA to the exact screen, and the exit rule
   (stop when the step is done, on reply, on unsubscribe, on plan purchase).
4. **Classify each email:** *transactional/relationship* (account, security, billing, the trial's own status)
   or *commercial* (promotes the product, upgrades, win-back). Commercial emails need the full CAN-SPAM set
   below; if an email mixes both, treat it as commercial.
5. **Write copy** in plain language (`write-plain-language-copy`), in shop words, EN and ES. One idea per
   email; show a real screen from the seeded demo, not a mockup. Claims go into the claims register
   (`.claude/skills/landing-page/claims.md`).
6. **Set measures** with data-analyst: open and click only as hints; success is the activation step completed
   within N days of the email. Define the holdout if the owner wants a test
   (`pricing-experiment`/`experiment-readout` style).
7. **Review:** product-manager or customer-success (flow and product fit), **compliance-officer (CAN-SPAM,
   consent, claims)**.
8. **Queue for the owner** with `send-owner-draft`: the sequence, the email tool it needs (a new tool is
   spending → `escalate-to-owner`), sender name and address, the postal address to use, and the unsubscribe
   mechanism.

## CAN-SPAM checklist (every commercial email)
Source: https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business (B2B email is
covered; penalties up to $53,088 per email as stated there on 2026-09-24).
- [ ] "From", "To", "Reply-To" and routing identify InvAI truthfully.
- [ ] Subject line matches the content; no fake "Re:" or urgency that isn't true.
- [ ] Identified as an ad where it is one (clear, not hidden) [COUNSEL: wording for B2B].
- [ ] A valid physical postal address `[owner to confirm]`.
- [ ] A clear, easy unsubscribe that works for at least 30 days after sending, with no login, fee or extra
      info beyond an email address.
- [ ] Opt-outs honored within 10 business days; never sold or shared; suppression list checked before every
      send.
- [ ] If a vendor sends for us, we are still responsible: its settings are in the owner draft.
Also: EU/UK recipients need prior consent for marketing email in most cases [COUNSEL: GDPR/ePrivacy per
country]; track consent at sign-up.

## Rules (MUST / MUST NOT)
- MUST NOT email buyers (a shop's customers), ever, or use buyer data for marketing (growth-marketer role;
  Etsy API Terms forbid emailing Etsy buyers: research 10 §3).
- MUST NOT send, schedule, import contacts or connect an email tool. The owner does.
- MUST stop a sequence when its goal is done; no email tells a shop to do what it already did.
- MUST keep security and billing notices transactional and free of promotion.
- MUST NOT use fake scarcity, fake personal notes ("sent from my iPhone"), or a testimonial without written
  permission (`.claude/skills/landing-page/claims.md`).

## Done when
- `sequence.md` maps every email to a real (or "to be created") event, a delay, an audience, an exit rule and
  a success measure.
- Each email has EN and ES copy, a single CTA to a real screen, and a classification; commercial ones pass the
  CAN-SPAM checklist.
- PM or customer-success and compliance reviews are recorded; an `OI-` draft lists what the owner must set up
  and send.

## References
- [sequences.md](sequences.md): the three sequences, email by email
- `invai-docs/product/scope.md` (segments, trial), `invai-docs/build/demo-guide.md`,
  `invai-docs/research/03-pain-points.md`
- Related playbooks: `landing-page` (claims), `define-metric`, `instrument-analytics-event`,
  `churn-risk-review`, `send-owner-draft`
