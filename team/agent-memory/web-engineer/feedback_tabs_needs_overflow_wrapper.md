---
name: feedback-tabs-needs-overflow-wrapper
description: "@invai/ui's TabsList is inline-flex with no overflow handling; at 390px a row of more than ~4 triggers pushes the whole page wider unless you wrap it yourself."
metadata:
  type: feedback
---

`invai-ui/src/components/tabs.tsx`'s `TabsList` is `inline-flex` with no `overflow-x-auto` or
`flex-wrap`. Any `<TabsList>` with enough triggers to exceed the viewport (5+ short tabs, or
3–4 longer ones) will overflow at 390px and, unless contained, cause page-level horizontal
scroll — a MUST violation for mobile screens.

**Why:** found on T-A6's new 7-item view switcher; the pre-existing 5-item "By
design/channel/blank/day/order" row on the same page had the identical latent bug (never
caught before because nothing forced a 390px look at it). Not an invai-ui bug to report — the
fix belongs at the call site, and the project already has a convention for it.

**How to apply:** always wrap `<TabsList>` in `<div className="-mx-1 overflow-x-auto px-1">`
when the tabs might not fit at 390px (which is nearly always once there are more than 3–4).
This is an established pattern, not something to invent: see `orders/index.tsx` and
`shipping.tsx`. Verify with a real scroll-width check
(`document.documentElement.scrollWidth` vs `clientWidth`) at 390px, not just a visual glance —
the tab row itself scrolling internally is fine and expected; the *page* scrolling
horizontally is the bug.
