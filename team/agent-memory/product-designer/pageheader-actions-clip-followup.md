---
name: pageheader-actions-clip-followup
description: invai-ui PageHeader actions row (shrink-0) clips at 390px instead of wrapping/scrolling — seen on /analytics/profit (T-A6) and Today/Operations (T-A7); owed a follow-up.
metadata:
  type: project
---

2026-09-30, reviewing T-A7 (`invai-docs/waves/A2/reviews/T-A7-product-designer-r1.md`): `@invai/ui`'s
`PageHeader` wraps its actions in `shrink-0`, so a 3-control row (e.g. "Build sheets" / "Import CSV" / "Buy
labels", or "Export CSV" alone) gets cut off at 390px instead of wrapping to a second line or scrolling
horizontally — the button text is unreadable ("Bu…", "C…", "Exp…"). Confirmed on two different screens by two
different builders (T-A6's `/analytics/profit`, T-A7's Today and `/analytics/operations`), so this is a real,
repeat kit gap, not a one-off.

**Why it matters going forward:** file a real `invai-ui` fix — wrap the actions row onto a second line at
narrow widths, or let it scroll horizontally like the tab-row pattern already does (`-mx-1 overflow-x-auto
px-1`, used in `orders/index.tsx` per T-A6's review). Same "accept as consumer follow-up, don't block the
card" treatment as [[statcard-neutral-state-followup]] — web-engineer isn't blocked on it, but it should stop
recurring once fixed once, centrally.

Related, same review: `KpiTile` (`src/features/analytics/shared.tsx`, copied from T-A6's own workaround) truncates
its label with `className="truncate"` and no `title` attribute — at 390px labels like "Costo de pra…" /
"Rotaciones(/…" are unreadable. Same "worth fixing once in the shared pattern" shape; not yet filed as its own
invai-ui task.
