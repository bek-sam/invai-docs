---
name: feedback-statcard-no-neutral-direction
description: invai-ui's StatCard always draws an arrow whenever `delta` is set; build a local tile for "no change" states instead of using it.
metadata:
  type: feedback
---

`@invai/ui`'s `StatCard` (`invai-ui/src/app/stat-card.tsx`) defaults `deltaDirection = "up"` and always
renders an arrow icon whenever the `delta` prop is a non-empty string — `deltaDirection` only picks
the color/icon, it can't suppress the arrow. There is no "neutral, no arrow" state.

**Why:** wave 20 T-20-2 (digest glance grid) needed "unchanged" / "sin cambio" deltas with no arrow
and a neutral color (gate issue 3). QA's own acceptance e2e (`e2e/digest-dates.spec.ts`) pins this as
a real kit bug, not a web-only rendering choice.

**How to apply:** don't fight `StatCard` with `deltaDirection: undefined` — the arrow still shows.
Build a small local tile on the `Card` primitive instead (same look: `border p-4`, label/value/delta
paragraphs), controlling the arrow yourself. Report the gap to product-designer so `StatCard` can grow
a real neutral state (e.g. `deltaDirection?: "up" | "down" | "flat"`) for the next card that needs it,
rather than every consumer reinventing the tile. See `invai-web/src/components/digest/glance-grid.tsx`
for the pattern.
