---
name: web-screen-review-checks
description: Web screen review traps - money wrapping mid-number at 390 es, stale gitignored i18n-es-missing.json, typecheck red from other WIP, clipped native selects in narrow grids
metadata:
  type: feedback
---

Checks for reviewing invai-web screen/copy cards.

- Money wrapping mid-number at 390 px in Spanish: look at every amount in the es 390 screenshots.
- `scripts/i18n-es-missing.json` is gitignored and can be stale; check its mtime against the commit before trusting it.
- Typecheck red can come from another agent's WIP in the shared tree; confirm with `git status` before blaming the card.
- 2026-10-01 T-P4-3: the author's own 390 screenshots can show clipping the report never mentions (native select in a `grid-cols-3` row shows "Mang ▾" for "Manga izquierda"). Read every screenshot yourself, especially selects and badges in narrow grids. Also watch es units with a normal space ("30 d") breaking across lines where the en "30d" fits.

**Why:** "AC met" claims on Spanish copy cards often rest on screenshots that were taken but not read closely.
**How to apply:** open every es screenshot at 390 and 1440 and scan form controls, units and amounts before you mark AC1.
