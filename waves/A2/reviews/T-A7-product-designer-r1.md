# Review: T-A7 Operations, Inventory health, Designs lifecycle, Today actions panel — round 1

Reviewer: product-designer on Claude Sonnet 5
Author: web-engineer on Claude Opus 5.5

## Verdict: approve

Inputs only: the task card, `git -C invai-web show e80298e a33ffc7 e206b76`, the author's report, and the 22
screenshots in `.e2e-out/web/T-A7/`. No stack started.

## The tech lead's question — "~$2,423.28 de impacto"

Matches `today-es-1440-light.png`. This is the digest's own `digest.impact` key (`"~{{amount}} de impacto"`),
reused unchanged from `insight-card.tsx` per the card's instruction ("Reuse `digestActionText` for the panel
wording") — not introduced here. The chip doesn't overflow or wrap in either language at 1440 or 390 px. It
does pair an approximation mark ("~") with to-the-cent precision, which slightly undercuts the "estimate"
framing, but that's a pre-existing digest-copy decision, not this card's to fix. Non-blocking.

## Five full-width buttons, same weight

`today-en-1440-light.png`/`-es-1440-light.png`: all 5 actions render as identical full-width `buttonVariants({size:"lg"})`
(brand primary, teal) regardless of $ impact — "Ship 46 overdue orders" ($2,423) looks exactly like "Reorder
…Pepper M" ($67). Order alone (highest impact first) carries the ranking; nothing else does. Acceptable for
v1 — nothing here is wrong, urgent, or misleading — but worth a follow-up: either de-emphasize the smaller
reorder actions (outline/secondary) or give the top action more visual weight, so a glance shows what matters
most, not just a list order a tired owner has to read top to bottom. Non-blocking.

## The two kit gaps the builder raised

1. **`PageHeader` actions clip at 390 px** — confirmed, and it's worse than the builder's note suggests:
   `today-en-390-light.png`/`-es-390-light.png` cut "Buy labels"/"Comprar etiquetas" down to "Bu"/"C",
   `operations-390-viewport-only.png` cuts "Export CSV" to "Exp…". This is a real bug (a control a user can't
   read or safely predict), but it's `@invai/ui`'s `PageHeader` (`shrink-0` wrapper), already present on the
   reviewed `/analytics/profit` page per the report — pre-existing, not a T-A7 regression. **Taking it as an
   invai-ui follow-up for myself**, not a blocker on this card.
2. **`StatCard` has no neutral/no-arrow state** — same class of gap as T-A6's finding, still open, still not
   this card's to fix (`KpiTile` in `shared.tsx` is a local copy of T-A6's own workaround, same as before).
   **Also taking as an invai-ui follow-up.**

## Findings (non-blocking)

1. **S4 — `KpiTile` label truncation at 390 px:** `inventory-en-390-light.png`/`-es-390-light.png` show stat
   labels cut with no tooltip ("Blank cost so…", "Costo de pra…", "Rotaciones(/…") — `shared.tsx`'s `<p
   className="truncate" …>{label}</p>` has no `title`. Inherited from T-A6's own `KpiTile` pattern (same file
   note says so), present in both languages, not introduced here. File alongside the two kit gaps above.
2. **S4 — "Unknown" vendor, `operations-es-1440-light.png`:** the reprint-cost-by-vendor table shows an
   untranslated `Unknown` in the Vendor column. Not found anywhere in `operations-view.tsx`'s strings — looks
   like seed/backend data (a null vendor label), not a missing i18n key in this diff. Flag to the backend
   owner if it recurs with real shop data; out of this card's owned paths.

## What I checked and liked

- **AC-B3 copy, exact:** `opsV2.lateDriversHint` en: "Which cuts of orders were more often late, not what
  caused it."; es: "Qué cortes de pedidos se retrasaron más seguido, no qué lo causó." — no "caused", stations
  named ("QC 1"), never a person.
- **Points format:** `formatPoints()` renders signed `"+18.0 pts"`/`"-18.6 pts"`, locale-aware decimal comma in
  es, "pts" never translated as a word — matches the spec's own examples.
- **AC-C1 "not enough data":** confirmed live per the report and visible in the inventory screenshots for
  small style/color groups.
- **Today panel gating:** `today-presser-en-1440-light.png` — no panel, no Analytics nav group, Today still
  loads fully for a role without `finance.read`. Matches AC-E2's refused-role requirement.
- **"Opened" indicator:** `today-action-clicked-opened.png` — check icon + green text + the word "Opened", not
  color alone (principle 5).
- **Money never splits mid-number** at 390 px es on Today/Operations/Inventory, per the report and confirmed
  in the screenshots I read.
- **Designs lifecycle badges:** `designs-es-1440-light.png` — "Aprobado"/"Creciendo"/"Bajando" badges read
  correctly, plain Spanish, color plus text.
- **Dark mode:** present in the screenshot set (`*-1440-dark.png`) for Today/Operations/Inventory.

## Evidence

- Screenshots read: `today-{en,es}-1440-light`, `today-{en,es}-390-light`, `today-action-clicked-opened`,
  `today-presser-en-1440-light`, `operations-es-1440-light`, `operations-390-viewport-only`,
  `inventory-{en,es}-390-light`, `inventory-390-deadstock-table`, `designs-es-1440-light`
- `grep -n "digest.impact" src/i18n/{en,es}.ts src/components/digest/insight-card.tsx
  src/features/today/actions-panel.tsx` — confirms the impact chip is the reused digest key, not new copy
- `grep -n "lateDrivers" src/features/analytics/operations-view.tsx src/i18n/{en,es}.ts` — AC-B3 wording
- Read `src/features/analytics/shared.tsx` (`KpiTile`, comment self-documents the T-A6-copied-not-imported
  pattern) and `invai-ui/src/components/button.tsx` (`buttonVariants` — confirms "green" buttons are brand
  `default`/`primary`, not a one-off color)

## Optional notes

- Consider whether the Today actions panel's top action (highest $ impact, especially a shipping action)
  should visually lead the other four, the next time this screen is touched.
