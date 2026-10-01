# Review of T-P3-2 (round 2)

- Reviewer: reviewer on opus 5.5
- Author: floor-engineer on sonnet (fix `5389e5f`); QA e2e copy `8ed8ad3`
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint && pnpm test` (invai-floor @8ed8ad3) | tsc clean; biome 82 files clean; 13 files / 112 passed |
| New tests against base `0dd01ee` (git archive in /tmp, deleted) | 2 fail as they should: one-sound test `expected ['tick','error','error'] to deeply equal ['tick','error']` (the r1 double beep exactly); TTL prune test (entry still present). 37 others pass |
| `scan-test-weakening.sh invai-floor 0dd01ee` | removed=1 added=14. The one removed line is the QA e2e copy swap (below). New `vi.mock`s are collaborators (`submit`, `feedback`, store, queue hook), not `PressStation`. No skip/only/snapshot/config hits |
| `git show 8ed8ad3` | 1 file, 1 line: `toContainText("1 offline scan was rejected")` -> `"1 queued scan was rejected"`, which is `en.ts` `outbox.alert.title_one` with count 1. Same matcher, nothing loosened |

## Round 2 items
| # | Closed? | Evidence |
|---|---|---|
| 1 double beep | yes | `PressStation.tsx` effect still takes the entry but applies/beeps only if `view.provisional \|\| view.queued`. A live scan's view comes from `viewFromResult` (both false), so no second apply. Fail-on-base proof above |
| 2 resolved pile-up | yes | `pruneResolved` on every flush drops entries > 2 min past `sentAt ?? parkedAt`; `clearResolved` on Next/new scan/unmount |
| 3 copy | yes | es `busyQueued` "Se verificará otra vez en {{n}} s"; alert title en/es no longer says offline/"sin conexión" |

## Round 1 regressions checked
- Wrong blank never PRESS: `localPressCheck` unchanged; busy wrong blank is `tone: blocked`, `provisional: true`.
- Late answer only for the same clientScanId: reducer `result` guard unchanged; effect reads `resolved[resultClientScanId]` only.
- Busy -> late verdict still replaces the panel: every local/queued view sets `provisional`/`queued` (`result.ts:114,151`), so the gate passes; test "still replaces a busy panel" passes (`tick, warn, error`).
- 429 never parks: `sync.ts` change only restructures the `setState`; `outbox.ts` unchanged; r1 20-flush test still green.
- Pruning vs a waiting busy panel: `sentAt` is set fresh at the send that publishes the entry (`outbox.ts:157`), so a new entry is ~0 s old and only older than 2 min would go. The panel consumes it on the next render. A `result` phase can't come back for an old id (Next/scan always make a new one). Even if a timer flush lands during runCheck's `await`s, the entry waits in the store until the provisional view is shown. No path drops a result the panel still needs.

## Checks
- [x] Only owned paths: 7 files in `invai-floor/src/**` (author); QA's `e2e/offline.spec.ts` is QA-owned, 1 line
- [x] Nothing outside scope
- [x] Tests prove the fix (fail on base) and none were weakened
- [x] Tenancy/idempotency n/a (client only, same clientScanId); en/es typed in both catalogs
- [x] Floor mismatch still blocks; mock provider untouched; no contract change

## Optional notes (not blocking)
- A late answer that arrives after Next is published after the cleanup ran. It stays until the first flush 2 min later (flush runs on submit, focus, online and the timer), so the memory is bounded.
- The one-sound test's `submit` mock writes the `resolved` entry itself rather than going through the real engine. `outbox.ts:172` still publishes live sends, so the test matches real behavior.
- No live floor run this round. Logic is covered by unit tests; the QA e2e covers the alert text at the gate.
