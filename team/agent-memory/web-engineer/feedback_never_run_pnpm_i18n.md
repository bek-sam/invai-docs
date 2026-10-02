---
name: feedback-never-run-pnpm-i18n
description: agent-brief's hard rule overrides write-plain-language-copy's "run pnpm i18n" step — add keys by hand to en.ts/es.ts/scripts/i18n-es.json instead
metadata:
  type: feedback
---

`invai-docs/team/agent-brief.md` ("Hard rules") says "all UI text is en and es, added by hand
(never run `pnpm i18n`)" — this overrides the `write-plain-language-copy` skill's documented step
of running `pnpm i18n` to regenerate `src/i18n/{en,es}.ts` from `t("key","Default")` calls.

**Why:** `gen-i18n.py` extracts every `t(...)` call across all of `src`, including other agents'
uncommitted in-progress edits in the same shared tree — running it mid-wave risks picking up or
clobbering keys that aren't yours yet (confirmed as a real drift risk in
[[project_t23_1_p2_sweep]]: "i18n-es.json can drift from hand-edited es.ts").

**How to apply:** when a card adds one or a few keys, hand-edit all three files — `src/i18n/en.ts`,
`src/i18n/es.ts`, and `scripts/i18n-es.json` (the source `pnpm i18n` would otherwise read for
Spanish) — keeping them consistent, instead of invoking the generator. Check
`scripts/i18n-es-missing.json` is absent (or has none of your keys) as the card's AC normally asks;
since you never ran the generator, it simply won't be touched.
