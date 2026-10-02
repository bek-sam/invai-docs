---
name: feedback-locale-currency-nbsp-overflow
description: Spanish currency strings from Intl/@invai/ui's Money join the number and "US$" with a non-breaking space, so a narrow KPI grid cell clips or breaks mid-word in es even when it fits fine in en.
metadata:
  type: feedback
---

`Intl.NumberFormat('es', {style:'currency', currency:'USD'})` joins the amount and the
currency code with U+00A0 (non-breaking space), e.g. `"-123.456,78 US$"`. That NBSP
makes the whole string one unbreakable run in the browser, so a grid item sized to English
numbers overflows in Spanish (B-226: a 6-column KPI grid clipped the "Costos" value at
1440px in es, even though nothing was wrong in en).

**Why:** confirmed with `node -e` printing codepoints — the space before "US$" is `a0`, not a
regular `0x20`. `break-words`/`overflow-wrap:break-word` alone "fixes" the overflow but
breaks at an ugly arbitrary point ("16.468,39 U" / "S$"), because CSS grid items default to
`min-width:auto` (their own min-content size), which a `minmax(0,1fr)` track can't override
without the item itself getting `min-w-0`.

**How to apply:** for any money/KPI tile that might render in Spanish, (1) give the grid item
`min-w-0` and the value text `break-words` as a safety net, but (2) size the grid so the
*whole* string fits on one line without needing to break at all — that's the real fix. 4–5
equal columns at ~1400px content width was safely wide enough in practice (T-A6's
`profit-v2/kpi-tile.tsx`); 6 columns was not. Don't rely on `break-words` alone to make a
clipped Spanish string "not clipped" — it produces a worse-looking wrap, not a real fix.
See [[feedback_tabs_needs_overflow_wrapper]] for the companion mobile-width issue found the
same session.
