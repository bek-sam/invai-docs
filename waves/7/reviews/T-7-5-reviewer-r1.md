# Review of T-7-5 (round 1)

- Reviewer: reviewer on Claude Sonnet 5
- Author: web-engineer on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-ui`: `pnpm typecheck` | clean (`tsc --noEmit`, no output) |
| `invai-ui`: `pnpm lint` | "Checked 54 files in 50ms. No fixes applied." |
| `invai-ui`: `pnpm test` | 24 passed (5 files) |
| `invai-ui`: `pnpm build` | no `build` script in this package (library repo; not part of its DoD) |
| `invai-web`: `pnpm typecheck` | clean — the 8 pre-existing failures the report flagged are gone (folded in by `3f24b82`, verified by re-running against current HEAD) |
| `invai-web`: `pnpm lint` | "Checked 143 files in 227ms. No fixes applied." |
| `invai-web`: `pnpm test` | 76 passed (14 files) |
| `invai-web`: `pnpm build` | `vite build` succeeds (large-chunk warnings only, pre-existing) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-ui 178c829` | "Result: no hits" (0 removed / 5 added assertions) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web 073c53f` | "Result: no hits" (0 removed / 0 added — this card's own commit touches no test file) |
| `git show --stat` on `6aa9b99`, `c29c60a`, `74fa8b4`; `git diff --stat 178c829..c29c60a` | files listed below, cross-checked against owned + granted paths |
| Grep for hard-coded English in the owned components and web error paths (`grep -noE '"[A-Z][a-zA-Z ]{3,}"' ...` on `data-table.tsx`, `app-shell.tsx`, `pin-pad.tsx`, `relative-time.tsx`, `money.tsx`, `command.tsx`, `file-drop.tsx`, `lib/errors.ts`, `routes/signup.tsx`) | every hit is a `t()`/`tr()` fallback-default argument, not a rendered literal; confirmed each key exists in both `en.json`/`es.json` (ui) and `en.ts`/`es.ts` (web) with a real Spanish translation, not an English copy |
| Grep of `nav.gangSheets` / `channels.mock` in `en.ts`/`es.ts` | `gangSheets`: "Gang sheets" / "Hojas de prensado"; `mock`: "sandbox" / "entorno de prueba" — both now genuinely different strings, not identical copies |
| Grep of `onRowClick` usages in `invai-web` (7 call sites: drafts, products, blanks, purchase-orders, vendor inbox, sheets, profit) and their column defs | in every case the first non-checkbox column's `cell` renders plain text/`<span>` — no nested button, link, or other interactive element ends up inside the new activator `<button>` |
| OKLCH→sRGB→WCAG contrast re-derivation (by hand, not axe) for `--color-success`/`--color-success-foreground` and for the many `text-success` usages against `--color-background`, light and dark | see Checks — all four pairings pass AA |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Table rows: real link/button, keyboard reachable, accessible name | Yes | `data-table.tsx`: the first non-checkbox cell renders a native `<button type="button">` wrapping the cell's own content when `onRowClick` is set; native focus + Enter/Space activation, accessible name = the cell's visible text. Checked all 7 `onRowClick` sites in `invai-web` — none nest another interactive element in that column, so no button-in-button. `<tr>` onClick stays as a mouse-only convenience; the activator button's `onClick` calls `e.stopPropagation()` so the click isn't double-fired. |
| 2. Skip link | Yes | `app-shell.tsx`: `<a href="#app-shell-main">` is the first element in the tree, visually hidden until focused (`sr-only focus:not-sr-only ...`), targets `<main id="app-shell-main" tabIndex={-1}>`. |
| 3. Locale (`RelativeTime`/`Money`) | Yes | `formatMoney`/`formatRelativeTime` now default to `i18n.language`, with an explicit `locale` param the components pass from `useTranslation()`. New tests assert the exact AC example (`formatRelativeTime(..., "es")` → `"hace 4 semanas"`) plus a future-tense case and `formatMoney(1234, "USD", "es") === "12,34 US$"`. |
| 4. No English left / untranslated Spanish fixed | Yes | Every remaining capitalized string in the owned files is a `t()`/`tr()` fallback default with a matching real key in both locale files (verified above). `nav.gangSheets` and `channels.mock` are no longer character-identical between `en.ts`/`es.ts`. |
| 5. Toasts suppressed only where a dialog explains | Yes | `main.tsx`'s `DIALOG_EXPLAINED_CODES` = exactly `PLAN_LIMIT_REACHED`, `PAYMENT_REQUIRED`, `CREDITS_EXHAUSTED`, `EMAIL_NOT_VERIFIED`. Traced both dialog hosts: `UpgradePromptHost` (covers the first three via `upgradeReasonOf`) is mounted unconditionally inside `BillingBanner` → `AppFrame` → `_app` layout (not gated on `canRead`), and `VerifyEmailPromptHost` (covers the fourth) is mounted unconditionally inside `VerifyEmailBanner` → `_app`, regardless of the user's verified state. No suppressed code lacks an always-mounted dialog. |
| 6. Axe: 0 serious/critical on 5 pages | Trusted (not re-run) | Per the skill, axe re-run is optional; trusted the author's before/after counts (1/2/0/0/1 → 0/0/0/0/0) since the code changes plausibly cause exactly those fixes (see Checks for the contrast math I did verify independently). |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat 178c829..c29c60a`, `git show 74fa8b4`) — `invai-ui`: `app-shell.tsx`, `file-drop.tsx`, `money.tsx`/`.test.ts`, `relative-time.tsx`/`.test.ts`, `command.tsx`, `data-table.tsx`, `pin-pad.tsx`, `en.json`/`es.json` (all owned), plus `progress.tsx`, `tabs.tsx`, `theme.css` (all explicitly granted in `wave.md`'s 2026-09-26 grant line). `invai-web`: `lib/errors.ts`, `main.tsx` (both owned). No `Badge` file touched — correct, since the fix was in the shared token, not the component.
- [x] Nothing outside scope.
- [x] Tests exercise the behavior, and none were weakened — scan script clean in both repos; new tests (`money.test.ts`, `relative-time.test.ts`) are real assertions, not loosened ones. One gap, not blocking: no new/changed automated test covers the DataTable activator-button behavior itself (AC1's riskiest change) — verified manually by the author and independently by me via the column-def grep above, but a future regression (e.g. someone nesting a button in a table's first column) wouldn't be caught by CI. Worth a follow-up unit test, not a block.
- [x] Tenancy / idempotency / money-in-cents — n/a, no server-side or money-shape changes in this card.
- [x] en/es text — confirmed both locale files have real, distinct translations for every new key.
- [x] Contrast math (independent of axe): light-mode badge pair (`success` on `success-foreground`) 3.49:1 → 4.83:1 (AA pass, 4.5:1 needed); dark-mode badge pair unchanged at ~7.23:1. Also checked the many bare `text-success` usages against `--color-background` (not just the badge pairing): light 3.70:1 → 5.11:1, dark 7.06:1 — all pass AA both before-vs-after-fix directions and in both themes.
- [x] `TabsTrigger`'s `aria-controls` sync — reviewed the effect: it captures Radix's original `aria-controls` once (`data-controls-id`), then on every render sets it back only if `document.getElementById(original)` exists (paired Trigger+Content, e.g. `shipping.tsx`), else removes the attribute (content-less filter tabs, e.g. Orders' "Todos"). Runs after each commit, so it re-adds the attribute when a tab becomes active and its panel mounts, and drops it when the panel unmounts on tab-away. No caller changes needed; correct fix for the axe `aria-valid-attr-value` finding.
- [x] Decisions recorded where needed — the invai-ui grant (`Progress`, Tabs wrapper, `Badge`/`theme.css` success color) is recorded in `wave.md`'s 2026-09-26 build log.

## Optional notes (not blocking)
- No automated regression test for the DataTable row-button behavior (see Checks above) — recommend a follow-up unit test asserting keyboard activation and that a nested-interactive-element column can't silently break it.
- Author's follow-ups (Progress/Tabs/theme.css moved from "known gap" to "fixed" in round 2; remaining `page-has-heading-one` on Order detail, the empty `shipping.tsx` action-column header, and `orders-table.tsx` not using the shared `DataTable`) are correctly scoped as out-of-owned-files or below-the-bar and left as follow-ups rather than fixed here.
- Flagging one item for the product-designer's copy review: `nav.gangSheets` was translated to "Hojas de prensado" to match `invai-ui`'s own key, but `invai-web`'s `es.ts` uses the untranslated loanword "gang sheets" in roughly a dozen other strings (subtitles, dialog titles, table headers). The fix is correct per AC4 (the two values were identical before), but it now creates a terminology split within the same app.
