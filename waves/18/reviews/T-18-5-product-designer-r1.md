# Review of T-18-5 (round 1)

- Reviewer: product-designer on Sonnet 5
- Author: web-engineer on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web show ab961f3 --stat` | 12 files, all inside T-18-5's owned paths (`assistant.tsx`, `catalog/designs.$designId.tsx`, `components/market/**`, `i18n/en.ts`, `i18n/es.ts`) |
| `git -C invai-web show ab961f3 -- src/i18n/en.ts src/i18n/es.ts` | every new key matches `specs/market-signals.md`'s copy table verbatim (chip.*, badge.sample, band.high/medium/low, vote.done/no, niche.label/change/none, R1–R5 actions en+es) |
| `git -C invai-web show ab961f3 -- src/components/market/*.tsx` | read `recommendation-card.tsx`, `confidence-badge.tsx`, `sample-data-badge.tsx`, `niche-chip.tsx`, `niche-picker.tsx`, `use-niche-taxonomy.ts` |
| `git -C invai-web show ab961f3 -- src/routes/_app/assistant.tsx src/routes/_app/catalog/designs.$designId.tsx` | wiring for mock badge, recommendation hydration on stream + reload, niche chip mount |
| Read 4 screenshots | `t18-5-assistant-en-1440-votes.png`, `t18-5-assistant-es-390.png`, `t18-5-design-niche-en-picker.png`, `t18-5-design-niche-es.png` |
| `git show ab961f3 -- src/components/market/recommendation-copy.test.ts` | unit tests cover R1–R5 fill-in, money in cents, niche label lookup, en |

## Acceptance criteria (my lens: copy, states, a11y, 390px, invai-ui use)
| # | Met? | Evidence |
|---|---|---|
| 1 Chips | Yes | en 1440 screenshot shows "Seasonality" chip; es screenshot shows "Temporada"; i18n diff adds all 4 tool labels en/es exactly as spec's chip.* row |
| 2 Starters | Yes | `marketTrend/marketPrice/marketSeason` keys added en/es, text matches spec's starter/starter2/starter3 rows exactly, alongside wave 17's 4 |
| 3 Sample badge | Yes | Screenshot shows "Sample data" / "Datos de muestra" next to the tool-chip row, not a tooltip; `SampleDataBadge` renders unconditionally on `m.mock`, plus `rec.sample` text inside each mock recommendation card (spec guardrail 3) |
| 4 Votes | Yes | `RecommendationCard` binds `vote.mutate({id: rec.id, ...})`, `aria-pressed` reflects `rec.vote` so a second tap shows stored state; reload path (`openConversation` → `hydrateRecommendations`) refetches by id from `AssistantMessage.recommendations`; `stale.note` wired verbatim from spec copy, not exercised on this seed (acceptable known gap, code path correct) |
| 5 Niche chip | Yes | `niche-chip.tsx` covers 0 (`market.niche.none` + "Pick a niche"), 1 (`Niche: X`), 2 (`Niches: X, Y`) states as one literal string matching the spec's flow-step-5 wording exactly; `NichePicker` is the existing `CommandDialog`, edits both at once, disables (not silently evicts) a third pick once 2 are chosen, Save/Cancel gate the write (a lightweight confirm before `market.niches.set`, consistent with reversible-action guidance) |
| 6 Permissions in UI | Yes | `canManage={can("market.niches.manage")}` hides "Change" only, not the whole chip; report's designer screenshot (not one of my 4, but consistent with the existing nav-gating pattern) shows no Assistant/Profit/Ad-spend nav and no page error |
| 7 Copy/layout | Yes | es-390 screenshot: no horizontal scroll, "Temporada" chip and "Datos de muestra" badge render correctly in Spanish; en-1440 and niche screenshots show light mode correctly; dark mode claimed in report, not independently re-viewed here (within my 4-screenshot budget) |

## a11y checks
- Vote buttons: accessible name includes the action text via `aria-label={t("market.vote.doneAria", "Mark '{{action}}' done", {action})}` — resolves the spec review's non-blocking note ("names beyond Done/Not useful alone") exactly as suggested, in en and es (`doneAria`/`notUsefulAria` translated, not just interpolated English).
- Confidence band: icon (`ShieldCheck`/`FlaskConical`/`CircleHelp`) + fixed text + tone, never color alone — matches CLAUDE.md principle 5 and the spec review's non-blocking note.
- Sample data badge: icon + text, not color alone.
- Niche picker checkbox rows use `CommandItem`'s built-in keyboard handling (cmdk); Cancel/Save are raw `<button>` elements rather than the kit `Button`, so they lose the kit's `focus-visible:ring-2` treatment and fall back to the browser default outline. Visible focus still exists, so this is not a blocking a11y failure — flagged below as a non-blocking cleanup.

## invai-ui component note (not blocking)
The author built a local `ConfidenceBadge` (`src/components/market/confidence-badge.tsx`) because no shared band component exists yet in `@invai/ui`, per my spec review's own non-blocking note. Correct call under the consumer rule (build locally, report it). I'll promote a shared `ConfidenceBadge` into `invai-ui` (tone + icon + text, `high/medium/low`) before wave 19's digest needs the same treatment, so market-signals and the digest don't diverge — tracked as a backlog item for me, not a card blocker here.

## Checks
- [x] Only owned paths changed (`git diff --stat` lists only `assistant.tsx`, `designs.$designId.tsx`, `components/market/**`, `i18n/en.ts`, `i18n/es.ts`)
- [x] Nothing outside scope (no `invai-ui` edit, no standalone Market screen)
- [x] Tests exercise the behavior (`recommendation-copy.test.ts`, 6 new tests); none weakened — no `.skip`, no loosened assertions, no mock of the unit under test
- [x] Copy exact match to spec table (en/es); no raw keys or English-in-Spanish in the screenshots I read
- [x] Money in cents (`formatMoney`), en/es text, no color-alone status signaling
- [x] Decisions recorded in the report (niche chip as one literal Badge string vs. per-niche chips; vote cards fetch full records via `market.recommendations.list({ids})`) — consistent with the spec's exact copy requirement, no `record-decision` needed (card-local choices)

## Optional notes (not blocking)
- Niche picker's Cancel/Save should be the kit `Button` component instead of raw `<button>`, for a consistent focus ring and to avoid a second styling system for the same control. Low priority; file as a small follow-up, not a re-review trigger.
- Confirm at build time (already claimed done in the report, not one of my 4 screenshots) that two vote buttons per card don't truncate the longer R1 action text at 390px.
