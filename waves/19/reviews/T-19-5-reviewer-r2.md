# Review of T-19-5 (round 2)

- Reviewer: reviewer on sonnet
- Author: web-engineer on sonnet
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web show 87e800d --stat` | 5 files: `src/components/digest/digest-copy.ts`, `digest-copy.test.ts` (new), `insight-card.tsx`, `src/i18n/en.ts`, `src/i18n/es.ts` — all inside the card's owned globs |
| `git -C invai-web status --short` | ` M e2e/digest.spec.ts` only, unstaged, not part of the commit (QA's uncommitted file, correctly not touched or read for content) |
| `git -C invai-web show 87e800d -- src/components/digest/digest-copy.ts src/components/digest/insight-card.tsx` | read in full; matches the report's description |
| `git -C invai-backend grep -n "D8 win\|d8Wins" src/modules/digest/detectors.ts` and read `src/modules/digest/detectors.ts:317-359` | confirmed the real wire value: **every** D8 candidate (`bestNet` and `onTime`) sends `templateKey: "D8 win"`, disambiguated only by which fact is present (`d8.net`+`d8.weeks` vs `d8.onTimeRate`) |
| Read `invai-backend/src/modules/digest/render.ts:79-88,228,258-274` (`TEMPLATES["D8 win.bestNet"/"D8 win.onTime"]`, `actionPart`'s `default` branch) | web's `digestWinText` now checks `templateKey === "D8 win"` and picks the branch from `facts` exactly like the backend's own email renderer (`factOf(i,"d8.net")` truthy → best-net-week, else on-time), same fact ids (`d8.net`, `d8.weeks`, `d8.onTimeRate`) |
| Diffed `en.ts`/`es.ts` win text against `render.ts` `TEMPLATES` | `digest.win.bestNetWeek` = "Your best net week in {{n}} weeks: {{net}}" / "Tu mejor semana neta en {{n}} semanas: {{net}}"; `onTimeRecord` = "Your best on-time rate yet: {{rate}}" / "Tu mejor tasa de envíos a tiempo: {{rate}}" — **verbatim match**, both languages, to `render.ts`'s `"D8 win.bestNet"`/`"D8 win.onTime"` |
| Read `invai-backend/src/modules/digest/detectors.ts:12-31` and `render.ts:142-149` (`COST_LINES`, `costLine.*` table) vs web's new `COST_LINE_KEYS`/`digest.costLine.*` | all 8 values (`channelFees`, `blankCost`, `transferCost`, `labelCost`, `packagingCost`, `laborCost`, `adsCost`, `refunds`) and both languages' words match the backend's own email table exactly |
| `grep -rn "designMilestone\|win.best_net_week\|win.on_time_record\|win.design_milestone" invai-web/src` | only remaining hit is a negative test case in `digest-copy.test.ts` proving the old invented key now falls back to generic — the dead key and copy are fully removed |
| Red-for-the-right-reason: copied `digest-copy.test.ts` onto round-1 head `9b8a69e` (symlinked `node_modules`, scratch dir, deleted after) | `./node_modules/.bin/vitest run digest-copy.test.ts` → 6 of 9 tests fail on the old code (`"Review blankCost costs"` instead of `"Review blank costs"`; `sourceDateText` throws `Invalid Date` because the old signature took no `lang` param and the test calls the new 4-arg signature — both are real, not just cosmetic, signature/behavior changes) |
| `invai-web`: `node_modules/.bin/vitest run src/components/digest/digest-copy.test.ts` at HEAD | `Test Files 1 passed (1)`, `Tests 9 passed (9)` |
| `pnpm typecheck` | `tsc --noEmit` clean |
| `pnpm lint` | `biome check .` — "Checked 166 files in 112ms. No fixes applied." |
| `pnpm test` | `vitest run --passWithNoTests` — "Test Files 17 passed (17)", "Tests 97 passed (97)" (was 16/88 at r1; +1 file, +9 tests, matches the report) |
| `VITE_API_URL=http://localhost:3000 pnpm build` | "✓ built in 1.44s", same pre-existing >500KB chunk warning (`env`/`index`/`BarChart`), not from this card |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web origin/main` | hits are only in QA's uncommitted `e2e/digest.spec.ts` (`test.fail` markers removed / one `test.skip`) — not this card's commit; `removed=0, added=36` assertion lines overall |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 2 Digest page — "the win" | **yes (fixed)** | `DigestWinCard` now names the real number/rate for a real `"D8 win"` insight in both languages, sourced from the backend's own `facts[].formatted`; falls back to the generic line only for a non-`"D8 win"` templateKey or a `"D8 win"` with neither fact |
| 7 en/es, no raw keys | **yes (fixed)** | D3's `review_costs` now renders a plain word (`costLineLabel()` + `digest.costLine.*`, both languages) instead of the raw `CostLine` enum identifier; an unrecognized cost-line value still gets a real English word via `COST_LINE_KEYS` fallback, never the bare identifier |
| All other criteria (1, 3-6) | yes | unchanged since r1 (`T-19-5-reviewer-r1.md`); this round touched only `digest-copy.ts`, `insight-card.tsx`, `en.ts`, `es.ts` |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git show 87e800d --stat` lists exactly `src/components/digest/**` and `src/i18n/{en,es}.ts`, both inside the card's owned globs)
- [x] Nothing outside scope — the Market-watch empty-`{{channels}}` finding from the product-designer's review is correctly diagnosed to backend code (`invai-backend/src/modules/digest/render.ts:282`, not owned by this card) and reported, not edited; confirmed by reading that file and by T-19-3's own round-2 fix (`cfe1098`, reviewed separately) landing exactly there
- [x] Tests exercise the behavior, and none were weakened — new `digest-copy.test.ts` is the only test file touched, it is all additions (`removed=0, added=36`), and it fails on the pre-fix code for the right reason (see Evidence)
- [x] Tenancy / idempotency / money / en-es — no server code in this diff; both new copy paths pull their numbers from the backend's own pre-formatted `facts[].formatted`/cost-line words rather than recomputing, so money/rate formatting stays server-controlled; en/es complete and verbatim to the backend's own tables
- [x] Decisions recorded where needed — no new cross-cutting decision needed; the report's disclosure of the backend `render.ts:282` bug (found while fixing this round) is exactly the "report, don't edit" behavior `respect-ownership` requires, and T-19-3's own commit fixes it

## Optional notes (not blocking)
1. `e2e/digest.spec.ts` remains uncommitted and modified in the working tree throughout this round, as it was at r1 (QA-owned, out of scope for this card). Confirmed again it was not staged or committed by this author.
2. The r1 optional note on `sourceDateText`'s browser-locale bug is now fixed as a side effect of this round's work (it now takes `lang` and formats from `i18n.language`); the separate, still-open `format.ts` `formatDay()` instance is unchanged and correctly left as a known gap for whoever owns that file.
