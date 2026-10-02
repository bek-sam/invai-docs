---
name: feedback-intl-date-trailing-punctuation
description: An Intl.DateTimeFormat value can end in its own punctuation (es-MX "a.m."/"p.m."); never follow it with a template's own trailing period
metadata:
  type: feedback
---

A copy template that ends `... {{date}}.` breaks in Spanish when `{{date}}` is an
`Intl.DateTimeFormat` string with `hour12` AM/PM: es-MX renders "4:30 a.m." (with its own period),
so the sentence reads "4:30 a.m.." — a visible double-period typo. English "4:30 AM" has no
trailing punctuation, so the bug is invisible until you screenshot the Spanish build.

**Why:** found live-screenshotting T-P5-5's `alerts.line.order_at_risk` line
(`invai-web/src/i18n/{en,es}.ts`) — looked fine in English, wrong in es-MX at both 1440 and 390.
Same family as [[project_t_p4_3_spanish_sweep]]'s "English literal wrapped around an
already-localized number" bug class, but the trailing character here comes from the *locale*
formatter itself, not from English prose around a number.

**How to apply:** when a copy template ends with an Intl-formatted date/time placeholder, drop the
template's own trailing period (the formatted value supplies its own sentence-final punctuation,
or none, depending on locale). Only an issue when the placeholder is the *last* token before
punctuation; mid-sentence placeholders are fine. Always screenshot the Spanish line at the exact
param values that exercise AM/PM, not just a quick glance at the English one.
