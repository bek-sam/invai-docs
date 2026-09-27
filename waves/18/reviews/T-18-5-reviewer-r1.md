# Review of T-18-5 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: web-engineer on Sonnet 5 (Job 2 of the report; Job 1 was the T-18-1 consumer co-review, not reviewed here)
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web log --oneline origin/main..HEAD` | `ab961f3` (T-18-5) + `01ec8cb` (QA's own commit, not reviewed here) |
| `git -C invai-web diff --stat origin/main..HEAD` (and `git show ab961f3 --stat`) | 12 files, all inside T-18-5's owned globs: `assistant.tsx`, `catalog/designs.$designId.tsx`, `components/market/**` (new), `i18n/en.ts`, `i18n/es.ts`; the 13th file (`e2e/market.spec.ts`) is QA's own commit, not `ab961f3` |
| `pnpm typecheck` (invai-web, at `ab961f3`) | clean |
| `pnpm lint` (`biome check .`) | "Checked 154 files in 107ms. No fixes applied." |
| `pnpm test` | "Test Files 16 passed (16); Tests 88 passed (88)" — matches the report |
| `VITE_API_URL=http://localhost:3171 pnpm build` | built in 1.42s; only the pre-existing >500kB chunk warning |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web origin/main` | "Result: no hits" (removed=0, added=55 assertions; no skip/only/mock-of-unit-under-test/snapshot changes/config loosening) |
| Own API on port 3171 (`invai_t18_rev_18_5`, a migrated copy of dev `invai`, `MIGRATION_DATABASE_URL`/`DATABASE_URL` set, `WEB_ORIGIN=http://localhost:5210`) + own worker on Redis DB 10 | worker log: `market signals computed` for 5 shops, Desert Bloom `designs:40, signals:639, recommendations:13` |
| `curl` `market/recommendations/list` as owner | 3 `R1` recommendations, `mock:true`, full `params`, `sources` |
| `curl` `market/recommendations/vote` twice, same id/vote | identical `votedAt` both times → idempotent |
| `curl` as `designer@`: `market/recommendations/list` | `403 FORBIDDEN "Missing permission finance.read for market.recommendations.list"` |
| `curl` as `designer@`: `market/niches/set` | `200`, succeeds (has `market.niches.manage`) |
| Browser (Playwright script, own scratch file, deleted after use), `vite preview --port 5210` on the freshly rebuilt `dist/` | see screenshots below |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Chips | Yes | Live browser: "Seasonality" chip (en) and "Tendencia del mercado" text confirmed present in es run; i18n diff adds all 4 tool labels en/es exactly matching spec's `chip.*` row |
| 2 Starters | Yes | `assistant.starter.marketTrend/marketPrice/marketSeason` added en/es alongside the 4 wave-17 starters; clicked "When should I get ready for the holidays?" live and it fired |
| 3 Sample badge | Yes | Live screenshot: "Sample data" badge sits next to the tool-chip row (not a tooltip); es run: body text contains "Datos de muestra" |
| 4 Votes | Yes | Live: vote cards rendered from `tool_result.recommendations` with band badges and Done/Not useful; clicked Done → `aria-pressed="true"`; reloaded the page and reopened the same conversation from the sidebar → `aria-pressed="true"` still, i.e. bound to the stored id via `AssistantMessage.recommendations` + `list({ids})`, not re-voted |
| 5 Niche chip | Yes | Live: design "Arizona Est. 1912" shows "Niche: Teachers · Change"; opening the picker shows the pre-selected niche checked, grouped by family ("Work and roles"), counter "1/2"; matches AC32's 0/1/2 states and one shared picker |
| 6 Permissions in UI | Yes | `designer@` gets `FORBIDDEN` on `market.recommendations.list` and on `ai.assistant.ask` (report; matches "no access, as today"); `designer@` succeeds on `market.niches.set` (has `market.niches.manage`) — matches spec AC24 exactly |
| 7 Copy/layout | Yes | en/es structural key diff (`market.*`, `assistant.*` blocks) is 1:1 between `en.ts` and `es.ts` (checked with a key-only diff, zero mismatches); no raw keys or English seen in the es screenshots (own run + report's) |

## Blocking findings
None.

## Send-button `disabled={!input.trim()}` removal — judged, not blocking
`src/routes/_app/assistant.tsx` (form `onSubmit`, `Textarea` `onKeyDown`, and `ask()`): a blank/whitespace-only send still no-ops, both from the button and from Enter — `ask()` trims and returns early (`const message = text.trim(); if (!message || streaming) return;`) before any state change, so nothing observable happens on an empty send either way. Removing `disabled` only changes whether the button *looks* clickable when the box is empty; it does not let a blank message through, and the button keeps its `aria-label` and keyboard focusability. This is a reasonable, honestly-disclosed trade for QA's `askStarter` polling helper (which never types into the textarea). Non-blocking; a small future improvement would be `aria-disabled` (visual/AT signal without breaking QA's polling by button state) but that is not required by any acceptance criterion here.

## Checks
- [x] Only owned paths changed (`git show ab961f3 --stat`; QA's `e2e/market.spec.ts` is a separate commit, not this card's)
- [x] Nothing outside scope — no `invai-ui` edit (a local `ConfidenceBadge` was built per the consumer rule and reported for the design system to promote, matching the product-designer's own spec-review note), no standalone Market screen, no digest work
- [x] Tests exercise the behavior, and none were weakened — `scan-test-weakening.sh` found no hits; `recommendation-copy.test.ts` (6 new tests) asserts real interpolated output (design name, blank, channels, price in cents formatted, niche label), not tautologies
- [x] Tenancy: n/a (web-only card; every call goes through the already-reviewed contract procedures). Idempotency: vote re-verified idempotent live (same `votedAt` on a repeat vote). Money in cents: `recommendation-copy.ts` uses `formatMoney(cents, ...)` throughout, never divides/rounds. en/es text: verified structurally complete and, live, rendered correctly in both languages with no raw keys
- [x] Decisions recorded in the report and judged reasonable: niche chip as one literal `Badge` string (matches spec's exact copy and QA's literal-text assertions), vote cards fetching full records via `list({ids})` (needed for the fixed action copy, capped at ≤3 per turn), `vite preview` instead of `vite dev` for manual verification (documented, defensible, not a code change)

## Optional notes (not blocking)
- Agree with the product-designer's note: `NichePicker`'s Cancel/Save should be the kit `Button` for a consistent focus ring instead of raw `<button>` elements. Low priority.
- The four QA-harness/test-fixture gaps the author found and routed (the pre-existing `net::ERR_ABORTED` on every streamed `ai.assistant.ask`, `askStarter`'s non-exact locator colliding with sidebar history, `loginAs` not accepting "Correo" once the locale is set to Spanish before login, and the niche e2e test's unconditional 2-pick assumption) are all outside this card's owned paths and were reproduced and verified directly rather than by editing QA's files — correct handling per `respect-ownership`. None block this card.
