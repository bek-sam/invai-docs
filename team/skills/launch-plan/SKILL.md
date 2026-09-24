---
name: launch-plan
description: Plan an InvAI launch (public launch, an app-store listing going live, a new channel or major feature) with go/no-go gates for product, compliance, support and ops, a dated T-minus calendar, owner-sent messages queued as drafts, metrics and a hold/rollback rule. Use for "launch", "go live", "release announcement", "listing goes live", "GTM plan".
---

# Launch plan

A launch happens only when its gates pass, every outbound piece is an owner draft with a date, and the team
knows what it measures and when it stops.

## When to use
- Public launch, or the first app-store listing going live (this also starts the growth-marketer: four weeks
  before).
- A new channel becomes available to shops (for example Etsy API after Commercial Access), or a major feature
  ships.
- Primary author: growth-marketer; product-manager owns scope and the go/no-go; customer-success owns support
  readiness.

## Where it lives
`invai-docs/growth/launches/<YYYY-MM>-<slug>/plan.md` (created on first use), from [template.md](template.md).
`invai-docs/growth/**` is growth-marketer's. When growth-marketer is inactive (PM or customer-success
leading), the tech lead assigns the output path on the card, inside the leading role's owned paths (for
example `invai-docs/product/launches/<YYYY-MM>-<slug>/plan.md` for the PM).

## Steps
1. **Define the launch in one line:** what, for which segment (small self-serve, mid assisted, large
   white-glove), on which channels, target date `[owner to confirm]`.
2. **Tier it:** *Tier 1* public launch or app-store listing (all gates, full calendar); *Tier 2* new channel
   or major feature (product, support, compliance gates, email + release notes); *Tier 3* small feature
   (release notes only: `release-notes`).
3. **List the gates** from [template.md](template.md) and give each an owner and evidence:
   - Product: in `product/scope.md`, `release-checklist` done, `run-golden-path` green, known issues listed.
   - Compliance: the marketplace approval granted (packet status from `marketplace-app-application`), listing
     rules checked (`app-store-listing`, `listing-compliance-check`), legal docs published by the owner
     (`legal-doc-draft`), claims register reviewed.
   - Security and ops: no open High findings (`invai-docs/security/`), SLOs and alerts for the launched path
     (`define-slo`), incident plan in place (B-10), capacity for the expected signups.
   - Support: help articles EN/ES (`write-help-article`), support macros and onboarding checklist
     (`onboard-shop`), who answers what (the owner answers customers).
   - Measurement: events and metrics defined (`define-metric`), dashboard or weekly review ready.
4. **Build the calendar** T-28 to T+30 days: assets (pages, listing, emails, release notes, demo video
   script), reviews, owner drafts, the go/no-go meeting (T-2), launch day, and follow-ups. Every outbound item
   is an `OI-` draft with its send date (`send-owner-draft`).
5. **Set success and stop rules** with data-analyst: 2–4 metrics with targets (activation within the trial,
   first gang sheet within N days, support tickets per new shop, late-shipment rate of new shops). A **hold
   rule**: what pauses signups or the listing (for example a Sev1 incident, a golden-path failure, a
   marketplace warning), and who decides (the owner).
6. **Pre-mortem:** list the 5 likeliest failures (a marketplace review delay, an import format a new shop
   uses, label buy errors, peak-season carrier surcharges, a competitor move from `competitive-watch`) with a
   mitigation each.
7. **Review:** product-manager (scope and go/no-go criteria), customer-success (support readiness),
   compliance-officer (claims, approvals, legal). Then `escalate-to-owner` for the go/no-go and the date.
8. **After launch:** at T+7 and T+30 write a short readout in the plan (metrics vs targets, top issues from
   `invai-docs/customers/`, lessons via `log-lesson`).

## Rules (MUST / MUST NOT)
- MUST NOT launch, publish, post, send, buy ads or change a listing's visibility. The owner does, from the
  queued drafts.
- MUST NOT set a launch date that depends on a marketplace approval not yet granted. Use "approval + N days".
- MUST keep every public claim in the claims register (`.claude/skills/landing-page/claims.md`) and reviewed
  by compliance.
- MUST treat a failed gate as a no-go unless the owner accepts the risk in writing (an `OI-` answer), recorded
  with `record-decision`.
- MUST NOT promise features, dates or prices the owner hasn't approved.

## Done when
- `plan.md` has the one-line definition, tier, every gate with owner and evidence status, the dated calendar,
  metrics with targets, the hold rule and the pre-mortem.
- Every outbound item has an `OI-` draft id and a send date.
- PM, customer-success and compliance reviews are recorded; the go/no-go question is in the owner inbox.
- T+7 and T+30 readouts are scheduled in the calendar.

## References
- [template.md](template.md): plan template with gates and calendar
- `invai-docs/product/scope.md`, `invai-docs/build/demo-guide.md`, `invai-docs/research/02-competitors.md`
- Related playbooks: `release-checklist`, `run-golden-path`, `marketplace-app-application`,
  `app-store-listing`, `landing-page`, `lifecycle-email-sequence`, `release-notes`, `define-metric`,
  `send-owner-draft`, `escalate-to-owner`
