---
name: feedback-es-placeholders
description: Keep interpolation placeholders like {{name}} untranslated in Spanish help copy
metadata:
  type: feedback
---

Spanish help articles must keep i18n interpolation tokens exactly as the catalog spells them
(`{{name}}`, `{{blank}}`, `{{channel}}`, `{{poNo}}`, `{{day}}`, `{{count}}`, `{{n}}`) — never
translate the token itself to `{{nombre}}`, `{{prenda}}`, `{{canal}}`, etc.

**Why:** `invai-web/src/i18n/es.ts` and `invai-floor/src/i18n/es.ts` never translate the key inside
`{{ }}`, only the surrounding sentence (e.g. `"¿Cambiar el rol de {{name}}?"`). I drafted T-21-4's
Spanish articles with translated placeholder names on a first pass and caught it with
`grep -o '{{[^}]*}}' *.md` before committing — the fix touched 5 files.

**How to apply:** After writing any Spanish help/UI copy that quotes a message containing `{{...}}`,
grep both language files for stray non-English tokens before calling it done. See
`.claude/skills/write-plain-language-copy/SKILL.md` step 5 ("Keep placeholders exactly").
