# Review: specs/market-signals.md — product-designer

Reviewer: product-designer · 2026-09-27
Lens: flow, screen states, copy (en/es), 390 px + a11y, invai-ui coverage

## Verdict: approve-with-changes

## Blocking

1. **Unbuildable flow — recommendation vote buttons have no wire shape.** User flow step 4 and the "Done/Not
   useful" buttons sit *inside* a streamed assistant answer, but `assistant.tsx` only carries `text_delta`,
   `tool_call` (a name-only chip) and `error`/`done` events (see `invai-web/src/routes/_app/assistant.tsx:80-90`).
   There's no per-recommendation id on the stream or the stored message for T-18-5 to bind
   `market.recommendations.vote` to. Fix: T-18-1's contract needs a `recommendations` array on the assistant
   message/stream event (id, rule, action, confidence band, evidence refs), analogous to `tool_call`, before
   T-18-5 can build the vote buttons.
2. **Niche chip UI is specified for 1 niche, but the mapper allows 2 (Step 2.2).** Flow step 5 and the copy
   row `niche.label`/`niche.change` show a single "Niche: Teacher · Change" chip. Spec needs: 0/1/2-niche chip
   states, and whether "Change" edits one chip or opens a picker for both. Without this, T-18-5 will build a
   single-niche UI that can't represent a real two-niche design.
3. **Trademark-dropped queries are invisible with no fallback copy.** Step 6.6/AC12 say a query at/above the
   trademark threshold is "never shown," but no answer text covers this case for a user who explicitly asked
   about that niche — they'll see an answer that looks like a bug ("insufficient data" for a niche they know
   is huge). Add a fixed line for this path, reusing the refusal pattern in guardrail 5, e.g.:
   - en: "I can't show market data for this. Ask about a specific design instead."
   - es: "No puedo mostrar datos del mercado para esto. Pregunta sobre un diseño específico."

## Non-blocking

- **Confidence band has no visual spec** (Step 4 "Bands", copy `band.high/medium/low`). Suggest mapping to a
  new shared `ConfidenceBadge` in `invai-ui` (tone + icon + text, never color alone: high→success, medium→
  warning, low→muted/neutral) so market-signals and the wave 19 digest render bands identically instead of
  two ad hoc treatments. Flag to T-18-5 and the wave 19 web card.
- **Staleness (`stale: true`, AC10) has no distinct UI cue** beyond the source date already required by
  guardrail 2 and a lower confidence band. That's probably enough — just confirm the source/date line is
  never omitted when `stale`, since it's the only signal the user gets.
- **Niche picker for 64 items**: a plain `<select>` (as used for `designs.template` in
  `designs.$designId.tsx:294`) is unwieldy at that size. Recommend the existing `Command`/`CommandDialog`
  (cmdk) from `invai-ui` for a searchable niche picker instead of `NativeSelect`.
- **Copy — R4 action** ("Make 1–2 new designs for the {{niche}} niche") reads a little stiff in Spanish;
  suggest: "Crea 1 o 2 diseños nuevos para el nicho {{niche}}." (matches spec; no change needed, confirming
  it's fine) — leaving as-is.
- **Glossary**: "niche/nicho", "seasonality/temporada", "sample data/datos de muestra", "confidence/confianza"
  are new shop vocabulary. Product-designer will add these to `.claude/skills/write-plain-language-copy/glossary.md`
  once T-18-5 ships, so future copy stays consistent.
- **390 px**: the assistant screen already collapses the conversation sidebar under `lg` (`assistant.tsx:104`);
  recommendation cards with two buttons per card need to stack cleanly at 390 px without truncating rule
  action text (some actions carry 2 placeholders, e.g. R1). Verify at build time, no spec change needed.
- **a11y**: vote buttons need names beyond "Done"/"Not useful" alone (e.g. `aria-label="Mark 'test $19.99 on
  Amazon' done"`) so multiple recommendations in one answer are distinguishable to a screen reader.

## invai-ui components needed by the web card (T-18-5)
- No new base component is strictly required — `Badge`, `Button`, `Command` cover it.
- Recommend (not blocking): a shared `ConfidenceBadge` (see above), reused by wave 19's Market watch block.
