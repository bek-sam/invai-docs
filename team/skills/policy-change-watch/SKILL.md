---
name: policy-change-watch
description: Scheduled check of marketplace, carrier and privacy policy pages that bind InvAI (Etsy, Amazon, Shopify, TikTok Shop, Walmart, USPS, FTC/state privacy) - dated, sourced findings with impact, owner and a proposed backlog row for waves/backlog.md. Use weekly/monthly, or on "policy change", "new rule", "Creativity Standards", "DPP update", "dispatch SLA", "USPS change".
---

# Policy change watch

Every policy change that affects InvAI is caught on a schedule, recorded with its source and date, rated, and
turned into a backlog row or an owner question before its effective date.

## When to use
- On the cadence in [watch-list.md](watch-list.md) (weekly for the fast movers, monthly for the rest).
- When a shop, the owner, a reviewer or news mentions a rule change.
- Before a marketplace application (`marketplace-app-application`) and before a launch (`launch-plan`).

Not for API version deprecations and SDK changes: those are `provider-deprecation-watch` (integrations).
Competitor moves are `competitive-watch`.

## Steps
1. **Read the last watch file** in `invai-docs/compliance/policy-watch/` (created on first use) so you only
   look for what changed.
2. **Check each page due** in [watch-list.md](watch-list.md) with WebFetch (and WebSearch for news of
   changes). Look at the page's "last updated" date, changelogs and announcement posts. If a page returns 403
   or needs JavaScript (etsy.com, partner.tiktokshop.com), try the Wayback snapshot or the official
   forum/changelog, and list it under "Not checked".
3. **Record each change** with: date checked, effective date, source URL, a short quote or number, and whether
   the source is official, `[3P]` or `[U]`. A change with no source is left out.
4. **Rate it:**
   - `none`: wording only.
   - `watch`: may matter later; re-check next cycle.
   - `act`: changes what our code, listings, packets, legal drafts or shops must do. Name the rulebook section
     it changes (`research/10-…` §, `research/12-…` §).
5. **Find the impact and owner** for each `act`: which module or doc (use the ownership table in
   `team/operating-system.md`), which shops (segment, channel), and the deadline (effective date minus build
   and review time).
6. **Turn it into a backlog row.** The backlog `invai-docs/waves/backlog.md` is owned by the tech lead; you
   propose, the tech lead adds, the PM ranks.
   1. Find the next free id: `grep -oE "^\| B-[0-9]+" invai-docs/waves/backlog.md | grep -oE "[0-9]+" | sort -n | tail -1`, add 1. Ids are never reused.
   2. Pick the priority table with the backlog's own definitions: **P0** breaks in production, violates a
      policy or blocks a pilot or approval; **P1** needed before the first paying shop or first real scale;
      **P2** later.
   3. Write the row in the backlog's exact columns, with the source as `PW-YYYY-MM-<n>` (this watch file's
      finding id):
      ```
      | B-40 | Amazon: <what to change>, effective <date> (<URL>) | integrations-engineer | PW-2026-10-1 | open |
      ```
   4. Put the proposed rows in the watch file's "Proposed backlog rows" section and tell the tech lead and PM
      in your report. If an existing row already covers it, name that id instead and add the new deadline.
7. **Update our own docs** you own: packet checklists (`invai-docs/compliance/packets/`), the DPP pack, legal
   drafts. Rulebooks in `research/` aren't yours; list the correction for the tech lead.
8. **Escalate** with `escalate-to-owner` when a change threatens scope, a pilot, an application, or has an
   effective date sooner than a wave can deliver. Shops that must act themselves (for example a new listing
   label) get a draft notice through `send-owner-draft`.

## Output: `invai-docs/compliance/policy-watch/YYYY-MM.md`
```
# Policy watch YYYY-MM (last run YYYY-MM-DD)
## Changes
| Id | Source (URL) | Checked | Effective | What changed (quote/number) | Tag | Rating | Impact and owner | Deadline |
## Proposed backlog rows
| ID | Item | Owner role | Source | Status |
## Owner items
- OI-… (why)
## Not checked (and why)
```
Append new runs to the month's file; keep finding ids stable (`PW-2026-10-1`, `-2`, …).

## Rules (MUST / MUST NOT)
- MUST cite a URL and the date checked for every change, and tag `[3P]`/`[U]` where the official page couldn't
  be read.
- MUST state the effective date and work back to a deadline. A change found after its effective date is
  escalated the same day.
- MUST NOT edit `waves/backlog.md`, `research/**`, code or specs yourself (`respect-ownership`). Propose.
- MUST NOT contact a marketplace, carrier or regulator to ask about a rule. That is outbound: draft it for the
  owner.
- MUST NOT act on rumor alone: seller-forum or blog claims stay `watch` until an official or two independent
  sources agree.

## Done when
- The month's file lists every due page as checked (with date) or under "Not checked" with a reason.
- Every `act` finding has an owner, a deadline and a proposed backlog row or an existing id.
- Owner questions are queued in `owner-inbox.md`, and the report lists the proposed rows for the tech lead.

## References
- [watch-list.md](watch-list.md): pages and cadence
- `invai-docs/research/10-marketplace-engineering-rules.md` (current baseline per channel),
  `12-security-quality-playbook.md` §2
- `invai-docs/waves/backlog.md` (format, priorities), `invai-docs/team/operating-system.md`
- Related playbooks: `provider-deprecation-watch`, `competitive-watch`, `listing-compliance-check`,
  `marketplace-app-application`, `escalate-to-owner`
