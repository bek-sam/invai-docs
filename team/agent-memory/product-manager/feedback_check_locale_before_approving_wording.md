---
name: check-locale-before-approving-wording
description: Before approving a Spanish copy example in a wording rule, check it against the digest's already-shipped Intl locale convention (facts.ts LOCALE map, AC13 es-US), not just the English/Spanish text.
metadata:
  type: feedback
---

When I write an example string for a new Spanish copy row (plan review, spec Copy table), I must
check it against the number-formatting locale the area already ships, not just translate the
words. `invai-backend/src/modules/digest/facts.ts` has one `LOCALE` map
(`{ en: "en-US", es: "es-US" }`, AC13: "money stays USD in Spanish too") used for every number the
digest renders — money, counts, relative percent, hours. A new metric that introduces its own
locale (e.g. plain `"es"`, giving a decimal comma) produces a line that mixes separators
(`"31.4% (+3,3 pts ...)"`), which reads as a bug next to the rest of the sentence.

**Why:** In wave 20's T-20-1 (2026-09-28) I approved `"+6,9 pts"` as the Spanish example for the
new `change.pts` copy row in `plan-pm.md`, without checking it against `facts.ts`'s already-shipped
`es-US` convention (AC13). The builder implemented exactly what I approved, correctly, and flagged
the inconsistency themselves in their report's Decisions section. QA's acceptance test then pinned
the comma too. All three of us (me, the builder, QA) propagated the same unchecked example forward
until round-1 review caught it — see `invai-docs/specs/weekly-digest.md`'s 2026-09-28 review-log
line and `waves/20/reviews/T-20-1-product-manager-r1.md`.

**How to apply:** Before finalizing a Spanish copy example for money, counts or any percent/point
figure, grep the module's own formatting code (`grep -n "LOCALE\|Intl.NumberFormat" <module>/facts.ts`
or equivalent) and use the same locale the module already uses for every other number in the same
rendered sentence or email. One digest = one number convention throughout.
