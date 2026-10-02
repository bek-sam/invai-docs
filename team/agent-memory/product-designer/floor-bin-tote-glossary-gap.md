---
name: floor-bin-tote-glossary-gap
description: invai-floor uses "tote"/"caja" for the pack destination bin everywhere except a new pick-list "shelf bin" label that invented "Bin"/"Compartimento" — a glossary gap worth closing.
metadata:
  type: project
---

`invai-floor/src/i18n/{en,es}.ts` consistently calls the post-pick destination container "tote" (en) / "caja" (es) — `location.bin`, `pack.useTote`, `pack.toteAssigned`, `pack.binOccupied`, etc. T-23-2 (2026-09-29) added `pick.binLabel` for the blank's *storage* bin on the shelf, using new words instead: "Bin {{bin}}" (en) / "Compartimento {{bin}}" (es). Same pick-list row also shows the (pre-existing, unlabeled) destination bin code via an arrow (`i.binCode` → code), so a presser now sees two different "bin" concepts on one row with inconsistent labeling.

**Why:** flagged as a non-blocking note in `invai-docs/waves/23/reviews/T-23-2-product-designer-r1.md` — not blocking because press-station scan-match still catches a wrong pick before a wrong print, but it's a real glossary miss (`write-plain-language-copy`: new shop words need product-designer sign-off before shipping, not after).

**How to apply:** next floor audit or spec touching pick/pack, propose disambiguating the two concepts (e.g. "shelf bin" vs "tote") and add the winning term to `.claude/skills/write-plain-language-copy/glossary.md`. See [[browser-tool-device-select-blocker]] for how this review was done (code trace, no screenshots).
