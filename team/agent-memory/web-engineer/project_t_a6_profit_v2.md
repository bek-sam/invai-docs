---
name: project-t-a6-profit-v2
description: T-A6 (Profit v2) landed 2026-09-30; analytics.* *Pct fields are already percent-numbers (×100), not 0..1 ratios, despite a schema comment that says otherwise — check real data, not the comment.
metadata:
  type: project
---

T-A6 (wave A2, web-engineer) added six new views to `/analytics/profit` (contribution,
losing orders, leakage, shipping profit, why-changed, break-even) behind a `view` search-param
switcher, default unset = the original untouched table (kept for golden-path parity). Landed
2026-09-30, commit `f9124ac` in invai-web.

**Non-obvious data-shape gotcha for whoever builds T-A7 (Operations/Inventory) next:**
`invai-contracts/src/schemas/analytics.ts`'s doc comment on `ContributionLadder.cm1Pct` etc.
says `"CM ÷ revenue"` (implying a 0..1 ratio), but the *actual* backend
(`invai-backend/src/modules/analytics/finance-service.ts`) returns it already multiplied by
100 (e.g. `cm3Pct: 31.6` for a 31.6% margin) — confirmed against the real seed via a curl/
typed-client probe, not by trusting the comment. Every other `*Pct` field in that file
(`losingPct`, `leakagePct`, `pctOfGross`, and by the same pattern `ReprintCost.ratePct`,
`FilmWaste.filmUsePct`, `LateDriverRow.latePct`, `SizeMixSizeRow.salesSharePct`/
`stockSharePct` — T-A7's fields) documents "× 100" explicitly and follows the same
percent-number convention. Only `UnitEconomics.estimatedShare` (and anything named without
"Pct") is a true 0..1 ratio. Added `formatPctNumberLocale`/`formatRatioPctLocale` to
`invai-web/src/lib/format.ts` for the two cases — reuse them rather than re-deriving.

See also [[feedback_locale_currency_nbsp_overflow]] and
[[feedback_tabs_needs_overflow_wrapper]], both found while building this card's screenshots.
