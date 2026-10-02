# Review of T-26-5 (round 1)

- Reviewer: product-designer on Sonnet 5
- Author: web-engineer (per card; commit co-authored "Claude Opus 5.5")
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `cd invai-web && pnpm typecheck` | pass, 0 errors |
| `cd invai-web && pnpm lint` | pass, 1 pre-existing warning unrelated to this diff (csv-import test file) |
| Read 6 screenshots in `/tmp/t265/` | all 6 looked at (shot1–shot6) |
| `git -C invai-web show --stat 66ab0cb` | 9 files, matches card's owned paths |
| Manual contrast calc, `--color-warning` oklch(0.75 .16 80) vs white | 2.26:1 (fails AA 4.5:1 for small text) |
| Read `invai-ui/src/components/button.tsx` | `disabled:pointer-events-none` on all Button variants |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 nav entry, hidden for floor, preselect from design | yes | `nav.ts:210`, `designs.$designId.tsx` link, report's refused-case exercise |
| 2 pick design, searchable, thumbnails | yes | shot5 |
| 3 analysis, sample label, colors, contrast warnings | yes | shot1 (warnings), code `analysis.source === "mock"` → "Sample analysis" badge (not in crop, confirmed in code at line 286) |
| 4 choose, live estimate, generate disabled with reason | **partial** | shot1 (estimate shown); the "reason" is a `title` attr on a `disabled:pointer-events-none` button — see blocking #1 |
| 5 results grid, plain-word failures, polling | yes | shot2/3, labels.ts messages match spec examples closely |
| 6 approve/reject/zip/attach, unapproved blocked with reason | yes | `photos.needsApproval` visible text (line ~659), report's live exercise |
| 7 creditKind i18n | yes | not independently re-grepped, trust report + en/es diff stat |
| 8 error mapping | yes | `photoErrorMessage`/`labels.ts` covers all 10 reasons + cap, plain sentences |
| 9 en/es, light/dark, 390px, keyboard, alt text | **partial** | dark shot3 good; alt text from analysis confirmed (`alt={image.altText ?? ""}`); **390px grid is 2 columns, not 1** — see blocking #2; choose-step and pick-step were not screenshotted at 390px, so wrapping there is unverified (gate should take them) |

## Blocking findings
1. `invai-web/src/routes/_app/listing-photos.tsx:531-540` — the Generate button's credits-short reason is passed only via the native `title` attribute, and the shared `Button` component (`invai-ui/src/components/button.tsx:7`) applies `disabled:pointer-events-none` to every disabled button. `pointer-events: none` suppresses hover entirely, so this `title` tooltip can **never** appear for anyone — mouse, keyboard or screen-reader user. A shop user with a credit shortfall sees a greyed-out "Generate" button with no way to learn why, failing AC4's "disabled with the reason" and the plain-language-copy rule ("every error says what happened and what to do next"). Fix: render the shortfall as visible text near the button (same pattern already used for `photos.needsApproval`), not a tooltip on a disabled control.
2. `invai-web/src/routes/_app/listing-photos.tsx:160,674` — both grids use `grid-cols-2` at the base breakpoint (no `grid-cols-1`), so at 390 px the results grid renders **2 columns** (confirmed in shot4/shot6), not the "one column" the card's AC9 explicitly requires. Not a horizontal-scroll bug, but it is a written, specific, unmet acceptance criterion: images and their Approve/Reject rows are cramped at phone width, which is exactly the width an owner checks from. Fix: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4` (or similar) so 390 px gets one column as specified.

## Checks
- [x] Only owned paths changed (`git diff --stat` matches card's owned globs)
- [x] Nothing outside scope
- [ ] n/a — I did not re-run the test suite or scan for weakened tests (primary `reviewer` covers this; my scope per the card is UX/copy/a11y)
- [x] en/es text present for all new strings I sampled (copy reads natural, plain-language, matches glossary; no internal words — "queued"/"rendering" reuse an existing app-wide pattern, not new jargon)
- [ ] n/a — tenancy/idempotency/money not in my review scope for this card

## Optional notes (not blocking)
- `--color-warning` as a *text* color (`text-warning`, used here for contrast warnings and `design_larger_than_print_area`/`illustration_not_photo`-adjacent warn-severity messages) measures ~2.26:1 against white, well under WCAG AA's 4.5:1 for small text. This is a pre-existing `invai-ui` token already used this way in 20+ other `invai-web` files, not something this card introduced — I'll pick it up as an `invai-ui` follow-up rather than blocking this card on inherited design-system debt.
- The custom "Attach to AI listing draft" listbox (`role="listbox"`/`role="option"` on plain buttons, lines ~838-855) is fully keyboard-operable via Tab/Enter but doesn't implement roving-tabindex/arrow-key nav per the ARIA listbox pattern. Minor; worth a shared `invai-ui` combobox/listbox component if this pattern repeats.
- `photos.select` button text ("Select {{name}}") has no truncation; a 40-character design name could wrap the button inside the narrow 390px/2-col grid cell. Not exercised in the screenshots (demo names are short), flagging as an edge case to check.
- Nice touches worth keeping: analysis + choose combined on one scrollable page rather than a forced wizard click-through reads clearly in shot1 and is faster for repeat use; "Recent sets" list on the pick screen; check-failure copy ("Product fills 78% (Amazon needs 85%)", "Drawn illustration: Amazon wants a photo for the main image") matches the spec's own example sentences almost verbatim.
- Step-1 and step-3 screens were not screenshotted at 390 px (budget was 6 shots); the gate should take them given finding #2 touches the same grid class pattern used at line 160.
