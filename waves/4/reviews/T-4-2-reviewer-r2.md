# Review of T-4-2 (round 2)

- Reviewer: reviewer on Sonnet 5
- Author: floor-engineer on Opus 5.5
- Verdict: approve

## Evidence I re-ran
Worktree `invai-floor-t42-r2` @ `a0d88bd` (`node_modules` symlinked). Backend worktree `invai-backend-t42-r2` @ `bdffe6f` (HEAD), `node_modules` symlinked, `.env` copied and pointed at a fresh DB copy, port 3194, `REDIS_URL=redis://localhost:6379/12`; floor dev server on :5194.

| Command | Result |
|---|---|
| `invai-floor-t42-r2$ ./node_modules/.bin/tsc --noEmit` | clean |
| `invai-floor-t42-r2$ ./node_modules/.bin/biome check .` | "Checked 69 files … No fixes applied" |
| `invai-floor-t42-r2$ ./node_modules/.bin/vitest run --passWithNoTests` | 6 files, 72 passed (71 + 1 new) |
| `docker exec local-postgres-1 createdb -U invai -T invai invai_r42b_copy` + `tsx src/db/migrate.ts` | up to date |
| API on :3194 (`REDIS_URL=redis://localhost:6379/12`) | `{"ok":true,"db":true,"redis":true,"s3":true}` |
| `E2E_FLOOR_URL=http://localhost:5194 E2E_API_URL=http://localhost:3194 ./node_modules/.bin/playwright test e2e/offline.spec.ts` | 1 passed (3.9s) |
| Archived `aba5ccf` (round-1 code, before the fix), copied in the new `outbox.test.ts`, ran only the new test (`vitest run … -t "permanent 500"`) | **fails**: `alerts` contains the `gave_up` entry (`parkReason: "gave_up"`) instead of `[]` — proves the new test actually exercises the fix |

## Round-1 blocking finding — resolved
`src/outbox/sync.ts:176-179` now filters `report.parked` to `parkReason === "rejected" || parkReason === "blocked"` only, so a `gave_up` (sustained-outage, no server verdict) entry no longer reaches `alerts`/`ReplayAlert` or plays the error sound; it still shows in the Problems sheet with "The server kept failing. Tried 5 times." Verified directly: the new unit test (permanent 500, 5 flushes) asserts `alerts: []` and `rejected: []`, and I re-ran it — passes on `a0d88bd`, fails on `aba5ccf` (above). The E2E's real-rejection case (order on hold) still alerts correctly (`offline.spec.ts` passed).

## Round-1 optional note — addressed
`retryEntries` (`src/app/actions.ts:138`) now has the same `isLead()` guard as `sendEntryAsMe`/`discardParked`. Confirmed by reading the diff (`if (!isLead(useApp.getState().session)) return 0;`, first line of the function).

## Acceptance criteria
Unchanged from round 1 (this round is a targeted fix, not new scope); AC3 is now fully met — the alert fires only for an actual server verdict (`rejected`/`blocked`), matching its wording ("a replayed command that the server rejects").

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat aba5ccf..a0d88bd`): `src/app/actions.ts`, `src/outbox/outbox.test.ts`, `src/outbox/sync.ts` — all within T-4-2's owned globs, no scope creep
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened: one test added, none removed or loosened; it fails without the fix (verified above)
- [x] Tenancy / idempotency / money / en-es: n/a / unchanged — this round touches no server, DB or i18n surface
- [x] Decisions recorded where needed: n/a, this is a bugfix round, not a new decision

## Optional notes (not blocking)
none
