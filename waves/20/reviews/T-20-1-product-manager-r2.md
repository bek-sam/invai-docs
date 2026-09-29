# Review of T-20-1 (round 2) — product-manager

- Reviewer: product-manager
- Author: backend-engineer on Opus 5.5 (T-20-1); web-engineer on Sonnet (T-20-2 r2, co-checked here); qa-engineer (acceptance-file fix)
- Co-review scope: my r1 changes-required item (drop `PTS_LOCALE`, es-US for Spanish points) plus the R1 peak-under-way fallback wording
- Verdict: **approve**

## r1 finding, closed
`invai-backend` `076dd69` does exactly what my r1 review asked (`T-20-1-product-manager-r1.md`, "T-20-1 must change"):
- `facts.ts`: `PTS_LOCALE` removed, `signedPts` now uses the shared `LOCALE[lang]` map — Spanish points render `"+6.9 pts"` / `"-6.9 pts"`, period decimal, matching AC13's already-shipped money/count/relative-percent convention. No more mixed separators in one line.
- `pure.test.ts` lines 620/637 updated to the period form.
- QA's `d6a19f1` updates the pinned acceptance assertions I flagged as blocking (`date-copy.acceptance.test.ts:290-293`, `"+6,9 pts"`→`"+6.9 pts"`, `"+2,5 pts"`→`"+2.5 pts"`) — nothing else in that file touched.
- `specs/weekly-digest.md` carries the decision in the "Change wording" note and a dated review-log line (2026-09-28), so the rule is findable outside this review thread.

Nothing else in `076dd69` changed; scope and owned paths are unchanged from round 1.

## Web es-US number fix (`invai-web` `d092a4b`), checked for scope
`digest-copy.ts`'s `localeNumber` moved from bare `es` (period grouping, "10.000") to `es-US` ("10,000"), which widens my r1 decision beyond points to plan-usage counts inside the same digest. This is authorized, not scope creep: the tech lead amended `T-20-2.md` AC4 same day ("Amended 2026-09-28 by the tech lead after the PM's T-20-1 decision... es-US throughout the digest, no mixed separators"), citing this exact review. Correct call — a digest email/page showing "31.4%" and "+6.9 pts" in `es-US` next to a plan-usage count in bare-`es` period grouping would be the same bug in a different spot. `settings/billing.tsx` is explicitly left out (separate screen, backlog follow-up), which is the right fence — no request to expand that further.

## R1 peak-under-way fallback, checked as requested
`recommendation-copy.ts`'s new branch (`p.niche ? nicheLabel(p.niche) : monthName(p.peakMonth, lang)`) fills the approved template (`specs/market-signals.md` "R1 action (peak under way; wave 20)": `"The {{niche}} season is on now..."` / `"La temporada de {{niche}} ya empezó..."`) with the peak month name instead of leaving `{{niche}}` empty. This is not new copy — it reuses the already-approved string and mirrors a pattern the backend already ships: `invai-backend/src/modules/digest/render.ts`'s `marketPart()` does the same `p.peakMonth ? monthName(...) : peak` substitution for the identical case (line ~294, `Intl.DateTimeFormat(lang === "es" ? "es-US" : "en-US", { month: "long" })`).

Rendered: **"The September season is on now. Make sure Cactus Mama is listed and in stock."** / **"La temporada de septiembre ya empezó. Asegúrate de que Cactus Mama esté publicado y con inventario."** Both read naturally as plain shop language — "the September season" and "la temporada de septiembre" are ordinary phrasing, not a template artifact. `Intl` long-format month names are lowercase in Spanish by default ("septiembre"), which is correct Spanish orthography (months aren't capitalized) — no fix needed there. The test (`recommendation-copy.test.ts`) asserts the no-double-space/no-empty-slot case directly, which is the right regression guard.

One minor gap, not blocking: the web `monthName()` (`recommendation-copy.ts`) uses bare `"es"` for the Intl locale, not `"es-US"` like the backend's `render.ts` `monthName()`. For month names this makes no visible difference (`"septiembre"` either way), so it doesn't reproduce the points/count bug — but for strict consistency with the digest's now-stated "one `es-US` locale throughout" rule, a future pass should align it. Not worth a round 3 for a difference with no rendered effect; flagging so it isn't lost.

## Verdict
**Approve.** The Spanish-points fix, the QA acceptance update, and the web es-US number widening all match my r1 decision and the tech lead's authorization; the R1 fallback wording is acceptable as shipped, reusing approved copy with no new string needed.
