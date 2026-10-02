---
name: project-help-center-map
description: Where InvAI help center topics map to real screens (esp. "receiving") as of T-21-4
metadata:
  type: project
---

As of T-21-4 (wave 21, 2026-09-28), `invai-docs/help/en/**` and `help/es/**` have 13 articles + an
`index.md` each, covering: getting-started, sku-mapping, gang-sheets-and-vendors,
floor-tablet-setup, receiving, shipping-labels-and-tracking, csv-tracking-export,
profit-and-ad-spend, ai-listings-and-trademark-check, the-assistant, weekly-digest,
team-and-roles, plans-and-billing.

**Why this mapping, not the obvious one:** "Receiving" is not the web `Inventory → Purchase
orders` page alone — `invai-floor/src/i18n/en.ts` has a dedicated **Receiving** floor station
(tabs: Purchase orders, Vendor transfers, Stock count) used by the `receiver` role on a tablet.
That's the richer, more accurate target and what shops actually call "receiving." The web PO page
is cross-linked from `gang-sheets-and-vendors.md` (vendor sheet "Mark received") instead of
duplicated.

**How to apply:** When asked to update or add a help article, check `invai-floor/src/i18n/en.ts`
`station.*` and its named sections (not just `invai-web/src/lib/nav.ts`) before assuming a topic
lives only in the web app — several floor-only flows (receiving, offline outbox, stock count)
have no web-side equivalent screen. None of these articles have screenshots yet (no process was
started per the card's rules) — `![...](../img/<slug>/...)` paths are placeholders for whoever
next has a stack running.
