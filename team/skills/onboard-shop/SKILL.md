---
name: onboard-shop
description: Onboard a DTF shop onto InvAI at the right service level (self-serve for small shops, assisted for mid-size, white-glove for large or multi-location), from profile and dry-run import to go-live with a rollback plan. Use when a pilot or new shop signs on, shares files, or is stuck in setup.
---

# Onboard a shop

Each shop runs its own real day of orders through InvAI (import → SKU map → gang sheet → press → label) at the
service level that fits its size, with a written, repeatable setup and a same-day way back.

## When to use
- The owner says a pilot or new shop is starting, or a shop sends its files.
- A self-serve shop stalls on the **Today** onboarding checklist.
- A shop adds a location, a channel or a vendor (re-run the matching steps).

## Pick the level (segments from `invai-docs/product/scope.md`)
| Level | Shop | Who does the work | Target time to first real sheet |
|---|---|---|---|
| **Self-serve** | Small: 1–3 people, under 100 orders/day, often Etsy-first | The shop alone, with help articles | Same day |
| **Assisted** | Mid: 5–30 staff, 100–1,000/day, several marketplaces | The shop, on a call the owner runs, with a pack you prepare | 3–5 days |
| **White-glove** | Large: 30+ staff, 1,000+/day or several locations | You prepare everything; the owner runs calls; engineers on standby | 2–3 weeks, one location at a time |

Pick up a level when the shop has personalization on most orders, Amazon Custom ZIPs, or more than 3 channels.
Pilots target mid (assisted) first. Large shops wait until `scale-test` passes.

## Steps
1. **Open the shop folder** `invai-docs/customers/<shop-slug>/` (slug like `pilot-a`; never the real name in
   paths or git). Raw files stay in `~/invai-pilots/<shop-slug>/raw/`, outside every repo.
2. **Intake.** List what arrived against the concept's "Questions for pilot shops": order exports per channel,
   SKU sheet, blank list with costs and suppliers (S&S, SanMar), a real vendor gang-sheet PDF and the order
   list sent with it, vendor price per inch, reprint rate, current tools and their cost, staff and roles. Gaps
   become asks, drafted for the owner (`send-owner-draft`).
3. **Write `profile.md`** (template in `levels.md`): orders/day per channel, SKU scheme with examples
   (scrubbed), personalization share and type, blanks, vendor sheet spec (width, DPI, PDF or PNG), staff by
   role and language (how many read Spanish), hardware, pains in their words, and the level chosen and why.
4. **Dry-run the import** with `import-dry-run`. Its numbers decide readiness. Don't configure against
   unmeasured data.
5. **Prepare the setup for the level** using the matching checklist in `levels.md`:
   - self-serve: check the in-app checklist on **Today** covers them (connect a channel or import a CSV,
     import blanks, map SKUs, add the DTF vendor, invite staff) and link the help articles each step needs,
   - assisted: the call pack (agenda, their SKU rules drafted, blank CSV ready for **Catalog → Blanks**
     import, fee overrides and labor and packaging for **Settings → Costs**, vendor for **Settings →
     Vendors**, stations for **Settings → Stations**),
   - white-glove: everything in assisted, plus a migration plan (history to load or not, open orders at
     cutover), a per-location station and staff map, and a cutover day.
   Save it as `customers/<shop-slug>/setup.md`: numbered steps someone else could repeat on a fresh local
   company.
6. **Prove value on their data** (locally): build gang sheets from one real day and record film use against
   the vendor's sheet, sheet build time against theirs by hand (vendor figures say 20–45 minutes), and true
   profit for their top 10 designs from **Analytics → Profit**. These numbers go in `profile.md` and the
   weekly update.
7. **Decide stock push.** Marketplace stock push is off by default (`decisions/0003-stock-push-opt-in.md`).
   Note in the call pack that the owner asks the shop whether to turn on **Pause listings when blanks run
   out** per channel in **Settings → Channels**, after their blank counts are right.
8. **Plan go-live** with `go-live.md`: logins, PINs, tablets paired, scanner and label-print tests, vendor
   invited, the first day's order batch, and the **rollback plan** (they go back to the old way the same day,
   and what that means for orders already on a sheet).
9. **Queue everything outbound for the owner:** welcome and ask emails, call agenda, go-live date. Use
   `send-owner-draft`. Real data in any non-local environment needs an `escalate-to-owner` entry first.
10. **Report readiness** in `customers/<shop-slug>/onboarding.md`: `ready`, `ready with workarounds` (list
    them), or `blocked` (issue ids in `customers/issues.md`). Log every product problem found with
    `triage-support-ticket`.

## Rules
- MUST keep real PII out of every repo. Evidence is scrubbed first (`scrub-pii-fixture`). Slugs, not shop
  names.
- MUST load real data only into a local database, never the shared dev DB others are using, and never a
  deployed one without the owner.
- MUST NOT contact the shop, its vendor or a marketplace. The owner sends everything.
- MUST NOT edit code, even a CSV alias. Data problems become issues for the owning engineer through the tech
  lead.
- MUST NOT promise features, dates or prices. Log the request and send it to the PM.
- MUST NOT go live without a written rollback plan and a passed scanner and label-print test.

## Done when
- `profile.md`, `setup.md` and `onboarding.md` exist in `customers/<shop-slug>/`, with no raw PII.
- Dry-run numbers are recorded, and one real day went import → gang sheet → label locally with no manual DB
  edits.
- Value numbers (film use, time, top-10 profit) are recorded, or the reason they couldn't be is.
- Go-live checklist and rollback plan written; all outbound items are in the owner inbox.
- Readiness stated, with issue ids for every workaround or blocker.

## References
- `levels.md`, `go-live.md` (this folder)
- `.claude/agents/customer-success.md`, `invai-docs/product/scope.md` (segments)
- `invai-docs/00-platform-concept.md` ("Questions for pilot shops"), `invai-docs/build/demo-guide.md`,
  `invai-docs/build/runbook.md`
- Related playbooks: `import-dry-run`, `triage-support-ticket`, `scrub-pii-fixture`, `send-owner-draft`,
  `write-help-article`, `churn-risk-review`
