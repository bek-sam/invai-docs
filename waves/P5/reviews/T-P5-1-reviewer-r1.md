# Review of T-P5-1 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: backend-foundation on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend show 41ac4bd --stat` | 1 file, `src/db/seed/builder.ts` +32/-2; `git status src/db/seed` clean |
| `pnpm typecheck` | `tsc --noEmit` exit 0 |
| `pnpm exec biome check src/db/seed` | 10 files, no fixes |
| `pnpm vitest run src/db/seed --reporter=dot` | 4 files, 6 tests passed (vitest "close timed out" warning after the pass, nothing failed) |
| `scan-test-weakening.sh invai-backend 41ac4bd~1` | no hits |
No reseed: the brief says the tech lead checks AC1/AC3/AC4 by SQL on the gate's fresh seed.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes in code (numbers at the gate) | builder.ts:937,1054-1057: the order-scoped `orderQcFailApplied` flag means only the first item that reaches `packed` on a qcFail order gets the detour. builder.ts:1551-1569: the history block takes one item (`min(id)`) per order that has 2 or more pressed-or-later items (`HAVING count(*) >= 2`), so every history reprint leaves a sibling that was not reprinted. Report: 168/6162 = 2.73%, 97.6% partial |
| 2 | Yes | Same model as before: the same row gets `isReprint=true` (1074-1076, 1621-1624) plus a `reprints` row (1063, 1636). No sibling inserts. Spread: n%4 gives 4 reasons and n%2 gives 2 presses and 2 vendor sheets, which holds for any pool of 4+ (160 gives 40/40/40/40 and 80/80) |
| 3 | Yes in code | The diff adds no `random.*` call, so the PRNG stream and every order plan stay the same. Item states are unchanged; only siblings' extra QC transitions and their flags go away. The history UPDATE is limited to `companyId = shopId`, `placedAt < histEnd` (now - 31 d, before the live window) and states pressed to delivered. It touches no live or golden-path order, user, PIN or station token |
| 4 | Gate SQL | Report: 2 reprint orders lose money, 0 have $0 revenue |
| 5 | Closed by R3 | `imaging.preview` call unchanged (the diff doesn't touch it) |
| 6 | Counts yes | Counts are deterministic when the pool has 160 or more orders. Pool under 160: `.limit` returns fewer rows and the loop is bounded by `length`; an empty pool skips the block. No crash, no loop |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`src/db/seed/builder.ts`)
- [x] Nothing outside scope (no schema, catalog or test edits)
- [x] No tests weakened (scan clean). No new test, which is fine for a seed-data card checked by gate SQL
- [x] Tenancy: the new query filters `companyId = shopId` inside the seed's own `run` tx. No new table, money or copy
- [x] Decisions: follows 0020 and R3, nothing new to record

## Optional notes (not blocking)
- builder.ts:1553-1568: `GROUP BY` + `LIMIT` with no `ORDER BY`, plus `min(id::text)` over `defaultRandom()` UUIDs. Which orders and items get reprinted changes from run to run; the counts don't. Adding `.orderBy(orderItems.orderId)` would not help (the ids are random too). This is the same kind of randomness the old unordered `limit(260)` had.
- builder.ts:1578,1589 (existing code): each history batch's `itemCount` is the full candidate count (160), but each sheet holds 80, so the gap is now 4x bigger than before.
- History reprints are flagged in place: no second `transfers` row and no ready-to-pressed transitions. The reprint cost comes from the vendor gang sheet path (existing behavior; 0020 says the seed needs no change).
- Card gap behind the report's incident 2: the card's Verification pins `REDIS_URL` but not `SEED_OUTPUT_FILE`. Future seed cards should require both before any scratch seed.
