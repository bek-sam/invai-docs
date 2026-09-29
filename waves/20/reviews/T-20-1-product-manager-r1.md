# Review of T-20-1 (round 1) — product-manager

- Reviewer: product-manager
- Author: backend-engineer on Opus 5.5
- Co-review scope (per card): the wave 20 wording rule I approved in `plan-pm.md`
- Verdict: **changes-required**

## Copy check (approved rows vs shipped strings)
Checked every rendered string in `git show bfae180` and the report's curl output against the four
approved rows and the two spec Copy tables (`specs/market-signals.md` "R1 action (peak under way;
wave 20)", "source.weekEnding (wave 20)"; `specs/weekly-digest.md` `change.pts`,
`change.unchanged`).

| Row | Approved | Shipped (`render.ts` / `facts.ts` / curl) | Match? |
|---|---|---|---|
| R1 peak under way | "The {{niche}} season is on now. Make sure {{design}} is listed and in stock." / "La temporada de {{niche}} ya empezó. Asegúrate de que {{design}} esté publicado y con inventario." | Identical in `render.ts`; curl: "The Faith season is on now. Make sure Blessed & Sun-Kissed is listed and in stock." / "La temporada de Fe ya empezó..." | Yes |
| source.weekEnding | "week ending {{date}}" / "semana al {{date}}" | `market.source` = "{{source}}, week ending {{date}}" / "{{source}}, semana al {{date}}"; curl: "week ending Sep 27" / "semana al 27 sep" | Yes |
| change.pts | "{{sign}}{{n}} pts" (points scoped to `marginPct`/`onTimePct` only) | `glanceOf` scopes points to `unit === "pct" \|\| unit === "ratio"`, which in the 5-row glance array is exactly `marginPct` and `onTimeRate` — correct scope. En "+6.9 pts" matches. **Es "+3,3 pts" / "+6,9 pts" uses a decimal comma** | No — see below |
| change.unchanged | "unchanged" / "sin cambio" | `UNCHANGED` constant, verbatim; curl "unchanged" / "sin cambio" | Yes |
| R1 no act-by while under way, no empty niche | `params.niche = f.niche` fix I flagged in the plan review | `rules.ts` now takes `today`/`niche` on `DesignFacts`, sets `params.niche` when under way; curl shows `"niche":"faith"`, no `actByDate` | Yes |
| Past-peak dropped | not shown | `r1PastPeak` filter in `market-watch.ts` (vs `weekEnd`) and `market/service.ts` (vs shop-local today, keeping `ids` lookups); curl confirms 3 past-peak rows absent | Yes |

Everything matches except one: the decimal comma in Spanish points.

## Open question, decided: Spanish number convention
**Pick es-US throughout the whole digest, including points.** `facts.ts` already has one
locale map (`LOCALE = { en: "en-US", es: "es-US" }`, comment: "Money stays USD in Spanish too
(AC13)") used for money, counts, relative percent and hours. The new `PTS_LOCALE` in this diff
(`es: "es"`, plain, giving a decimal comma) is the only exception in the file, and it produces a
line that mixes separators: `"Margen: 31.4% (+3,3 pts vs. la semana pasada)"`. That reads as a
bug, not an intentional Mexican-Spanish convention, next to `"31.4%"` in the same sentence. The
comma example came from my own wave 20 plan review (`plan-pm.md` line 48, `"+6,9 pts"`), written
without checking it against AC13's already-shipped `es-US` rule — I'm correcting that now, not
introducing a new rule.

Decision: Spanish points render **"+6.9 pts"**, identical to English, using the existing `LOCALE`
map (no new `PTS_LOCALE`). Recorded in `invai-docs/specs/weekly-digest.md` ("Change wording" note
+ a dated review-log line, 2026-09-28). No owner escalation needed — this is copy/i18n
consistency inside already-approved scope, not pricing, spend or plan limits.

## T-20-1 must change (round 2) — exact change
This is backend's fix, not T-20-2's, because `facts.ts` computes and stores the formatted
`en`/`es` strings server-side (both the email and the wire fact the web displays verbatim per
AC3's "keep the wire shape, change only the values"); T-20-2 doesn't reformat numbers itself.

1. `invai-backend/src/modules/digest/facts.ts`: drop the separate `PTS_LOCALE` map; `signedPts`
   should use the existing `LOCALE[lang]` (same as `signedPct`/`money`), so Spanish points format
   as `"+6.9 pts"` / `"-6.9 pts"`, not `"+6,9 pts"`.
2. Update the author's own `digest/pure.test.ts` assertions at lines 620 and 637 (currently expect
   `"+6,9 pts"` / `"-6.9 pts"` / `"-6,9 pts"`) to the period-decimal form.
3. **Flag to the tech lead / qa-engineer, not backend-engineer's to touch:** QA's acceptance file
   `digest/date-copy.acceptance.test.ts:290-293` currently pins the comma form (`"+6,9 pts"`,
   `"+2,5 pts"` for `margin?.change?.formatted.es` / `onTime?.change?.formatted.es`) — these need
   the same period-decimal update before round 2 can go green, per this review's decision.

Nothing else in T-20-1 needs to change. All other approved copy shipped verbatim; the earlier
plan-review implementation note (`params.niche`) was correctly implemented; scope, owned paths and
the past-peak/under-way timing logic are sound.
