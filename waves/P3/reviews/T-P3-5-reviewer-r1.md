# Review of T-P3-5 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: backend-engineer (market) on Opus 5.5
- Verdict: approve (partial fix — AC1 and AC3 met for `service.test.ts`; AC2 not met, see below)

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm vitest run src/modules/market/service.test.ts --reporter=dot` | 1 file, 26/26 tests passed, exit 0 (only a benign "Vite server close timed out" message, no test failure) |
| `pnpm typecheck` | clean, exit 0, no output |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend origin/main` | "Result: no hits" on every category (deletes, skips/only/mocks, assertion removal, snapshots, config, test-only branches) |
| `git -C invai-backend diff --stat origin/main` | only `src/modules/market/service.test.ts`, +21/-4 |
| `git -C invai-backend status --short` | clean, nothing uncommitted |

Did not re-run the full `src/modules/market` suite or the acceptance files per the tech lead's instruction (foreground-only, scoped command); the tech lead's stated facts (5 scoped runs 0,1,1,0,0, failures in `*.acceptance.test.ts`) are taken as given.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes, for owned file | All 4 writing `describe` blocks in `service.test.ts` now clear `market_series_cache` in `afterAll` (confirmed by reading lines 462-469, 596-615 — before-write guard already present — and 734, 892, 1098). Matches the pre-existing bracket pattern already used by the two self-protecting blocks and the file-level outer `beforeAll`/`afterAll` (lines 460-469), which is unchanged. |
| 2 | **No** | Tech lead confirms 5 scoped runs = 0,1,1,0,0, failures only in `market.acceptance.test.ts` and `market-prod-mode.acceptance.test.ts` (no `clearCache()` anywhere in either file — confirmed by grep, zero hits), and the full suite wasn't verified (hung under contention). This card's owned-path fix is correct but the card's own AC2 (full `src/modules/market` green ×5) is unmet. Returning the acceptance files to the backlog is the right scope call, not a cover for a missed criterion — flagging explicitly rather than treating it as met. |
| 3 | Yes | Diff is 21 insertions / 4 deletions, every changed line is a new `afterAll` body or a comment; no `expect(...)`, `.skip`, `.only`, retry or timeout touched. `scan-test-weakening.sh` reports no hits. |

## Why the partial fix is safe to push
- `clearCache()` (`withSystem((tx) => tx.delete(marketSeriesCache))`, line 202, unchanged) is a full delete
  of the global cache table — not scoped to one block's keys. That's safe here only because
  `fileParallelism:false` makes execution sequential within one process: at the point each new `afterAll`
  runs, `service.test.ts` is the only writer, so "clear everything" and "clear only what this block wrote"
  coincide. This matches the identical pattern already used by the two blocks the author didn't need to
  touch (lines 462, 505, 870 — clear-before-write) and by the file's own outer `afterAll` (line 466,
  unchanged), so the diff is consistent with existing, reviewed style, not a new risk.
- The diff cannot be the cause of the two acceptance-file failures: `market.acceptance.test.ts` runs
  *before* `service.test.ts` in the observed execution order, so it cannot see any effect of this change.
  `market-prod-mode.acceptance.test.ts` runs after, but the file-level cache state `service.test.ts` leaves
  behind (empty, via the unchanged outer `afterAll`) is identical before and after this fix — only the
  *intra-file* ordering changed. The hook timeout there is pre-existing and belongs to a file this card
  correctly didn't touch (qa-engineer's `*.acceptance.test.ts`, carved out by the role brief).

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat` shows `src/modules/market/service.test.ts` only)
- [x] Nothing outside scope (acceptance files correctly left untouched and reported as a follow-up)
- [x] Tests exercise the behavior, and none were weakened (scan clean; all 4 new blocks still run the same assertions, only cleanup added)
- [x] Tenancy / idempotency / money-in-cents / en-es — n/a, test-only change to a global non-tenant cache table
- [ ] Decisions recorded where needed — n/a, no cross-cutting decision needed; follow-up backlog item is enough

## Optional notes (not blocking)
- Agree with the author's recommendation: file a qa-engineer card for `market.acceptance.test.ts` and
  `market-prod-mode.acceptance.test.ts` to add the same `clearCache()` bracket, so AC2 can be met in full
  on a later pass.
