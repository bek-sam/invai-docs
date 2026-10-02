---
name: qc-term-inconsistency
description: invai-web es.ts mixes "QC" (untranslated) and "control de calidad" for the same concept, like the documented "transfer" split.
metadata:
  type: project
---

`invai-web/src/i18n/es.ts` has two conventions for QC live side by side: `qcFails: "Fallas de QC"`,
`Taller: QC, empaque y etiquetas` keep "QC" in English, while `qc_fail_spike` (alert title) and the new
T-P5-5 `orders.timelineReason.qc_fail`/`qc_pass` ("Falló/Pasó el control de calidad") spell it out.

**Why:** found while reviewing T-P5-5 (2026-10-01). Not a new bug — the new timeline-reason keys match the
nearest sibling (`qc_fail_spike`) — but it's the same unresolved "pick one" gap glossary.md already flags for
"transfer" (floor says "Transferencia", web says "Transfer").

**How to apply:** next glossary pass, add a QC row to `glossary.md` and decide one spelling for web (floor
already standardizes on "control de calidad" per the glossary table). Don't block a card on this alone unless
it's the card's whole purpose — flag it and move on, like [[enviar-glossary-ambiguity]] and the transfer note.
