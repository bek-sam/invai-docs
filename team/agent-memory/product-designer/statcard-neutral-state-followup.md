---
name: statcard-neutral-state-followup
description: invai-ui StatCard has no neutral/no-arrow delta state — a follow-up I own, found reviewing T-20-2.
metadata:
  type: project
---

2026-09-28, reviewing T-20-2 (`invai-docs/waves/20/reviews/T-20-2-product-designer-r1.md`): `@invai/ui`'s
`StatCard` always draws an arrow whenever `delta` is set — `deltaDirection` only picks the color/icon, there's
no "no direction" value for a zero/unchanged change. web-engineer worked around it with a local `GlanceTile`
on the digest page (accepted as fine for now, per `add-ui-component`'s "build locally, report the gap"
pattern).

**Why it matters going forward:** file a real `invai-ui` follow-up to add a neutral `deltaDirection` (no
arrow, muted text, still passes "never color alone" via the value text) so the digest glance grid — and any
future consumer with an "unchanged" state — can drop the local copy. Related to
[[market-signals-and-digest-wave-18-19]].
