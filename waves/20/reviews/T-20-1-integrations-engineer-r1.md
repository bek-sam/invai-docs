# T-20-1 co-review (integrations-engineer, mock `asOf` hunk)
Scope: `invai-backend/src/integrations/market/mock*.ts`, `asOf` computation only (grant, `wave.md`).

## Verdict: approve

## What I checked
- `git -C invai-backend show bfae180 -- src/integrations/market` touches exactly one file,
  `src/integrations/market/mock.ts` (no `mock*.ts` sibling exists), 15 lines: a new private
  `lastCompletePeriodEnd(granularity, now)` and one call-site change in `mockDemandSeries`
  (`periodsEnding(granularity, count, new Date())` → `periodsEnding(granularity, count,
  lastCompletePeriodEnd(granularity, new Date()))`). Nothing else in `integrations/market/` changed.
- **Only the anchoring changed.** `lastCompletePeriodEnd` returns the last complete ISO week's
  Sunday (midnight UTC, via `isoDow = now.getUTCDay() || 7` then `midnight - isoDow*86_400_000`)
  or the last day of the previous month; both are always in the past. The actual `asOf` value is
  still produced downstream, unchanged, by `seriesAsOf`/`periodEndIso` in `period.ts` (not part of
  this grant, not touched), which independently recomputes the ISO-week-correct end-of-day instant
  from the period label — so `asOf` is exact (`23:59:59.999Z` Sunday), not just "close to midnight".
- **Never future.** Traced by hand and confirmed by test: on a Monday (`isoDow=1`), `end` = the
  Sunday one day back = the just-finished week's end, correctly excluded from the current partial
  week. On a Sunday itself (`isoDow=7`), `end` = 7 days back, i.e. the current (not-yet-complete)
  Sunday is also excluded — conservative but never future, matching AC4's "never a future date".
  Month branch: `Date.UTC(year, month, 0)` is JS's own "day 0 of this month" = last day of the
  previous month, same guarantee.
- **Weekly/monthly series still end on the right period.** `periodsEnding` builds its period array
  backward from `end`, so shifting `end` one week/month earlier shifts the whole generated window
  by exactly one period — the period *labels* (`isoWeek`) are computed the same way as before, only
  from an earlier anchor. `mock.test.ts`'s seasonal-peak tests (Halloween/Oct, Christmas/Dec,
  Mother's Day/May, back-to-school/Aug, teacher dual-peak) pin fixed 2025 calendar months inside a
  3-year window and are insulated from the exact end-of-week shift; all still pass.
- **Determinism tests still meaningful.** `mock.test.ts`'s "identical for the same query, called
  twice" test explicitly compares `points`/`requestKey` and calls out `asOf`/`fetchedAt` as
  wall-clock (not compared) — that framing is unaffected by this hunk, since the hash inputs
  (`source:query:period`) are unchanged in kind, only which periods get hashed shifts with the
  earlier anchor. `mock.test.ts:286` ("asOf is the end of the last point's period, not the call
  time") and the new `date-copy.acceptance.test.ts` AC4 test (frozen clock `2026-09-28T15:00Z`,
  Monday) assert both "not after now" and the exact value `periodEndIso(isoWeek(2026-09-27), "week")`
  — a real regression guard for gate issue 4, not just a shape check.
- **No provider interface change.** `export`s from `mock.ts` are unchanged (`MOCK_TREND_SHAPES`,
  `MockTrendShape`, `mockDemandSeries`, `mockDemandProvider`, `THIN_TEST_SUFFIX`,
  `mockPricingProvider`); `lastCompletePeriodEnd` is private. `mockDemandSeries`'s signature and
  `DemandSeries` return shape are untouched. `DemandProvider`/`PricingProvider` interfaces
  (`types.ts`) not touched by this commit.
- Biome: `pnpm exec biome check src/integrations/market/mock.ts` → clean.

## Tests run (own DB, dropped after)
Own test DB `invai_t20_revint` (OrbStack/Postgres restarted mid-session after an unrelated
connection drop; re-ran clean after it came back healthy), `TEST_DATABASE_URL`/
`TEST_MIGRATION_DATABASE_URL` pointed at it, Redis untouched (pure/DB tests only, no queue use).
- `vitest run src/integrations/market/mock.test.ts src/integrations/market/period.test.ts src/integrations/market/index.test.ts` → 3 files, 43 tests passed.
- `vitest run src/modules/digest/pure.test.ts src/modules/digest/date-copy.acceptance.test.ts src/modules/market/engine.test.ts src/modules/market/service.test.ts src/modules/market/market.acceptance.test.ts` → 5 files, 117 tests passed (includes QA's AC4 acceptance test and the wave-19 copy test).
- `vitest run src/modules/digest src/modules/market src/modules/today src/integrations/market` (full sweep of every area this card touches) → 21 files passed, 2 skipped, 244 tests passed, 3 skipped, 1 todo, 0 failed.
- `dropdb invai_t20_revint` after.

## Notes (non-blocking)
- `lastCompletePeriodEnd`'s week branch returns midnight, not end-of-day, for `end`; correctness
  relies on `period.ts`'s independent `periodEndIso` recomputation, which is fine (verified above)
  but worth a one-line comment pointing at that split if this file changes again.
