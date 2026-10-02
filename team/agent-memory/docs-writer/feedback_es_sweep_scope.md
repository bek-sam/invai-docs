---
name: feedback-es-sweep-scope
description: The es-help "stray English word" sweep must include glossary shop words, not just internal/technical terms.
metadata:
  type: feedback
---

When checking help/es/*.md for untranslated English, grep for glossary shop words (transfer, blank, gang
sheet, etc. — see [[feedback_es_placeholders]] and `.claude/skills/write-plain-language-copy/glossary.md`)
in addition to internal/technical words (tenant, queue, webhook, mock...). T-21-4 round 1's sweep only
checked the technical-word list and missed "transfers" left untranslated in `receiving.md` (x4) and
`index.md` (x1); round 2 also caught 4 more instances of the same miss in `gang-sheets-and-vendors.md` and
`profit-and-ad-spend.md` that round 1 never caught either, because the same narrow grep was used across
all 13 articles.

**Why:** product-designer caught it in review, not the author's own check — the check that should have
caught it (internal-words sweep) was scoped too narrowly.

**How to apply:** before marking any es help article done, run a second grep pass keyed to the glossary's
English-word column (`transfer`, `blank`, `gang sheet`, `sheet`, `press`, `pack`, `receive`, `vendor`,
`profit`, `shipping`, `label`, `ship by`, `at risk`, `on hold`, `reprint`) across every *.md in help/es,
not just the file you're actively editing — a word missed once in one article is often missed the same way
in others that describe the same feature.
