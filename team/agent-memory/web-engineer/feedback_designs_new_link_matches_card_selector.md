---
name: feedback-designs-new-link-matches-card-selector
description: Playwright selector gotcha on /catalog/designs - "Nuevo diseño"/"New design" button and each card use the same href pattern
metadata:
  type: feedback
---

On `designs.index.tsx`, both the "New design"/"Nuevo diseño" button and every design card link to `/catalog/designs/$designId` (the button with `params={{designId: "new"}}`). A Playwright locator like `a[href*='/catalog/designs/']` matches the new-design button first (it's earlier in the DOM), so clicking "first card" actually opens the new-design form instead of an existing design's detail page.

**Why:** found during T-P4-3 round 2 while retaking screenshots of the placement-select fix — the first attempt silently landed on the blank "new design" page at both 1440 and 390, which would have shipped a wrong/misleading screenshot if not checked against the actual rendered image.

**How to apply:** when scripting navigation to an existing design's detail page from the list, filter out the new-design link, e.g. `a[href*='/catalog/designs/']:not([href$='/new'])`. Always look at the resulting screenshot before trusting it matches the intended route — don't assume `.first()` found the right element.
