# T-P2-5: Today actions build can be re-queued the same day after 3 failed tries

| Field | Value |
|---|---|
| Wave | P2 |
| Scope ref | `always-in-scope: bug` (T-A9 reviewer follow-up, `waves/A2/wave.md:80`, `waves/24/wave.md:53`); PM rank 2 (`reviews/plan-pm.md`) |
| Owner | backend-engineer (today) |
| Reviewer | reviewer (opus) |
| Co-reviewers | none (no migration, no contract change) |
| Risk flags | none (job idempotency; reviewer checks it) |
| Model | sonnet |
| Depends on | nothing |

## Tech lead's notes
- `buildTodayActionsJob` (`invai-backend/src/modules/today/jobs.ts:64-71`) uses jobId `today-actions-<company>-<date>` with 3 attempts; the default queue keeps failed jobs for 7 days (`src/lib/queues.ts:89`, `removeOnFail`). BullMQ ignores an `add` whose jobId already exists, so the hourly sweep (`sweepTodayActions`) can't rebuild that day after a final failure: the panel stays hidden all day.
- The `(company_id, date)` set row in `buildTodayActions` is the real idempotency guarantee.

## Owned paths (edit)
- `invai-backend/src/modules/today/**`

## Read-only paths
- `src/lib/**` (backend-foundation; don't change queue defaults), `src/modules/catalog/**` (T-P2-2), everything else.

## Acceptance criteria
1. When the sweep finds a shop with no set for its local day and the existing job for that jobId is in the `failed` state, it removes that failed job and enqueues a fresh build (or an equivalent within `today/**`). A job that is waiting, active, delayed or completed is left alone (no duplicate builds). `job.remove()` is wrapped so a concurrent sweep that already removed or re-added it doesn't fail the sweep (architect ruling 4; BullMQ 6.3 `getJob`/`getState`/`remove`).
2. Still at most one action set per `(company, date)`, and a rebuild never deletes recorded clicks (T-A9).
3. Tests (red before the fix): final failure then next sweep → a new job runs and the set exists; an active job → the sweep doesn't add a second; repeated sweeps after success → no new job.
4. A failed build logs one warn with `companyId`, date and attempt count (no PII).

## Verification
- `cd invai-backend && pnpm typecheck && pnpm lint 2>&1 | tail -n 20`; `pnpm test src/modules/today --reporter=dot 2>&1 | tail -n 20`.
- Exercise once for real on your own worker (`REDIS_URL=redis://localhost:6379/11`, API `PORT=3125` if needed; record and stop PIDs; never reset the dev DB): force a build to fail 3 times (for example a test-only bad input), run the sweep, show the set appears.

## Budget
- About 2 hours.

Commit only your paths. Don't push. Report: `invai-docs/waves/P2/reports/T-P2-5.md` (at most 60 lines).
