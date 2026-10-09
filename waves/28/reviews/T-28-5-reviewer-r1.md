# Review of T-28-5 (round 1)

- Reviewer: reviewer on opus (claude-opus-5-5)
- Author: backend-engineer on sonnet
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend show --stat 8dcb068 d5e8fd1` | 2 files: `src/modules/channels/sync.ts` (+6), `src/modules/channels/sync-auto-import.test.ts` (new, 95 lines); both commits unpushed on top of origin/main |
| backend `pnpm typecheck` (dirty tree: T-28-2/T-28-3 uncommitted files present) | exit 0 |
| `pnpm exec biome check src/modules/channels` | 13 files, clean |
| `pnpm exec vitest run src/modules/channels --reporter=dot` | 8 files, 52 tests pass (exit 0) |
| New test against base code (`git archive origin/main` in /tmp, test file from d5e8fd1) | 2 failed / 2 passed: poll-skip and on-at-enqueue/off-at-run fail with `imported: 2`; the manual and auto-import-on tests pass on base, as they should (unchanged behavior). /tmp copy removed |
| `scan-test-weakening.sh invai-backend origin/main` | channels: removed=0 added=13; only hit is untracked `privacy/amazon-retention.test.ts` (T-28-3, not this card) |
| `grep syncConnectionJob/syncConnection(` | exactly two enqueuers: `channels.poll` (`jobs.ts:65`, `jobId: null`) and `syncNow` (`sync.ts:505`, `jobId: job.id`), so `!jobId` identifies poll runs correctly |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `sync.ts:543-547` returns before `setJob`, adapter, `markConnection` or emit; test 1 asserts 0 orders, `lastPollAt`/status/`lastError` unchanged, twice; `log.debug` with ids only (no PII) |
| 2 | yes | test 2: autoImport off + jobId → not skipped, job row `done`, `lastPollAt` set |
| 3 | yes | test 4 + existing 7 channels files unchanged and green; guard needs `autoImport === false`, so missing/true settings behave as before (same check as `pollableConnections`, `sync.ts:664`) |
| 4 | yes | setting is read from the row inside `syncConnection` at run time; test 3 switches it off after creation and before the run, and fails on base |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`src/modules/channels/**`)
- [x] Nothing outside scope (webhook path untouched, B-292)
- [x] Tests exercise the behavior and fail without the fix; none weakened (d5e8fd1 replaced a non-existent `lastSyncAt`, which compared undefined to undefined, with the real `lastPollAt`: a strengthening)
- [x] Tenancy: read stays under `withTenant`; no new `withSystem` in production code (test-only setup). Job replay safe: a skipped run has no effect
- [x] Decisions recorded where needed (poll vs manual by jobId, in the report)

## Optional notes (not blocking)
- Test 3 does not go through `syncConnectionJob.enqueue`; it proves the run-time read directly, which is the same thing given the handler only forwards ids.
- The skip runs before the `mode`/`status` check, so a poll for a disconnected connection with auto-import off now returns without the "Nothing to sync" `setJob`; with `jobId` null that `setJob` was a no-op anyway.
- I did not repeat the dev-DB tsx exercise (it adds an order to the shared DB each run); the base-code failure of the new test is my behavioral proof.
