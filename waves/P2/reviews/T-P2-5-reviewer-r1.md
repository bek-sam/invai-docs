# Review of T-P2-5 (round 1)

- Reviewer: reviewer on Claude Opus 5.5
- Author: backend-engineer on Claude Opus 5.5 (card said sonnet; no high-risk flag, so no model-split rule)
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` / `pnpm lint` (invai-backend, clean tree, HEAD 9338944) | tsc clean; `Checked 455 files. No fixes applied.` |
| `pnpm test src/modules/today --reporter=dot` | 3 files, 21 passed (uses a real BullMQ Worker + Redis + `invai_test`) |
| `pnpm test src/db/rls-coverage.test.ts src/api/authz.test.ts` | 2 files, 14 passed |
| new `jobs.test.ts` on base `9338944~1` (archive in /tmp, removed) | 5 failed (red before the fix) |
| `scan-test-weakening.sh invai-backend 9338944~1` | 0 assertions removed, 21 added; 3 hits = `vi.spyOn` observers (enqueue spy calls through; console spy for AC4), not mocks of the unit |
| dev DB `today_action_sets` for Desert Bloom; Redis db 11 `dbsize` | no 2026-09-25 row left (only today's); db 11 = 0 |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | `jobs.ts:100-122`: BullMQ 6.3.8 `JobState` = completed/failed/active/delayed/prioritized/waiting/waiting-children (+`unknown` from `getState`). Live 5 = `LIVE_JOB_STATES` (lib/queues.ts:248) → skip; completed → skip; failed → remove (try/catch) then enqueue; unknown/absent → enqueue (add dedupes). Test "failed → requeued → set exists" and "prioritized left alone, enqueue not called" |
| 2 | Yes | Job path calls `buildTodayActions` without `force`; `actions.ts:126-133` inserts `onConflictDoNothing` and returns `exists`, so a rebuild never reaches the clicks-deleting branch. Test asserts exactly 1 set row after repeat |
| 3 | Yes | failed→rebuilt, live-left-alone, completed/repeat→no enqueue; red on base confirmed |
| 4 | Yes | `jobs.ts:70-82` warn with companyId, date, attempt, attempts, `errorData` only; AC4 test asserts all four fields |

Race analysis (Q1): a failed job can't be "just retrying" (BullMQ moves retryable failures to `delayed`, a live state). Two sweeps both seeing `failed`: A removes+adds; B's `remove()` either hits A's new waiting job (removed, B re-adds: still one job) or an active/locked one (`Job.remove` throws "locked", caught → `false`). Worst case B removes A's already-completed job and re-adds: one extra build that no-ops on the `(company_id,date)` conflict. A DLQ redrive racing the same way ends the same. No lost or duplicate set either way.

## Blocking findings
none

## Checks
- [x] Only owned paths changed: `src/modules/today/jobs.ts`, `jobs.test.ts`
- [x] Nothing outside scope; `src/lib/queues.ts` only imported (no default changed)
- [x] Tests exercise the behavior with a real worker; none weakened
- [x] Tenancy: build still under `withTenant`; existing `withSystem` id-read unchanged; no table, money or UI text
- [x] Decisions: none needed (architect ruling 4 followed)

## Optional notes (not blocking)
- Q3: `sweepTodayActions` → `requeueBuild` wiring (`jobs.ts:162`) has no test; it is a one-line call and the sweep had no test before. A cheap follow-up: run `sweepTodayActions(at)` and assert only the target company's job state, ignoring the global count.
- Q4: forcing `failed` through the Zod `permanentFailure` path gives the same end state as 3 exhausted attempts, as the card allowed; deleting the one row the exercise itself created (no reset) leaves the dev DB as found. Acceptable; I confirmed it is gone.
- AC4 logs once per failed attempt (up to 3 per day-build), on top of the worker's own `job failed` line; fine, given it carries the attempt count.
- The `completed`-with-no-set case (build skipped) stays blocked for the day, as before this card.
