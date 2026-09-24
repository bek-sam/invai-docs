---
name: competitive-watch
description: Monthly (or on news) check of InvAI competitors' pricing and features, above all Pythias, MyDesigns, STAHLS' Fulfill Engine and ShipStation, with sourced, dated findings and what they mean for scope and pricing. Use for "competitor", "Pythias", "MyDesigns", "pricing change", "battlecard input" or a monthly watch.
---

# Competitive watch

Once a month the team has a dated, sourced record of what the competitors changed and a short "so what" for
InvAI's scope, pricing and positioning.

## When to use
- First week of each month.
- When the owner, a pilot or the growth-marketer mentions a competitor move.
- Before `pricing-experiment`, and before the growth-marketer writes comparison pages (`seo-comparison-page`).

## Watch list (start from `research/02-competitors.md`; baseline as of Sep 2026)
| Tier | Product | Why we watch | Baseline |
|---|---|---|---|
| Direct | Pythias Technologies | Orders to DTF production, labels, blanks. The most direct threat | $199 (500 orders, 2 channels), $599, $1,499, $3,000; founding cohort of 100 shops; onboarding 1–2 weeks |
| Direct (selling side) | MyDesigns.io | AI listings, mockups and bulk publishing; "Self Fulfillment" is a file download only | $0 / $19.99 / $39.99 / $79.99 |
| Adjacent | STAHLS' Fulfill Engine | Scan-to-print, automated transfer ordering; no Etsy, Amazon, TikTok or Walmart | $500/mo in-house, plus per-item fees |
| Replaced tool | ShipStation (also Veeqo, Pirate Ship) | Labels. Shops hate its price rises | 1,000-label plan $59.99 → $149.99; API $9.95 → $99 |
| Replaced tool | Gang-sheet apps (Build A Gang Sheet, DTF Gang Sheet App, Antigro, CADlink) | Our wedge; could add marketplace intake | $40–799/mo or about $850 license |
| Decorator | Printavo, DecoNetwork, YoPrint, shopVOX, Teesom | Could add marketplace orders | $67–439/mo |

## Steps
1. **Read the last watch** in `invai-docs/product/competitive/` (created on first use) so you only look for
   changes.
2. **Check each tier-1 and tier-2 product** with WebSearch and WebFetch:
   - the pricing page (plans, caps, per-order or per-label fees),
   - the changelog, release notes or blog, and new integrations (Etsy, Amazon, TikTok, Walmart),
   - any AI listing or trademark feature (Pythias) and any production or gang-sheet feature (MyDesigns). These
     two moves would close our gap (concept "Risks").
   - public reviews (Capterra, Trustpilot, Shopify App Store) for new complaint themes.
   Scan tier 3 for big news only.
3. **Record each finding** with the date checked, the source URL and a quote or number. A finding with no
   source is left out. Mark vendor claims as claims.
4. **Rate each change:** `none`, `watch`, or `act`. `act` means it changes our pricing position, removes a
   differentiator (orders → labeled gang sheets, scan-checked floor, true profit, AI listings with a trademark
   check) or opens a gap we can take.
5. **Write the "so what"** for each `act`:
   - scope: is a `scope-change-request` needed?
   - pricing: compare the full monthly bill at 100, 300 and 1,000 orders/day with our plans (`PLAN_CATALOG` in
     `invai-backend/src/modules/billing/service.ts`). Does a `pricing-experiment` follow?
   - positioning: a note for the growth-marketer.
6. **Update the baseline table** at the top of the monthly file so next month starts from facts.
7. **Tell** the PM's own backlog ranking, the growth-marketer (when active) and customer-success (for
   churn-risk talk tracks). If a move threatens a pilot, flag it to the owner with `escalate-to-owner`.

## Output: `invai-docs/product/competitive/YYYY-MM.md`
```
# Competitive watch YYYY-MM (checked YYYY-MM-DD)
## Baseline (updated)
| Product | Plans and prices | Key features | Source |
## Changes this month
| Product | What changed | Source (URL, date) | Rating | So what for InvAI |
## Actions
- SCR / pricing experiment / growth note / owner flag
## Not checked (and why)
```

## Rules
- MUST cite a URL and the date checked for every fact, and mark unverified or vendor-claimed numbers.
- MUST compare total monthly cost (plan plus per-order or per-label fees) at the three shop sizes, not list
  prices alone.
- MUST NOT sign up for trials, contact sales, or create accounts. That is outbound, so it goes to the owner.
- MUST NOT scrape behind logins, or copy competitor text or screenshots into our materials.
- MUST NOT publish claims about competitors. Public comparisons go through the growth-marketer and compliance.

## Done when
- The month's file exists, with an updated baseline, sourced changes, ratings and actions.
- Every `act` has a follow-up: an SCR, a pricing experiment, a growth note or an owner-inbox entry.
- "Not checked" lists any site that couldn't be read.

## References
- `invai-docs/research/02-competitors.md` (full landscape and sources)
- `invai-docs/00-platform-concept.md` ("Competitors and the gap", "Risks")
- Related playbooks: `pricing-experiment`, `scope-change-request`, `seo-comparison-page`, `escalate-to-owner`
