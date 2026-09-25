# Review of T-4-2 (round 2)

- Reviewer: qa-engineer on Fable
- Author: floor-engineer on Opus 5.5
- Verdict: approve

## Evidence I re-ran
Same worktrees as the primary reviewer's round 2: `invai-floor-t42-r2` @ `a0d88bd`, `invai-backend-t42-r2` @ `bdffe6f` (HEAD), `node_modules` symlinked, DB copy `invai_r42b_copy`, API :3194 (`REDIS_URL=redis://localhost:6379/12`), floor :5194.

| Command | Result |
|---|---|
| `invai-floor-t42-r2$ ./node_modules/.bin/vitest run --passWithNoTests` | 72 passed |
| `E2E_FLOOR_URL=http://localhost:5194 E2E_API_URL=http://localhost:3194 ./node_modules/.bin/playwright test e2e/offline.spec.ts` | 1 passed (3.9s), still asserts the real BLOCKED alert fires correctly |
| Archived `aba5ccf` (pre-fix), copied in the new `outbox.test.ts`, ran only `-t "permanent 500"` | fails on old code (`alerts` has the `gave_up` entry) — confirms the test is not vacuous |
| Read `src/outbox/sync.ts:176-179` diff | filter now `parkReason === "rejected" || parkReason === "blocked"`, explicitly excludes `gave_up` and `session` (and never included `station_forgotten`, which parks via a different path) |

## My round-1 blocking finding — resolved
The fix does exactly what I asked for and nothing more: it doesn't touch the ~90s/5-attempt parking policy (AC1), it only stops a `gave_up` park from being presented as a server rejection. The new test's assertions match my concrete rule from round 1 (`alerts: []`, `rejected: []` for a permanent-500 give-up) and it's proven non-vacuous (fails pre-fix). `offline.spec.ts`'s existing real-rejection path (order on hold → BLOCKED) still passes, so the fix didn't collateral-damage the case AC3 actually asks for.

## Acceptance criteria
AC3 now fully met, no change to the others (round 2 is a scoped fix).

## Blocking findings
none

## Checks
- [x] Only owned paths changed: `src/app/actions.ts`, `src/outbox/outbox.test.ts`, `src/outbox/sync.ts`
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened: one new test, proven to fail pre-fix; no existing assertion touched (`scan-test-weakening.sh`-equivalent check: diff only adds lines to the test file, removes none)
- [x] `press.spec.ts` unaffected (not touched by this diff; not re-run this round since neither changed file is on its path — `sync.ts`'s change only narrows an alert filter, and `press.spec.ts` doesn't exercise `gave_up`)
- [x] Decisions recorded where needed: n/a

## Optional notes (not blocking)
none
