# Wave 20 plan review — product-manager

Reviewer: product-manager. Scope check of `invai-docs/waves/20/wave.md`, T-20-1..5, `QA-acceptance.md` against
`invai-docs/product/scope.md` and wave 19 gate issues 1–6.

## Verdict: **approve with changes**

The 5 cards, scope refs and QA-acceptance step are sound and evidence-backed (every card traces to a real
backlog row — B-136, B-137, B-140, B-141, B-71, B-106, B-47, B-116 — each with a source: a wave 18/19 gate
issue or a dated `team/lessons.md` row). Wording rule approved as written, with one implementation note added
below. Two small non-blocking required changes.

## Scope check

| Card | Scope ref | Valid? |
|---|---|---|
| T-20-1 | `always-in-scope: bug` → `scope.md#mvp-in` items 14/16/17, `#market-signals`, `#weekly-digest` | Yes. B-136/137/140/141 are bugs in shipped items 16 (market signals) and 17 (weekly digest); Today alert text is item 14. |
| T-20-2 | `always-in-scope: bug` → `#weekly-digest` (item 17) | Yes. |
| T-20-3 | `always-in-scope: reliability` | Yes. Matches "Reliability and observability needed to run pilots safely" and `CLAUDE.md` rule 8 (idempotent side effects); B-71 sourced from `build/audit-2026-09-24.md` A-BE. Test-only, no product code touched — correctly out of my remit beyond scope-ref sanity. |
| T-20-4 | `always-in-scope: security` | Acceptable, but it's the loosest fit of the five: this is an internal agent-team control (write-path guard, push-flag parsing), not a shop-facing security finding. It's covered by the "Security findings and incidents" bucket only because B-47/B-116 trace to real near-miss incidents in `team/lessons.md` (2026-09-27). Not a required change — just flagging that this category shouldn't become a blank check for team-tooling work; if a future card wants "security" as its scope ref without a lessons-row incident behind it, send it back. |
| T-20-5 | `always-in-scope: bug` → `#mvp-in` item 14 (demo mode) | Yes. |

Card count: 5 (T-20-1..5), plus QA-acceptance correctly marked "not a card" for wave step 3. Within the
5-card/wave limit. Nothing in any card's acceptance criteria reaches outside its scope ref — I checked each
"Out of scope" line and found no scope creep (T-20-1 correctly excludes web changes and the market engine's
detrending; T-20-3 correctly excludes product fixes; T-20-5 correctly excludes `dev.sh` and the runbook text).

## Wording rule — decided

**Approved as written**, with the digest "change.pts / unchanged" rule clarified (it applies only to
`marginPct` and `onTimePct`; every other metric keeps its existing relative-percent format — the plan text
didn't say that explicitly, so I made it a spec rule rather than leaving it to guesswork) and one
implementation note for T-20-1: `designRules()` in `invai-backend/src/modules/market/rules.ts` sets the R1
recommendation's own `niche` field to `null` (line 121; that field is the cross-design pointer R4 uses, not
the design's niche name). The "peak under way" wording needs `{{niche}}`, so T-20-1 must add
`params.niche = f.niche` (the value is already on `DesignFacts`, line 61) to R1's draft — otherwise the string
renders with an empty niche. This is a one-line implementation detail inside T-20-1's own owned path, not a
wording change; I flag it so it isn't missed during the build.

Final wording (unchanged from `wave.md`, now also recorded in the specs — see below):

1. **Past peak.** An R1 item whose act-by date is before the digest week's end (digest) or before today in
   the shop time zone (assistant, market list) is not shown and not emitted.
2. **Peak under way.** R1: "The {{niche}} season is on now. Make sure {{design}} is listed and in stock." /
   "La temporada de {{niche}} ya empezó. Asegúrate de que {{design}} esté publicado y con inventario." No
   act-by date shown.
3. **Points, not relative percent.** `marginPct` and `onTimePct` changes render as points, one decimal:
   "+6.9 pts" / "+6,9 pts". Any metric's zero change renders "unchanged" / "sin cambio", no arrow, neutral
   color. All other metrics keep their existing relative-percent change format.
4. **Mock outside source date.** `asOf` = end of the last complete ISO week (UTC), never a future date;
   rendered "week ending Sep 27" / "semana al 27 sep".

## Specs updated (my path, done)

- `invai-docs/specs/market-signals.md`: added the R1 timing rule under Step 5 (drop past-peak items, use the
  peak-under-way wording while today is in the peak month, and the `params.niche` note); two Copy rows, "R1
  action (peak under way; wave 20)" and "source.weekEnding (wave 20)"; a 2026-09-28 Review log line.
- `invai-docs/specs/weekly-digest.md`: two Copy rows, `change.pts` and `change.unchanged`, plus a "Change
  wording" note scoping `change.pts` to `marginPct`/`onTimePct` only; updated the "market item (reused)" row to
  point at the two new market-signals.md rows; a 2026-09-28 Review log line.

I did not touch item 4 (mock source date) as a new copy row beyond `source.weekEnding` — "week ending {{date}}"
was already the documented convention (market-signals.md Step 6, guardrail 2); wave 20's fix is the `asOf`
computation and locale-correct date formatting, not new wording.

## Required changes (non-blocking, for the tech lead to fold in)

1. T-20-1's card should note the `params.niche = f.niche` fix above so AC2 doesn't silently ship with an empty
   `{{niche}}`.
2. T-20-2's AC2 should reference that `change.pts`/`change.unchanged` apply only to `marginPct` and
   `onTimePct` (now spelled out in `weekly-digest.md`'s Copy section) so the web glance grid doesn't apply
   points formatting to other metrics (revenue, orders, etc.) by mistake.

Neither blocks batch 1 from starting. Architect review is still pending per `wave.md`.
