# Review of T-20-2 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: web-engineer on Sonnet 5
- Commit reviewed: `invai-web` `f59438f` (base `f5af662`, QA acceptance)
- Verdict: **changes-required** (1 blocking finding) + **one question for the tech lead / PM** (AC4 vs the PM's es-US decision, below) that must be answered before round 2

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` (invai-web, Node v24.21.0) | `tsc --noEmit`, exit 0 |
| `pnpm lint` | `Checked 167 files in 259ms. No fixes applied.` |
| `pnpm test` | `Test Files 17 passed (17)`, `Tests 103 passed (103)` |
| `pnpm build` (no env) | fails in `vite.config.ts`: "VITE_API_URL must be set to build for production" (pre-existing config guard, not this diff) |
| `VITE_API_URL=http://localhost:3000 pnpm build` | `✓ built in 2.89s` (only the pre-existing >500 kB chunk warning). `dist/` removed afterwards (gitignored; disk is at 98%) |
| New tests vs base: `git archive f59438f~1` into scratch, copied the new `errors.test.ts` + `recommendation-copy.test.ts`, `vitest run` | `2 failed | 13 passed`: the FORBIDDEN test and the R1 under-way test fail on the old code, so they prove AC3/AC5. The `digest-copy.test.ts` additions import new functions, so they fail on base by construction |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web f59438f~1` | no deleted tests, skips, mocks, snapshot or config changes; `removed=1 added=16` assertions. The one removed line is `errors.test.ts`'s FORBIDDEN pass-through `toMatchObject({… message: "Missing permission"})`, which AC3 deliberately reverses; it is replaced by stronger assertions (see note 3) |
| `node -e` Intl probe (Node 24 ICU) | `es-MX` short date: `lun 21 de sep`; `es-US`: `lun, 21 de sept`; NumberFormat `es`: `1950 10.000`; `es-US`: `1,950 10,000`; points `es-US` `+6.9`, `es` `+6,9`; money `es-US` `$1,956.37` |
| `git -C invai-ui status --short`; read `invai-ui/src/app/stat-card.tsx:41,59-71` | clean; `deltaDirection = "up"` default and the arrow is drawn whenever `delta` is set (no "none" state) — the local `GlanceTile` claim is true |
| Backend payload compare: `git -C invai-backend show bfae180 -- src/modules/digest/build.ts`, `facts.ts:84-113`, `render.ts:289-302`, `market/rules.ts`, `market/compute.ts:914,1013` | see AC2, AC5 and finding 1 |
| Looked at all 4 screenshots in `reports/shots/t20-2-*` | es 390 heading "Semana del lun 21 de sep", glance "+3,3 pts" (pre-PM-decision backend) and "sin cambio" with no arrow; en 1440 "+3.3 pts"/"unchanged"; office@ "No access / You don't have access to this page. Ask the owner."; es plan usage "387 de 10.000 pedidos … Te quedan 1950 créditos de IA" next to "$1,956.38" and "~652,08 US$ de impacto" |

Not re-run: QA's `e2e/digest-dates.spec.ts` against a live API (needs a DB copy with a rebuilt digest; disk at 4 GB free). The report states 6/7 pass and the failing one targets `/settings/billing`; I judged AC4 from the code, the Intl probe and the screenshot instead.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Spanish heading, app language not browser locale | Yes | `digest-copy.ts` `weekOfLabel()` builds a local `Date(y, m-1, d)` and formats with `Intl.DateTimeFormat(es ? "es-MX" : "en-US")`; used in `digests/index.tsx` and `$weekKey.tsx` (both `formatDay` calls replaced). Probe: "lun 21 de sep" (card example omits "de"; matches the backend's `SHORT_DATE_LOCALE` es-MX precedent). Screenshots es 390/en 1440 |
| 2 Points and unchanged | Yes | Web renders `item.change.formatted[lang]` verbatim — it never reformats the backend string, so T-20-1 r2's switch to "+6.9 pts" in Spanish flows through with no web change and no web test pins the comma. Arrow: `glanceChangeDirection(changePct)` is `null` for `null`/`0`; backend `build.ts` sets `changePct = round1(change) \|\| 0` and `changeFact` says "unchanged" iff the same `round1(change) === 0`, so "no arrow" and "unchanged" coincide exactly (including `-0`). Neutral color `text-muted-foreground`. Points scope is backend's (`unit pct\|ratio` = margin, on-time) |
| 3 Refused page, every screen | Yes | `errors.ts:42-47` returns `errors.forbiddenMessage` for every `FORBIDDEN`; `ErrorState` already titles it "No access"; en/es keys present (`en.ts:834`, `es.ts:852`, es text matches the card). Screenshot office@ en. Test fails on base |
| 4 Plan usage thousands separator | Met as the card is written, **but now conflicts with the PM decision** — see "Question for the tech lead" | Digest plan usage uses `localeNumber()` (bare `es`): "10.000" es / "10,000" en. The card grant never included `settings/billing.tsx`, and gate issue 5's "10000" was the digest page's "Uso del plan" (wave 19 gate screenshot 2), so for the digest page the card's literal AC4 is met; QA's e2e targeting `/settings/billing` is a card/test mismatch, not an author defect |
| 5 Peak under way wording | **Partly** — finding 1 | Correct when `params.niche` is present (test: "The Faith season is on now…"); broken sentence when it is absent. Single renderer used by `recommendation-card.tsx` (market page + `assistant.tsx`) and `digest-copy.ts:128` (digest page) |
| 6 390/1440, en/es, no raw keys, targets | Yes | 4 screenshots looked at: no raw keys, no English in the Spanish shots; the changed tiles are not tap targets |

## Blocking findings
1. `invai-web/src/components/market/recommendation-copy.ts:46` — `{ niche: p.niche ? nicheLabel(p.niche) : "", design }`. The backend only sets `params.niche` when the design has a primary niche (`market/rules.ts` `...(f.niche ? { niche: f.niche } : {})`, `compute.ts:914` `primary = nm?.niches[0] ?? null`), but R1 can fire from the design's **own** sales seasonality with no niche mapping (`compute.ts:540` `ownSeason`). For such a design in its peak month, the market page, assistant card and digest page render "The  season is on now. Make sure Cactus Mama is listed and in stock." / "La temporada de  ya empezó…" (empty slot, double space), while the email for the same record says "The September season is on now…" because `digest/render.ts:301` falls back to the peak month (`p.niche ? nicheLabel(p.niche, lang) : peak`). Fix: fall back to `monthName(p.peakMonth, lang)` like the backend, and add a test for the no-niche case (en and es).

## Question for the tech lead / PM (needed before round 2)
AC4's example ("10.000") predates the PM's T-20-1 decision (`reviews/T-20-1-product-manager-r1.md`; `specs/weekly-digest.md:134,228`): "one convention for the whole digest, `es-US` throughout … one rendered line never mixes separators". The Spanish digest page now shows `$1,956.38` (backend, es-US) and `387 de 10.000 pedidos · Te quedan 1950 créditos` (web, bare `es`) on the same screen — the same mixed-separator pattern the PM called a bug (and `es` does not group 4-digit numbers, so "1950" vs English "1,950"). The code comment at `digest-copy.ts:66-67` cites "the approved wave-20 exception for plan-limit numbers"; I found no such approval in `wave.md`, the specs or the plan reviews.
- Option A (my recommendation, follows the newer decision): digest page uses `es-US` → "10,000" / "1,950" in Spanish; the tech lead amends AC4 for the digest page; `localeNumber` + its test + comment change in round 2. QA's billing-page AC4 case is then re-pointed or re-scoped.
- Option B: PM confirms "10.000" as a deliberate exception for plan numbers; record it in `weekly-digest.md`, and the current code stands.
The author followed the card; this is not held against the diff, but round 2 can't be approved on AC4 until one option is chosen.

## Checks
- [x] Only owned paths changed (`git show --stat f59438f`): `components/digest/**`, `routes/_app/digests/**`, `lib/errors.ts` (FORBIDDEN case only), `market/recommendation-copy.ts` (grant: R1 branch only), `i18n/{en,es}.ts` (2 keys each). Two co-located test files outside the literal grant (`recommendation-copy.test.ts`, `errors.test.ts`) were edited because the granted behavior change made their fixtures wrong; disclosed in the report. Acceptable, tech lead to confirm. No `invai-ui`, `e2e/**`, backend or contracts edits; `billing.tsx` untouched
- [x] Nothing outside scope (local `GlanceTile` is needed for AC2 and justified by `stat-card.tsx:41,66-70`; kit gap reported to product-designer)
- [x] Tests exercise the behavior, none weakened: scan clean; new AC3/AC5 tests fail on base; the removed FORBIDDEN pass-through assertion is the behavior AC3 reverses
- [x] Tenancy / idempotency / money in cents: not touched (web copy only). en/es: both new keys present in both catalogs, es wording matches the card and `render.ts`
- [ ] Decisions recorded where needed: the "bare `es` for plan numbers" choice contradicts the recorded PM decision and has no record (question above)

## Optional notes (not blocking)
1. Pre-existing, not this diff: `insight-card.tsx:68,112` impact chips use `formatMoney(…, i18n.language)` → "~652,08 US$ de impacto" in Spanish, a third money format on the same page next to backend "$1,956.38". Worth a follow-up under the same es-US rule (web-engineer, or product-designer for `formatMoney`).
2. `FORBIDDEN` everywhere now also replaces the backend's meaningful action-level messages ("Only an owner can grant or change the owner role", `tenancy/service.ts:205`; "Sign in as a person to try the sample shop", `tenancy/demo.ts:40`) with "…access to this page", which reads oddly in a toast after a button click. The card asked for every screen, so not blocking; consider a per-code/`data.permission` variant later.
3. `errors.test.ts` lost its only generic pass-through test (a non-special code keeps the server `message`). Cheap to add back.
4. `digest.source.dateLine` es still says "semana que termina el {{date}}" vs the approved "semana al {{date}}" (author's own flag); outside this card's ACs.
5. `pnpm build` needs `VITE_API_URL` set; the card's verification line should say so.
