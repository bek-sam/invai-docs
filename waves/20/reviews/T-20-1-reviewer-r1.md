# Review of T-20-1 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: backend-engineer on Opus 5.5
- Verdict: **changes-required**

## Evidence I re-ran
Own DB `invai_t20_rev1` (dropped after), Redis DB 10 (flushed after), env exported inline
(`TEST_DATABASE_URL`/`TEST_MIGRATION_DATABASE_URL` — `.env` was left untouched per the T-19-3
lesson on `.env` first-key-wins).

| Command | Result |
|---|---|
| `pnpm typecheck` | clean |
| `pnpm lint` (biome) | "Checked 394 files ... No fixes applied." |
| `vitest run src/modules/digest src/modules/market src/modules/today src/integrations/market` | 21 files passed / 2 skipped; 244 tests passed / 3 skipped / 1 todo; 0 failed (clean re-run, see note below on a transient contended run) |
| `vitest run src/modules/digest/date-copy.acceptance.test.ts src/modules/market/market.acceptance.test.ts --reporter=verbose` | 2 files, 31 tests passed, incl. QA's AC1–AC5 acceptance tests and market's AC3 (`r1PastPeak`-guarded, wave 20 wording) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend bfae180~1` | 1 hit: a removed assertion in `market.acceptance.test.ts` (`expect(r1?.params.actByDate).toBe(season.actBy?.date)`) — this is QA's own commit `8814acb` (after `bfae180`) replacing an unconditional wave-18 expectation with the rule-aware guarded version; not the author's edit, not a weakening (see AC6 below) |
| `git -C invai-backend diff --stat bfae180~1 bfae180` | 11 files, all inside the card's owned globs (`market/{rules,compute,service,engine.test}`, `digest/{build,facts,market-watch,render,pure.test}`, `integrations/market/mock.ts`, `today/service.ts`). No scope creep. |
| `node -e 'Intl.NumberFormat("es",...).format(6.9)'` vs `"es-US"` | `"es"` → `"+6,9"` (comma); `"es-US"` → `"+6.9"` (period) — confirms the blocking finding below at the API level, not just by reading the source |

**Note on a transient false alarm.** My first pass at the 4-glob test run showed
`market.acceptance.test.ts:627` (AC3) failing with `expected undefined to be '2026-08-04'` — a
*different* shape of failure than the report's "expects an act-by date for an under-way peak".
Investigating, I found another agent's vitest process running concurrently against the shared
Postgres/Redis (`TEST_DATABASE_URL=...invai_t20_revint`, matching the integrations-engineer
co-review's DB name), plus my own parallel background runs; shortly after, `docker ps` failed and
`orb status` showed `Stopped` — OrbStack had crashed from the combined load. I restarted it
(`orb start`, `docker compose up -d` in `invai-infra/local`; only Postgres/Valkey/MinIO/Mailpit
containers, no data loss) and re-ran alone: 244/244 passed, twice, including AC3. `market.acceptance.test.ts` also passes 24/24 run alone. I'm treating the original failure as
resource-contention noise, not a defect in this diff — the qa-engineer and integrations-engineer
co-reviews (see below) independently confirm the same clean result on their own DBs.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 No past peak | Yes | `date-copy.acceptance.test.ts` AC1 (digest `marketWatch` and `market.recommendations.list` both drop the Aug-1 act-by item, keep an Oct-20 one); `r1PastPeak`/`notPastPeakSql` read together in `rules.ts`/`service.ts`/`market-watch.ts` |
| 2 Peak under way | Yes | `date-copy.acceptance.test.ts` AC2; `rules.ts` sets `params.niche = f.niche`, omits `actByDate` when `underWay`; render.ts's new `R1 action.underWay` template used only when `peakMonth && !actByDate` |
| 3 Points, not relative percent | **No** | En correct ("+6.9 pts", "unchanged"); **Spanish points use a decimal comma ("+6,9 pts") instead of the shop's existing `es-US` convention ("+6.9 pts")** — see Blocking findings |
| 4 Mock source date | Yes | `lastCompletePeriodEnd` in `mock.ts`; integrations-engineer co-review traced it never returns a future instant; `date-copy.acceptance.test.ts` AC4 pins the exact value |
| 5 Today alert | Yes | `today/service.ts` formats `shipBy` with `Intl.DateTimeFormat(..., { timeZone })` in the shop's zone; qa-engineer co-review confirmed no golden-path/smoke spec couples to the old ISO text |
| 6 Existing tests stay green | Yes, now | 244/244 green on a clean run; the one QA wave-18 test the author correctly flagged under "Blocked by other owners" (not edited, not weakened) has since been fixed by QA in `8814acb` per the approved rule, and now asserts the guarded (`peakMonth === 9` ⇒ no `actByDate`) behavior — I judge that change **right**: it matches the wave-20 wording rule in `wave.md` ("Peak under way ... carries no act-by date") and the author's own `engine.test.ts` R1-timing tests exercise the identical case (`today: "2026-10-02"`, under way ⇒ `actByDate` undefined) |

## Blocking findings
1. **`invai-backend/src/modules/digest/facts.ts:90`** — `PTS_LOCALE: Record<Lang, string> = { en: "en-US", es: "es" }` uses the plain `"es"` locale for the new points formatter (`signedPts`), which renders a decimal comma ("+6,9 pts", "+3,3 pts"), while every other Spanish number in the same digest (money, counts, relative percent — `facts.ts`'s existing `LOCALE` map, `{ en: "en-US", es: "es-US" }`, per AC13 "money stays USD in Spanish too") uses a period. Confirmed with `Intl.NumberFormat("es", ...)` → `"+6,9"` vs `Intl.NumberFormat("es-US", ...)` → `"+6.9"`. **Failure scenario:** a Spanish-reading shop owner opens the weekly digest and reads `"Margen: 31.4% (+3,3 pts vs. la semana pasada)"` in the same sentence as other lines formatted `"$1,234.56"` and `"(+23.5%)"` — one document mixes decimal separators, which reads as a bug. This is not just my own read: **the card's required co-reviewer, product-manager, already filed this exact finding as `changes-required`** in `invai-docs/waves/20/reviews/T-20-1-product-manager-r1.md`, with the fix specified (drop `PTS_LOCALE`, reuse the existing `LOCALE` map so Spanish points read `"+6.9 pts"`) and the correction recorded in `invai-docs/specs/weekly-digest.md`'s dated change-log (2026-09-28, currently uncommitted in `invai-docs`). The card's own AC3 wording ("es '+6,9 pts'") is itself the stale, pre-correction example — the PM's review explains this was their own plan-review typo, later caught against AC13's already-shipped convention. Round 2 must also fix the author's own `src/modules/digest/pure.test.ts` assertions (lines asserting `"+6,9 pts"`/`"-6,9 pts"`), which currently encode the same wrong convention and would mask a regression.

## Checks
- [x] Only owned paths changed (`git diff --stat bfae180~1 bfae180`, 11 files, all inside the card's globs)
- [x] Nothing outside scope (no contract, web, or other-module changes; `mock.ts` touches only the granted `asOf` computation, confirmed by integrations-engineer's line-level trace)
- [x] Tests exercise the behavior, and none were weakened — the one removed assertion in the scan is QA's own follow-up fix to their own wave-18 test (`8814acb`), not the author's edit; the author correctly reported it under "Blocked by other owners" instead of touching QA's file
- [x] Tenancy: no new tables; `service.ts`'s `notPastPeakSql` and `listRecommendationsPage` stay inside the existing tenant-scoped query, `ids`-lookup exception documented and tested (keeps a stored assistant card votable); no `withSystem` added on a request path
- [ ] en/es text — **blocked**: the Spanish points string is wrong per the checklist's own "en and es strings" bar (see finding 1); every other new/changed string (R1 under-way line, `market.source`, `change.unchanged`) matches the spec's Copy rows verbatim, checked against `specs/market-signals.md` and `specs/weekly-digest.md` directly, not paraphrased
- [x] Idempotency / money-in-cents / sizes-in-inches — not applicable, no side effects, money or sizes touched by this diff
- [x] Decisions recorded where needed — the Spanish-locale correction is recorded in `specs/weekly-digest.md`'s change-log by product-manager; no further decision needed from me

## Optional notes (not blocking)
- `r1PastPeak`/`notPastPeakSql` treat the "peak under way" case using the digest's exclusive `weekEnd`'s calendar month (or shop-local "today" for the live read), not the design's `currentMonth` at generation time. For a week that spans a month boundary (e.g. week ending the first Monday of next month), this can drop a still-in-peak item a few days before the calendar month actually turns — matches the card's literal AC1 wording ("before the digest week's end") and is exercised by `engine.test.ts`'s `r1PastPeak` unit tests, so I'm not blocking on it, but it's a subtle enough edge that a one-line comment noting the intentional choice (vs. using the generation-time `currentMonth`) would help the next person.
- The known gap the author flagged (`invai-web/src/components/market/recommendation-copy.ts` still renders "before {{peak}}" for an under-way item) is correctly out of this card's scope (T-20-2/web-engineer), and is already routed to the tech lead in the report.
- I did not re-run a live curl against a fresh API instance: the blocking finding is a pure formatting function (`signedPts`), fully reproduced at the `Intl.NumberFormat` level above, and the qa-engineer and integrations-engineer co-reviews already exercised the digest/Today/mock behavior end-to-end (curl and DB) with clean results. Re-running that would have been redundant given the budget note in `agent-brief.md`.

## Disposition
The card cannot be pushed yet: the required co-reviewer product-manager's `changes-required`
verdict (`T-20-1-product-manager-r1.md`) is unresolved, and I independently confirm the same
finding with my own evidence. Everything else — R1 timing (AC1/AC2), mock `asOf` (AC4), the Today
alert (AC5), scope and ownership — is sound and green. Round 2 needs only: `facts.ts`'s
`signedPts` to use the existing `LOCALE[lang]` instead of `PTS_LOCALE`, and the two Spanish
assertions in `pure.test.ts` updated to the period-decimal form. qa-engineer should also update
`digest/date-copy.acceptance.test.ts:291,293` to match (flagged to the tech lead, not this card's
owner's path).
