---
name: landing-page
description: Draft an InvAI marketing page (home, pricing, feature or segment page) as copy plus a layout spec, with every claim in the claims register, screenshots from the running app, EN/ES text and a 1440/390 px check, queued for the owner to publish. Use for "landing page", "homepage", "pricing page", "feature page", "website copy", "hero".
---

# Landing page

A page draft where every sentence is true, sourced and in shop words, with real product screenshots, ready for
the owner to publish.

## When to use
- Growth-marketer is active (four weeks before public launch or the first app-store listing; before that the
  tech lead does not assign it).
- A new feature ships that changes the pitch, or pricing is approved by the owner.
- A marketplace application needs a public website (Amazon requires one: `marketplace-app-application`).

## Where it lives
- Draft: `invai-docs/growth/pages/<slug>/page.md` (copy + layout spec) and `shots/` (created on first use).
- The site itself will live in the `invai-site` repo (to be created; growth-marketer owns it). Until it
  exists, the draft is the deliverable. Building the site from the draft is a separate card.

## Steps
1. **Read** `product/scope.md` (segments, MVP in/out, pricing hypothesis), `research/02-competitors.md` §8
   (gaps), `research/03-pain-points.md` (pains in shop words), `00-platform-concept.md`,
   `build/demo-guide.md`, and the growth-marketer role file "Positioning".
2. **Pick one segment and one job** per page (small shop self-serve, or mid shop assisted). Name the pain in
   the shop's words: late-shipment penalties, IP takedowns, order chaos, wrong presses, film waste, unknown
   profit.
3. **Write the structure** from [template.md](template.md): hero, problem, how it works (orders → gang sheet →
   floor scan → label → profit), proof, channels, pricing or CTA, FAQ, footer (legal links, Etsy notice if
   Etsy is named).
4. **Register every claim** in `invai-docs/growth/claims.md` using [claims.md](claims.md). Capabilities must
   be seen in the running app (`CLAUDE.md` "Demo data"); competitor facts come from `competitive-watch` and
   are dated; numbers come from data-analyst with a definition. No row, no sentence.
5. **Take screenshots from the real product** with seeded demo data: `cd invai-web && node
   ../.claude/skills/ux-audit/shoot.mjs ../invai-docs/growth/pages/<slug>/shots owner@desertbloom.test en /
   /orders /production/sheets /analytics/profit /listings/drafts` (routes live in
   `invai-web/src/routes/_app/`; `es` for Spanish). Look at each: demo names only, no "mock" badges, no
   secrets.
6. **Write plain copy** (`write-plain-language-copy`), then the Spanish version if the page targets
   Spanish-speaking owners (spec it; docs-writer or a reviewer checks the translation).
7. **Check the layout spec at 1440 px and 390 px** (headline length, CTA visible without scrolling on a phone,
   table of channels readable). For a built page, run `ux-audit` on it.
8. **Review:** product-designer (page and layout) or product-manager (positioning and scope), **plus
   compliance-officer for every claim and legal link** (operating-system "Who reviews whom").
9. **Queue for the owner** with `send-owner-draft`: what to publish, where (domain/path), when, and the claims
   list. Pricing sections need the owner's approved numbers in the entry.

## Rules (MUST / MUST NOT)
- MUST follow [claims.md](claims.md): evidence first, no fake reviews, testimonials, logos or numbers; pilot
  quotes only with written permission obtained by the owner.
- MUST describe only what is in the MVP and works today. Deferred items (direct Amazon, Etsy, TikTok, Walmart
  APIs; AI design generation) are not promised. "Coming soon" only with the owner's approval.
- MUST show prices only as the owner approved them.
- MUST NOT publish, deploy, buy a domain or tool, or start ads. The owner does (`send-owner-draft`,
  `escalate-to-owner`).
- MUST NOT add tracking scripts or forms that collect personal data without a privacy policy link and the
  owner's approval (and nothing that affects PCI SAQ A eligibility on billing pages: research 12 §2.5).

## Done when
- `page.md` has every section, every claim tagged with a register id, and EN (and ES where planned) copy.
- Screenshots come from the running app with demo data and were checked by eye.
- The layout was checked at 1440 and 390 px.
- Reviews are recorded (designer or PM, plus compliance), and an `OI-` draft says what to publish, where and
  when.

## References
- [template.md](template.md): page structure; [claims.md](claims.md): claims register and FTC rules
- growth-marketer role file (`.claude/agents/growth-marketer.md`); `invai-docs/research/02-competitors.md`,
  `03-pain-points.md`
- Related playbooks: `seo-comparison-page`, `app-store-listing`, `launch-plan`, `competitive-watch`,
  `ux-audit`, `send-owner-draft`
