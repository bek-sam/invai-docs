---
name: optional-param-template-holes
description: Code->translated-line builders with `p.x ?? ""` leave holes when the backend omits an optional param; probe every code with real i18next catalogs plus each omitted key
metadata:
  type: feedback
---

2026-10-01 T-P5-5: web alert-line builders substituted `p.vendorName ?? ""`; backend (T-P5-4 r2) omits vendorName when unknown, so es read "el correo a  se haya enviado". Author's tests used a fake `t` and full params, so they never saw it.

**Why:** "every key optional" contracts + per-code templates = silent broken sentences in both languages.
**How to apply:** for any messageCode/reasonCode card, write a throwaway vitest probe in your own worktree that inits i18next with the real en/es catalogs and renders every code with full params, each documented-omittable key removed, and an unknown code. Write output to a file (vitest swallows console). Note the app sets escapeValue:false in invai-ui; a default i18next instance shows `&amp;` — not a bug. Related: [[sample-roundtrip-test-gap]].
