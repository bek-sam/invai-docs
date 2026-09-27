# Review: specs/weekly-digest.md — product-designer

Reviewer: product-designer · 2026-09-27
Lens: flow, screen states, copy (en/es), 390 px + a11y, invai-ui coverage

## Verdict: approve-with-changes

## Blocking

1. **Market watch feedback widget is ambiguous.** AC17 says a vote on a Market watch item hits "the same
   market recommendation record" as the assistant's vote (which per `specs/market-signals.md` copy is a
   `Done`/`Not useful` **button pair**). But screens/flow step 2 and "Feedback" (item 9) give digest insights
   a **thumbs up/down + optional reason** (Not relevant / Wrong / Already knew) widget. The spec doesn't say
   which widget a Market watch item actually shows, or how a thumbs-down + reason maps onto the market
   module's `done`/`not_useful` vote. Pick one: either Market watch items render the market spec's Done/Not
   useful buttons (recommended, since it's literally the same record and keeps the two specs' vocabulary in
   sync), or define the reason→vote mapping explicitly.
2. **Missing copy: the AI-summary toggle's disabled explanation.** Screens/flow step 4 says "Write the
   summary with AI" is "disabled with an explanation while in shadow mode," but the Copy table has no string
   for that explanation — QA can't write an assertion and web can't build the row as specified. Suggest:
   - en: `settings.aiSummaryShadow` — "Turned off for now while we test AI summaries. You'll see the standard
     summary until this is ready."
   - es: "Está desactivado por ahora mientras probamos los resúmenes con IA. Verás el resumen estándar hasta
     que esté listo."
3. **Missing copy: the three thumbs-down reasons.** AC12 depends on a "not relevant" vote existing, and
   screens/flow step 2 names three reasons, but none are in the Copy table. Suggest:
   - `feedback.notRelevant` — en "Not relevant" / es "No aplica"
   - `feedback.wrong` — en "Wrong" / es "Incorrecto"
   - `feedback.alreadyKnew` — en "Already knew" / es "Ya lo sabía"

## Non-blocking

- **Digest status states are incomplete.** Only `ready`, `skipped_quiet` and (implicitly) "no digest yet for
  this shop" are covered. What does `/digests/2026-W39` show if the build job crashed instead of completing,
  or if a user opens a link before the sweep has reached that shop's hour that day? Recommend adding a
  `failed` (or just letting it retry next sweep run and treating "not found yet" as the existing empty state)
  so the page never renders a half-built digest. Not blocking since AC1–5 imply the happy path is well
  covered; flag for the tech lead to confirm with the architect (T-19-1).
- **Reuse market-signals' band copy.** Market watch shows "the confidence band" (screens/flow step 2) — reuse
  `band.high`/`band.medium`/`band.low` from `specs/market-signals.md` rather than a new digest-only string,
  so a shop that also uses the assistant doesn't see two different words for the same idea.
- **D1 wording for multiple disconnected channels.** `partial` and `D1 action` copy take a single
  `{{channel}}`. If two channels disconnect the same week, is there one line per channel or a joined list
  ("Etsy and Amazon")? Spanish "y" joining needs the same treatment. Confirm with the card owner before
  build; likely one D1 row per channel is simplest and avoids a pluralization rule.
- **Footer copy is incomplete.** Pipeline step 13 requires "why you got this, one-click unsubscribe, manage
  in Settings, InvAI's postal address," but the Copy table only has `footer.why`. Add `footer.manage` ("Manage
  in Settings" / "Administra en Configuración") and leave the postal address as a placeholder pending OI-12.
- **"Send me a preview now" rate-limit message** (AC30) should reuse the existing 429/"try again in N
  seconds" pattern already established in `invai-web/src/lib/errors.ts`'s retry handling rather than a new
  string — no spec change needed, just confirming it doesn't need a new copy key.
- **a11y**: the glance block, up to 3 actions, 1 win and Market watch stack a lot onto one page at 390 px.
  Confirm action buttons (e.g. "Ship 4 overdue orders") wrap onto two lines rather than truncate, and keep
  each at 44 px min height per InvAI's touch-target rule.
- **Glossary**: "digest/resumen semanal," "steady week/semana estable," "on-time rate," and "act on/actuar"
  are new or reused shop vocabulary; product-designer will confirm these against
  `.claude/skills/write-plain-language-copy/glossary.md` at build time.

## invai-ui components needed by the web card (T-19-5)
- No new base component required if Blocking #1 resolves toward reusing the market spec's Done/Not useful
  buttons; `Badge`, `Button`, `StatCard` (for the glance block, same pattern as Today's `StatGrid` in
  `invai-web/src/routes/_app/index.tsx:107-200`), and `EmptyState` (for the steady-week / paused states)
  already cover this screen.
- If Blocking #1 resolves toward a distinct thumbs+reason widget, that's a genuinely new pattern (not used
  anywhere in web today) and should come to product-designer as an `invai-ui` component request before
  T-19-5 starts, not be built locally in `invai-web`.
