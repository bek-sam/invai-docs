# Review of T-6-2 (round 1) — product-designer co-review (UI quality)

- Reviewer: product-designer on Sonnet 5
- Author: (unattributed in report) on sonnet
- Verdict: **approve**

Scope of this co-review: AC4 ("en and es, 390px, keyboard accessible") across the two new routes
(`/production/bins`, `/production/reprints`) and the sheet-detail changes. Full cross-repo
evidence is in `T-6-2-reviewer-r1.md`; this file adds the design/i18n/a11y read specific to this
lens and doesn't re-run tsc/lint/test/build.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web diff c130bde~1 c130bde -- src/i18n/en.ts src/i18n/es.ts` | +77 lines each side |
| Diffed the two files' key sets (`grep -oE '"[a-zA-Z.]+":'` on each, sorted, `diff`) | identical — no key added to one side without the other |
| `grep -nE '>[A-Z][a-zA-Z ]{3,}<'` over `bins.tsx`/`reprints.tsx`, excluding `t(` calls | no hits — no hardcoded English JSX text |
| Read `bins.tsx`, `reprints.tsx`, and the `sheets.$sheetId.tsx` diff in full for component/pattern reuse | see below |

## En/es
Full parity confirmed (identical key sets, matched counts). Spot-checked a sample of the new
keys for both files existing and reading naturally in context (`bins.create`, `bins.archivedToast`,
`sheets.markPrinting`, `sheets.printedToast`, `reprints.reasonsByWeek`) — no placeholder or
machine-translation smell in either language. Reason strings in the new reasons-by-week table use
the existing `t(\`reprintReason.${r.reason}\`, r.reason)` lookup (`reprints.tsx:232`), the same
pattern the pre-existing reprints list column already used — not a new i18n gap.

## Layout / 390px
Both new routes are built from `Page`/`Section`/`Field` (`components/page.tsx`) and `DataTable`/
`Dialog`/`NativeSelect`/`Switch` (`@invai/ui`) — the same shared, already-narrow-viewport-audited
component set every other route in this app uses (confirmed by grep: no bespoke fixed-width
containers, no `min-w` wider than the shared table wrapper already handles, no new CSS). The
reasons-by-week chart uses `ResponsiveContainer` (recharts), which reflows with viewport width by
construction. I did not independently load either route in a browser at 390px — the DB-copy pass
in the primary review exercised these routes live but at desktop width, and no screenshots
survived to check against (see that file's optional notes) — so this is a code-level judgment,
not a pixel-verified one. Nothing in the diff suggests a narrow-viewport regression.

## Keyboard access
- Icon-only actions (bin rename/archive) carry explicit `aria-label`s
  (`t("bins.rename", "Rename")`, `t("bins.archive", "Archive")`, `bins.tsx:146`/`158`) — a
  screen-reader/keyboard user gets a real label, not a bare icon.
- Forms use `Field`+`Input` with `htmlFor`, and dialogs use the shared `Dialog` primitive
  (native focus trap/`Escape`-to-close, already relied on by every other dialog in this app).
- Filters on `/production/reprints` use `NativeSelect` — a real `<select>`, fully keyboard-
  operable and consistent with how filters are built elsewhere in this app, rather than a custom
  dropdown that would need its own keyboard handling.
- Row selection for "Print labels" (`bins.tsx`, `RowSelectionState` via TanStack Table through the
  shared `DataTable`) renders through that shared component's existing checkbox column, not a new
  bespoke selection UI — so it inherits whatever keyboard behavior `DataTable` already has
  elsewhere, rather than introducing a new one to audit.
- Same caveat as layout: no live keyboard walkthrough was done in a browser; this is a
  code/pattern read confirming no new bespoke interactive control was introduced that would need
  one.

## Design decisions in the report
The reasons-by-week report was built as a single-series "total by week" bar chart plus a plain
`week / reason / count` table, instead of a 12-series stacked bar (`REPRINT_REASONS` has 12
values). Agreed with the reasoning in the report: a legible categorical palette for 12 series
doesn't exist in this design system, and a real table is more accessible than 12 colors anyway —
this satisfies "count by reason and by week" (AC2) without inventing a wide palette that would
itself be an accessibility problem (color-only differentiation). No objection.

## Checks
- [x] En/es complete and parity-checked.
- [x] No raw English strings found in the new JSX.
- [x] 390px: no code-level indicator of a regression; not pixel-verified live (see above).
- [x] Keyboard: existing accessible shared components used throughout; no new bespoke control
  introduced that would need its own audit; not walked through live.
- [x] Decisions (reasons report shape) recorded and reasonable.

## Blocking findings
None in this lens. (The reviewer and architect co-reviews found a blocking backend
state-machine gap unrelated to UI/i18n/a11y — see `T-6-2-reviewer-r1.md`. That finding doesn't
change this verdict, which is scoped to AC4, but the card as a whole cannot land until it's
fixed.)

## Optional notes (not blocking)
- The report claims 6 screenshots were taken for this pass; none exist on disk (already logged in
  the primary review). A live 390px/keyboard pass would have been preferable to the code-level
  read above, but nothing in the diff gives a concrete reason to suspect a regression.
