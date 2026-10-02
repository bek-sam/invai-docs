---
name: enviar-glossary-ambiguity
description: floor "enviar" is overloaded between shipping (glossary "ship by" = "enviar antes de") and the sync outbox ("escaneos sin enviar" = unsent scans on the tablet); a bare "por enviar" pill reads as shipping, not sync.
metadata:
  type: feedback
---

2026-10-01, T-P4-2: the floor-engineer's round-1 fix for the crowded Spanish header pill shortened
"{{count}} escaneo(s) por sincronizar" to "{{count}} por enviar" to save width. `reviewer` (r1,
`invai-docs/waves/P4/reviews/T-P4-2-reviewer-r1.md`) correctly blocked this: "enviar" in this product
means shipping an order ("enviar antes de" = ship by, `envío(s)` = shipping) everywhere else in both
catalogs, so a packer near the shipping table reading "12 por enviar" would think 12 orders need to
ship, not "12 of my scans are still stuck on this tablet and will be lost if I forget it" — the exact
warning this pill exists to give. The fix that stuck: "{{count}} escaneo(s) sin enviar", reusing the
noun ("escaneo") and this catalog's own `outbox.title: "Sin enviar"` instead of the generic verb
alone.

**Why it matters going forward:** when shortening floor/web copy under a width constraint, don't drop
to a bare glossary verb to save characters if that verb already has a different, strong meaning
elsewhere in the same app. Keep the noun, or pair the verb with a word unique to the correct meaning
("sin enviar" tied to the outbox vs "enviar antes de" tied to ship-by). Grep both catalogs for the
word first (`grep -n "enviar" invai-floor/src/i18n/es.ts invai-web/src/i18n/es.ts`) before approving
a shortened form.

Related: [[floor-bin-tote-glossary-gap]].
