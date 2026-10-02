---
name: t_p7_3_confidence_badge
description: How invai-ui's i18n reaches web, and the colocated-test pattern for a route file's exported pure helper
metadata:
  type: project
---

T-P7-3 (2026-10-01): `invai-web/src/i18n/index.ts` calls `initI18n()` from `@invai/ui` first (loads the
kit's `src/i18n/locales/{en,es}.json` into i18next's `translation` namespace), then layers the app's own
`en.ts`/`es.ts` on top with `addResourceBundle(..., true, true)`. So a kit component's own `t("someKit.key")`
lookup resolves against the kit's catalog even inside web, with no extra wiring — when promoting a local
web component into `@invai/ui` with identical copy, drop the web-side keys instead of passing a `label`
override, once a script diff confirms the kit's text is byte-identical to the old web text.

**Why:** avoids two driftable copies of the same three strings (web's old `market.band.*` vs the kit's new
`confidenceBand.*`); `ConfidenceBadgeProps.label` exists precisely for the case where the text *isn't*
identical, so don't use it as a default.

**How to apply:** before swapping a local component for a newly-promoted kit one, check whether the kit's
copy is actually the same (diff script or manual read) before deciding to drop web's old i18n keys vs. pass
`label`.

Also confirms [T-P5-5 reason codes](project_t_p5_5_reason_codes.md)'s route-file pattern a second time: a
route file's exported pure helper needing a unit test gets a colocated `-<routename>.test.ts` (dash prefix,
router-plugin ignores it), even when the card's owned-paths list only names the route file itself — the test
file is implied by an acceptance criterion requiring a unit test.
