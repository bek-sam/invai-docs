# Onboarding by level

## profile.md template
```
# <shop-slug> profile   (level: self-serve | assisted | white-glove)
Updated: YYYY-MM-DD
| Item | Value | Source |
|---|---|---|
| Orders/day by channel | Etsy __, Amazon __, Shopify __, TikTok __, Walmart __ | export row counts |
| SKU scheme | e.g. BC3001-BLK-M-D1042 (style-color-size-design) | SKU sheet |
| Personalization | __% of orders; Etsy questions / Amazon Custom ZIP / Shopify properties | exports |
| Blanks | brands, styles, suppliers (S&S / SanMar), reorder habit | blank list |
| DTF vendor | sheet width __ in, __ DPI, PDF/PNG, price per inch $__, turnaround __ | vendor PDF |
| Staff | owner __, office __, designer __, pressers __, packers __, receiver __; Spanish readers __ | intake |
| Hardware | tablets, scanners, label printer | intake |
| Tools today and monthly cost | ShipStation $__, gang-sheet service $__, listing tools $__ | invoices |
| Reprint rate | __% (their estimate or data) | intake |
| Pains in their words | "..." | owner's notes |
| Dry-run results | link | import-dry-run |
| Value on their data | film use __% vs vendor __%; sheet time __ vs __; top-10 profit | local run |
```

## Self-serve (small shops)
Goal: the shop finishes the **Today** onboarding checklist alone, the same day.
1. Check each checklist step works with a small shop's real export (dry-run results).
2. For each step, link a help article (`invai-docs/help/en|es/`). A missing one becomes a `write-help-article` request:
   - Connect a sales channel or import a CSV (**Settings → Channels**, or **Import CSV** on Today)
   - Import your blanks (**Catalog → Blanks**)
   - Map your SKUs (**Catalog → SKU Mapping**, "Accept N at ≥80%", "Save as rule")
   - Add your DTF vendor (**Settings → Vendors**)
   - Invite your team (**Settings → Team**)
3. Note where a small shop's owner, who does every job, would stall. Stall points become issues (severity: staff time) or help articles.
4. Check the plan fit: Trial is 300 orders, 3 users, 2 connections (`PLAN_CATALOG`). A shop that outgrows it in week 1 needs the owner to talk plans.

## Assisted (mid-size shops): the call pack
Prepared by you; the owner runs the call.
- Agenda (60–90 min): their day today → import one real export → map SKUs together → build one sheet → pair one tablet → questions.
- Drafted SKU rules for their scheme, with the expected auto-map rate from the dry run.
- Blank CSV in the **Catalog → Blanks** import format (same columns as `BlankVariantInput`), with their costs.
- **Settings → Costs** values: channel fee overrides, packaging per order, labor rate per hour.
- Vendor sheet spec for **Settings → Vendors**; stations list for **Settings → Stations** (Pick, Press 1..n, QC, Pack).
- Staff list by role with language. PINs are set by the shop, never written in our files.
- The stock push question (decision 0003).
- Known workarounds from the dry run, in plain words.

## White-glove (large or multi-location shops)
Everything in assisted, plus:
- **Migration plan:** which history to load (for profit baselines) or skip; how open orders move at cutover; how items already on a vendor sheet are handled.
- **Location map:** per location, its stations, staff, printers, and which channels ship from it.
- **Scale check:** confirm `scale-test` (QA) passed for this volume before committing a date. If not, escalate.
- **Cutover day plan:** hour by hour, who from the team is on standby (tech lead names them), and the rollback trigger ("if more than __ orders are blocked by 11:00, roll back").
- **One location first**, one week stable, then the next.
