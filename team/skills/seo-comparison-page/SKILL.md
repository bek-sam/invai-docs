---
name: seo-comparison-page
description: Draft a fair, dated "InvAI vs <competitor>" or "<competitor> alternative" page (Pythias, MyDesigns, ShipStation) where every competitor fact is sourced and dated, re-checked through competitive-watch, and nothing disparages. Use for "comparison page", "vs page", "alternative to Pythias/MyDesigns/ShipStation", "SEO comparison", "battlecard to page".
---

# SEO comparison page

A comparison page that a competitor could read without finding a false or unsourced statement, and a shop
could use to decide.

## When to use
- Growth-marketer is active and the owner wants search traffic from shops evaluating Pythias, MyDesigns or
  ShipStation.
- `competitive-watch` rated a competitor move `act` that changes an existing page.
- Every 30 days for each published page (facts expire).

## Which pages
| Page | Honest angle (research 02, 2026-09) |
|---|---|
| InvAI vs Pythias | Both take marketplace orders to production. Differences to show with sources: plan price and channel limits at 100/300/1,000 orders a day, onboarding time, AI listings and trademark check (Pythias shows none publicly), gang sheets fed by orders |
| InvAI vs MyDesigns | MyDesigns is strong at AI designs, mockups and bulk publishing; its "Self Fulfillment" is a file download. InvAI adds the production side. Say what MyDesigns does better |
| ShipStation alternative for print shops | Labels are one step; InvAI ties labels to the scan at pack and to ship-by. Compare total monthly cost including label fees at three volumes |

## Steps
1. **Run `competitive-watch`** (or read this month's `invai-docs/product/competitive/YYYY-MM.md`) so every
   competitor fact is at most 30 days old. Re-fetch the competitor's own pricing and feature pages yourself on
   the day you write, and save URL + date + quote for each fact.
2. **Build the fact table** first, not the prose, in `invai-docs/growth/pages/vs-<competitor>/facts.md`
   (created on first use): `Row | InvAI (claim id) | Competitor | Competitor source URL | Checked date`. Use
   "not shown on their public site as of <date>" instead of "doesn't have" when you can't prove absence.
3. **Register every claim** (ours and theirs) in `invai-docs/growth/claims.md` per
   `.claude/skills/landing-page/claims.md`. Our capabilities must be seen in the running app, and "integrates
   with" must match what really works today (CSV vs API).
4. **Write the page** with [template.md](template.md): who each tool fits, the table, "where <competitor> is
   stronger", how to switch, FAQ. Put "Last checked: <date>" at the top and sources at the bottom.
5. **Cost comparisons** use full monthly cost (plan + per-order or per-label fees) at 100, 300 and 1,000
   orders a day, with the assumptions shown. Our prices only as the owner approved them.
6. **SEO basics:** one primary query per page ("pythias alternative", "mydesigns vs", "shipstation alternative
   for print shops"), title ≤ 60 chars, meta ≤ 155 chars, H1 matches intent, FAQ answers real questions. No
   keyword stuffing, no competitor trademark in our domain or ad copy [COUNSEL for paid search].
7. **Review:** product-manager (positioning and scope) and **compliance-officer (every claim; comparative
   advertising)**. compliance may ask counsel through the owner.
8. **Queue for the owner** with `send-owner-draft`, including the re-check date. Add the page to the next
   month's `competitive-watch` list.

## Rules (MUST / MUST NOT)
- MUST source and date every competitor fact, and have a reasonable basis for every claim about them before
  publishing (FTC comparative advertising policy, 16 CFR 14.15:
  https://www.ftc.gov/legal-library/browse/statement-policy-regarding-comparative-advertising ;
  substantiation:
  https://www.ftc.gov/legal-library/browse/ftc-policy-statement-regarding-advertising-substantiation).
- MUST NOT disparage: no "clunky", "outdated", "scam", no mocking screenshots, no quoting angry reviews as
  fact, no guessing their roadmap or finances.
- MUST NOT copy competitor text, screenshots or logos. Their name in plain text only, to identify them.
- MUST include where the competitor is better or a better fit. A comparison with no trade-off is an ad, not a
  comparison.
- MUST NOT publish a page whose facts are older than 30 days; unpublishing an outdated page is an owner draft
  too.
- MUST NOT sign up for competitor trials or contact their sales to get facts (outbound: owner only).

## Done when
- `facts.md` has every row with a source URL and a checked date within 30 days.
- The page draft has "Last checked", a trade-offs section, sources, and claim ids for every sentence of fact.
- PM and compliance reviews are recorded, and an `OI-` draft states what to publish and when to re-check.

## References
- [template.md](template.md); `.claude/skills/landing-page/claims.md` (claims register, FTC rules)
- `invai-docs/research/02-competitors.md` (§2 Pythias and MyDesigns, §4 ShipStation, §8 gaps),
  `03-pain-points.md`
- Related playbooks: `competitive-watch`, `landing-page`, `send-owner-draft`
