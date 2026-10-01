# Review: T-A6 Profit v2 screens — round 1

Reviewer: product-designer on Claude Sonnet 5
Author: web-engineer on Claude Opus 5.5

## Verdict: approve

Inputs only: task card, `git -C invai-web show f9124ac`, the author's report, and the 37 screenshots in
`.e2e-out/web/T-A6/`. No stack started (decision 0019).

## The tech lead's question — the missing thousands separator

Confirmed with plain `Intl.NumberFormat("es", {style:"currency", currency:"USD"})` in Node: 4-digit amounts
lose the grouping separator ("1481,13 US$") while 5+-digit ones keep it ("16.468,39 US$") — this is real CLDR
data for the bare `"es"` locale (`minimumGroupingDigits: 2`: a leftmost group of 1 digit doesn't qualify), not
a bug in this diff's code. `es-US`/`es-MX` don't have the quirk but also don't match the "16.468,39 US$"
style already used everywhere else (they render American-style "$16,468.39").

**Verdict: acceptable to ship as-is, but not fully acceptable long-term.** It's inherited from `@invai/ui`'s
`Money`/the app's existing bare-`"es"` convention (the same one `digest-copy.ts`'s `digestMoneyLang()` already
had to special-case), not introduced by T-A6 — `formatMoneyShortLocale` deliberately matches it for
consistency within this screen (correct call for this card). But a shop owner scanning `leakage-es-1440.png`
sees "Comisiones del canal -1481,13 US$" next to "Ventas brutas 16.482,34 US$" with no separator on one and
one on the other — an easy misread under time pressure (principle 2, "show urgency honestly" extends to "show
numbers unambiguously"). Filing as an `invai-ui` follow-up for myself: force `minimumGroupingDigits: 1` in the
shared `Money`/format helpers so grouping is never locale-dependent. Not blocking this card.

## Findings (non-blocking)

1. **S4 — `losing-es-1440.png` / `losing-en-1440.png`:** every row in "Orders that lost money" shows `Units 0`
   and `Revenue $0.00` despite real negative CM2 and cost lines. The Contribution view's by-channel table
   (`contribution-en-1440-dark.png`) populates units correctly for the same period, so this looks like an
   `analytics.losingOrders` backend data gap (T-A3), not a web rendering bug — the column correctly reads
   `row.units`/`row.revenue`. AC-A2 itself only requires order #, CM2 and largest cost line (met). Flag to the
   tech lead for the backend owner; not a T-A6 defect.
2. **S4 — `designer-no-access.png`:** nav entry is correctly hidden and data is correctly refused (403
   confirmed), but the page chrome (period/channel selects, all 7 tabs, Recompute, Export CSV) still renders
   above the "No access" panel. A role that lands here sees controls for a page it can't use. Cosmetic; worth
   a full-page gate the next time this pattern is touched.
3. **Optional — dead code:** `formatPercentPoints` (format.ts) is exported and unit-tested but never called
   from any of the six new views — none of Track A's views compare two margin percentages, only dollar
   splits ("Por el volumen"/"Por la tasa"). Either wire it somewhere real or drop it; not blocking since no AC
   requires a percent-point delta in these specific views.

## What I checked and liked

- **Copy (en/es):** spot-checked all ~90 new `es.ts` keys (diff) — plain shop words, correct glossary terms,
  natural Spanish (tú-adjacent, not machine-translated). Banner ("39 pedidos todavía no están en estos
  números"), break-even prompt, and empty-shipments hint all match the spec's exact language.
- **States:** AC-A3 (zero labeled shipments), AC-A6 (no-costs prompt → set $2,500 → numbers), AC-A7 (banner)
  all screenshotted and read correctly in both languages (`breakeven-en-1440.png`,
  `breakeven-set-en-1440.png`, `contribution-es-1440.png`, `losing-es-1440.png`, `leakage-es-1440.png`).
- **B-226:** `overview-es-1440.png` confirms no clipping at 1440; KPI grid capped at 3 columns reads cleanly.
- **Layout at 390px:** `contribution-es-390.png`, `breakeven-es-390.png` — no horizontal scroll on the page,
  two-column KPI tiles wrap money onto two lines without clipping, the 7-tab row scrolls horizontally inside
  its own `-mx-1 overflow-x-auto px-1` wrapper.
- **Tab-row consistency:** the new view switcher reuses `@invai/ui`'s `Tabs`/`TabsList`/`TabsTrigger` and the
  same scroll-wrapper pattern already used in `orders/index.tsx` — not a one-off. The per-view dimension
  picker uses `NativeSelect` instead of a second tab row, a reasonable choice given 5 different dimension sets
  across views.
- **Dark mode:** `contribution-en-1440-dark.png` — tokens read correctly, no raw hex, danger/success colors
  consistent with the rest of the app.
- **Tokens/components:** `Money`, `ChannelBadge`, `DataTable`, `EmptyState`, `Section`, `NativeSelect` used
  throughout; no one-off styled money or percent strings found in the diff outside the new `format.ts`
  helpers, which are the right place for them.

## Evidence

- `git -C invai-web show f9124ac --stat` (18 files, all inside T-A6's owned paths)
- Node check: `Intl.NumberFormat("es"/"es-US", {style:"currency",currency:"USD"})` on -1481.13 and 16468.39
- `grep -rn "formatPercentPoints" invai-web/src` → defined + tested, zero call sites
- Screenshots read: overview-es-1440, breakeven-set-en-1440, contribution-es-390, costs-es-1440,
  losing-es-1440, leakage-es-1440, breakeven-es-390, designer-no-access, contribution-en-1440-dark,
  why-es-1440

## Optional notes

- Consider a full-page "No access" state (hide the header actions and tabs too) as a shared pattern, not just
  for this screen.
