---
name: market-signals-and-digest-wave-18-19
description: Context on the wave 18 (market signals) and wave 19 (weekly digest) specs I reviewed 2026-09-27 — new vocabulary, shared feedback pattern, and the two specs' coupling.
metadata:
  type: project
---

Reviewed `invai-docs/specs/market-signals.md` (wave 18) and `invai-docs/specs/weekly-digest.md` (wave 19) as
co-reviewer 2026-09-27; both approve-with-changes (see the review files in `invai-docs/waves/18/reviews/` and
`invai-docs/waves/19/reviews/`).

**Why it matters going forward:**
- Both specs introduce shop-facing vocabulary that isn't in `glossary.md` yet: niche/nicho, seasonality/
  temporada, sample data/datos de muestra, confidence band, steady week/semana estable, act on/actuar. Add
  these to `.claude/skills/write-plain-language-copy/glossary.md` once T-18-5/T-19-5 actually ship (not
  before — the spec could still change the words in review).
- The two specs share one feedback concept (a market recommendation vote is "done"/"not useful") but the
  digest spec separately describes a thumbs-up/down + reason (Not relevant/Wrong/Already knew) widget for
  *all* digest insights, without saying which one a Market watch item uses. I flagged this as blocking in the
  wave 19 review; whichever way the PM resolves it, don't build two separate vote UIs for the same underlying
  record — see [[assistant-structured-content-gap]] for the related contract gap.
- A `ConfidenceBadge` shared component (tone + icon + text per band: high/medium/low) would serve both specs
  and doesn't exist in `invai-ui` yet. Only build it once a wave actually needs it (don't speculatively add it
  now); it's a small, low-risk `add-ui-component` candidate.
