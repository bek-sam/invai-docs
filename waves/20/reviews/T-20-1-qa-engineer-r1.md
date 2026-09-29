# Review of T-20-1 (round 1)

- Reviewer: qa-engineer on Sonnet 5
- Author: backend-engineer on Opus 5.5
- Verdict: approve (co-review scope: Today golden-path safety + today/digest/market test run)

## Scope of this co-review
Per card ("qa-engineer: Today is a golden-path screen"), this review checks only: (1) the Today
alert wording change (AC5) cannot break `invai-web/e2e/golden-path.spec.ts` or
`screens.smoke.spec.ts`, and (2) the today/digest/market tests pass on an independent test DB. It
does not stand in for the primary `reviewer`'s full-card review.

## Evidence I re-ran
| Command | Result |
|---|---|
| `grep -n "Ship-by\|toISOString\|past its ship-by\|order_overdue" invai-web/e2e/golden-path.spec.ts invai-web/e2e/screens.smoke.spec.ts invai-web/e2e/api-golden-path.spec.ts` | No hits on the alert message text in any of the three suites. `api-golden-path.spec.ts:50` and `:442` only assert `today.orders.overdue` etc. as counts; the only `toISOString()` hits (`api-golden-path.spec.ts:289`, `golden-path.spec.ts:344`) are unrelated `scannedAt` payload fields for floor scans, not the alert. |
| `git -C invai-backend show bfae180` (full diff, read) | Confirms `today/service.ts` change is `message` text only (`shopDate.format(shipBy)` replacing `shipBy.toISOString()`), no title/severity/dedupeKey/entity change — the fields the web list/detail screens key off of are untouched. |
| Fresh test DB `invai_t20_qarev` created (`createdb -U invai -O invai`), migrated (`MIGRATION_DATABASE_URL=...invai_t20_qarev DATABASE_URL=...invai_t20_qarev pnpm db:migrate` → "up to date", 84 tables), `invai_app` grants present (`has_table_privilege('invai_app','companies','SELECT')` → t) | DB ready, RLS/app-role grants inherited correctly, matching the dev-copy-DB lesson in my memory |
| `TEST_DATABASE_URL=postgres://invai_app:invai@localhost:5432/invai_t20_qarev TEST_MIGRATION_DATABASE_URL=postgres://invai:invai@localhost:5432/invai_t20_qarev REDIS_URL=redis://localhost:6379/15 pnpm vitest run src/modules/today src/modules/digest src/modules/market` | `Test Files 1 failed \| 13 passed \| 2 skipped (16)`; `Tests 1 failed \| 174 passed \| 3 skipped \| 1 todo (179)`. The single failure is `src/modules/market/market.acceptance.test.ts:627` (QA's own wave-18 acceptance test), matching exactly what the author's report flags under "Blocked by other owners" — not a regression the author introduced silently. All `today/service.ts` tests, all `digest/*` tests (including the new `pure.test.ts` "a digest rendered on 2026-09-28" suite) and the rest of `market/*` (including `engine.test.ts`'s new R1-timing and `r1PastPeak` tests) are green. |
| `git -C invai-backend diff --stat bfae180~1 bfae180` | 11 files changed, all inside the card's owned globs (`market/{rules,compute,service,engine.test}`, `digest/{build,facts,market-watch,render,pure.test}`, `integrations/market/mock.ts`, `today/service.ts`). No out-of-scope files. |

## Acceptance criteria (my scope only)
| # | Met? | Evidence |
|---|---|---|
| 5 (Today alert, B-137) | Yes | `today/service.ts` diff shows `message` now formats `shopDate.format(shipBy)` ("Sep 26" style) in `timezone`; no golden-path/smoke spec asserts the old ISO text; `src/modules/today` tests green on my DB |
| 6 (existing tests stay green) | Partly, as reported | today/digest green including the new AC6 render test; the one pre-existing failure is the wave-18 test at `market.acceptance.test.ts:627`, which is Part 2 of my own task (see below) and not silently swept under the rug — the author surfaced it correctly in "Blocked by other owners" instead of editing my file. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat` above)
- [x] Nothing outside scope (mock.ts hunk is the `asOf` computation only, as granted)
- [x] Golden-path/smoke specs don't couple to the alert text — grep above
- [x] Today/digest/market tests green on an independent DB (`invai_t20_qarev`) and Redis DB 15, except the known, correctly-flagged conflict
- [x] The author did not edit my acceptance-test file to route around the conflict — correctly filed it instead (`respect-ownership`)

## Optional notes (not blocking)
- The "es glance" line mixes `es` (points, comma decimal) and `es-US` (other numbers, e.g. "$1,234.56") locales in one sentence, as the author flagged for T-20-2/PM. Not a Today/golden-path issue; leaving it to the primary reviewer and PM.

## Disposition of the flagged wave-18 test
Confirmed and fixed — see `invai-backend/src/modules/market/market.acceptance.test.ts` commit (Part 2
of my task), which asserts the approved rule instead of the old unconditional act-by expectation.
