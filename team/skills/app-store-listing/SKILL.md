---
name: app-store-listing
description: Draft InvAI's Shopify App Store listing (name, icon, introduction, details, features, screenshots, screencast, integrations, pricing section, support and privacy links, test credentials) to Shopify's current listing rules, and later the Walmart, TikTok and Amazon Appstore listings. Use for "App Store listing", "Shopify listing copy", "app screenshots", "listing review rejected".
---

# App store listing

A listing draft that passes the marketplace's listing rules on the first review and says only what InvAI
really does inside that marketplace.

## When to use
- Preparing the Shopify App Store submission (with `marketplace-app-application`, Shopify section).
- A reviewer rejected the listing, or Shopify changed its listing requirements (`policy-change-watch`).
- Later: Walmart Solution Provider marketing page, TikTok App and Service Store, Amazon Selling Partner
  Appstore (same steps, their limits from `.claude/skills/marketplace-app-application/checklists.md`).

## Before writing: two blockers to check
Shopify App Store rules (checked 2026-09-24,
https://shopify.dev/docs/apps/launch/shopify-app-store/app-store-requirements):
- **1.2.1 Billing:** apps that bill off-platform can't be distributed through the App Store; charges go
  through Shopify App Pricing or the Billing API. InvAI bills with Stripe today
  (`src/modules/billing/service.ts`, mocked).
- **2.2.2 / 2.2.3 Embedded:** a consistent embedded experience in Shopify Admin using the latest App Bridge;
  session tokens, no third-party cookies (1.1.1). `invai-web` is a standalone app.
If either is still unresolved (check `invai-docs/decisions/` and the owner inbox), stop and
`escalate-to-owner`: listing copy can't fix them, and they are product and pricing decisions.

## Steps
1. **Re-check the rules live:** WebFetch the requirements page above and
   https://shopify.dev/docs/apps/launch/app-requirements-checklist. Update
   [listing-template.md](listing-template.md) limits if they changed; note the date.
2. **Collect facts:** what the Shopify connection really does today (orders in via the Shopify adapter,
   tracking push, optional stock push: `decisions/0003-stock-push-opt-in.md`), which protected customer data
   fields we request and why, owner-approved prices.
3. **Draft the listing** in `invai-docs/growth/app-stores/shopify/listing.md` (created on first use) from
   [listing-template.md](listing-template.md). Count characters for every limited field:
   `printf '%s' "<text>" | wc -m`.
4. **Screenshots:** 3–6 desktop images at 1600×900 from the running app with seeded demo data (routes in
   `invai-web/src/routes/_app/`). Take them with a one-off Playwright script at that viewport, or
   `.claude/skills/ux-audit/shoot.mjs` and a separate resize step. No pricing, testimonials, statistics,
   outcome guarantees or PII in images; no Shopify logo misuse.
5. **Screencast** script (English, or English subtitles): install → onboarding → orders → gang sheet → floor
   scan → label → tracking back in Shopify. The owner records it (it shows real accounts).
6. **Reviewer materials:** demo store link, test credentials with full access (including any third-party
   account the reviewer needs), steps to test each listed feature. Reuse `reviewer-notes.md` from the packet.
7. **Register claims** (`.claude/skills/landing-page/claims.md`). Shopify listings forbid statistics and
   "first/best/only" in listing content (4.3.3, 4.3.4), even if we could prove them.
8. **Review:** compliance-officer (listing rules and claims) and integrations-engineer (the Shopify facts).
   Then `send-owner-draft` with the fields, assets and what to paste where.

## Rules (MUST / MUST NOT)
- MUST keep every field inside its limit and every rule in [listing-template.md](listing-template.md).
- MUST lead the app name with our brand; no "Shopify" in a way that suggests endorsement; unique and not
  confusable (4.1.2).
- MUST describe only features that work inside the Shopify flow today. CSV-only channels are described as CSV
  imports.
- MUST NOT include pricing in images, testimonials or reviews, statistics, guarantees, or PII anywhere in the
  listing.
- MUST NOT submit the listing, record the screencast with real data, or create the demo store. The owner does.

## Done when
- `listing.md` has every field filled, with character counts inside the limits and the date the rules were
  checked.
- 3–6 screenshots at 1600×900 exist and were checked by eye; the screencast script and reviewer notes are
  written.
- The two blockers are resolved in a decision, or escalated with an `OI-` id.
- Compliance and integrations reviews are recorded, and an `OI-` draft tells the owner what to paste and
  upload.

## References
- [listing-template.md](listing-template.md): fields, limits and prohibited content
- Shopify: https://shopify.dev/docs/apps/launch/shopify-app-store/app-store-requirements ,
  https://shopify.dev/docs/apps/launch/app-requirements-checklist ,
  https://shopify.dev/docs/apps/launch/protected-customer-data
- `invai-docs/research/10-marketplace-engineering-rules.md` §5
- Related playbooks: `marketplace-app-application`, `landing-page`, `send-owner-draft`, `escalate-to-owner`
