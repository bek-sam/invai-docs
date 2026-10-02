---
name: mirror-backend-copy-fallbacks
description: when web mirrors a backend-rendered template (digest email, recommendation copy), an empty/optional field's fallback must match the backend's fallback exactly, not just "don't crash".
metadata:
  type: feedback
---

T-20-2 round 1: `recommendation-copy.ts`'s R1 "peak under way" sentence used `p.niche ? nicheLabel(p.niche) : ""`
for the `{{niche}}` slot — safe (no crash, no raw key) but wrong, because R1 can fire from a design's own sales
seasonality with no niche mapping, producing "The  season is on now" (empty slot, double space) on the web
while the backend's `digest/render.ts` `marketPart()` for the *same record* correctly fell back to the peak
month name (`p.niche ? nicheLabel(p.niche, lang) : peak`). Caught by the reviewer, not by tests, because the
existing tests only covered the niche-present case.

**Why:** web and backend both render user-facing copy from the same `MarketRecommendation`/`DigestInsight`
record for different surfaces (assistant card vs. digest email vs. digest page); when a card grants access to
one side's renderer, check the other side's renderer for the same field's fallback behavior before assuming an
empty string or omission is acceptable. "It doesn't crash" is not the same as "it matches".

**How to apply:** when building or fixing copy that mirrors a backend template (`invai-backend/src/modules/
digest/render.ts`, market rules), grep the backend for the same field's fallback and copy it exactly, then add
a test for the missing-field case in *both* directions (not just the common case). See
[[project_t20_2_billing_locale_gap]] for the related lesson on matching the digest's number/locale convention
across surfaces.
