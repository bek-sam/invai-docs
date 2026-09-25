# Review of T-3-4 (round 2)

- Reviewer: reviewer on Opus 5.5
- Author: backend-foundation on Opus 5.5
- Commits reviewed: invai-backend `f036fbd`, invai-web `6718293`, on top of round 1's `97651a0` / `a6ea3a1` / contracts `06e62a3`. Worktrees were at these SHAs. The backend worktree also contains T-3-3's `b8ac9d0`, which sits between the two T-3-4 commits; it wasn't reviewed here.
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| backend `tsc --noEmit` | exit 0 |
| backend `biome check .` | "Checked 241 files … No fixes applied." |
| backend `tsup` | "Build success" |
| backend `vitest run` (`invai_test_r34`, Redis db 11) | **62 files, 435 tests passed** (includes `worker/job-failures.test.ts` and the new `import-csv.test.ts` case) |
| web `tsc`, `biome`, `vitest run`, `vite build` | exit 0; 119 files clean; **10 files, 55 tests passed** (includes `lib/poll-job.test.ts`, 8 tests); built in 1.18 s |
| Live stack (copy `invai_r34_copy`, API :3194, web :5194 Vite dev, imaging :8194, Redis db 12) | Browser check in the web-engineer r2 file. Summary: the deadline toast appeared at **181.1 s** with the worker stopped, and the done toast plus click-to-print worked with the worker running. |
| **Two batches on the same 2 orders**, both queued while the worker was down, then the worker started | Both finished. Batch A: "1 labeled, 0 failed, 1 skipped". Batch B: "1 labeled, 1 failed" (B's second order hit "This label is being bought right now" while A held it). **DB: 1 purchased label per order, no double buy.** |
| BullMQ 6.3.8 source (`node_modules/bullmq`) for the `onFinalFailure` trigger | See the semantics section below |

## Round-1 blocker
- **Fixed.** `shipping.tsx` now uses `pollJob`: a 3-minute deadline, transient-error retry with capped backoff, and an abort on unmount, with `invalidate()` in `onSettled`. Verified by the unit tests and in the browser (web-engineer r2).

## `onFinalFailure` semantics (`src/worker/job-failures.ts`, `lib/queues.ts`)
- **Trigger is correct.** `job.finishedOn` is set only by `moveToFailed` on the no-retry path (`bullmq/dist/esm/classes/job.js:482-505`). A retrying failure goes through `moveToDelayed`/`retryJob` and leaves it unset.
- **It covers the "stalled too often" case.** In 6.3.8, `moveStalledJobsToWait-9.lua:96-99` doesn't fail an over-stalled job directly. It sets a deferred failure (`defa`) and moves the job back to wait. The next worker pick-up returns that reason from `getUnrecoverableErrorMessage` and calls `handleFailed(new UnrecoverableError(...))` (`worker.js:571-575`). So the Worker `failed` event does fire, with `finishedOn` set. Bad input (`def.input.parse` throwing, then retries used up) reaches the same listener.
- **The row update is guarded.** It updates the `jobs` row named by `data.jobId ?? data.importRunId` only while it is `queued`/`running`, under `withTenant(companyId)`, so it can't overwrite a handler's own `done`/`failed`. Every job whose input has `jobId` points it at a `jobs` row: `channels` sync, `buildSheets`, `regenerateSheet`, `batchBuy`. For the CSV import, `importRunId` equals the job row id.
- **Hooks are idempotent against the handler's own final-attempt path:**
  - `failCsvImport` returns early if the run is already `completed`/`failed`;
  - the build hook updates only `status = 'building'`;
  - regenerate checks `building` under `lockSheet`.
- **Errors are caught and logged**, not thrown into the event emitter.
- **Tests:** `job-failures.test.ts` covers retrying (no change), final (row failed), an already-done row left alone, data without ids ignored, and the CSV hook failing both the run and the job. I read the diff; the new file has no `.skip`/`.only`, and no assertions were removed anywhere.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 CSV import async, chunked, resumable | Yes | Round 1 live kill-and-resume evidence still holds. r2 adds a stop when the run is no longer `running` (`sync.ts:256`), tested. |
| 2 Renders in a job after commit | Yes | Unchanged since r1 |
| 3 `batchBuy` job; web flow keeps working | **Yes** | The web blocker is fixed and verified in the browser. `saveResult` never downgrades `labeled`, and the summary is re-read from the job row. The concurrent-batches run above shows no double buy. |
| 4 Sheet job retries; hashed scrap id | Yes | r1, plus `onFinalFailure` for build and regenerate |
| 5 Golden path | Not re-run in r2 | r1 got 7/13 API steps on a fresh seed; steps 8–13 and the browser suite are left for the integration gate (qa-engineer r1 escalation). r2 touches only the batch mutation and worker failure handling. |

## Blocking findings
None.

## Checks
- [x] Owned paths. Backend: `worker/**` and `lib/queues.ts` (backend-foundation), plus the card's module files. Web: `shipping.tsx`, a new `src/lib/poll-job.ts` and its test, and one i18n key in `en.ts`/`es.ts`/`scripts/i18n-es.json`. The new lib file and the i18n key go beyond the literal "batch mutation only" grant. The r1 web-engineer review asked for a string that needs en and es, and the helper exists only to serve that mutation. I accept both as within the grant's intent; the tech lead should note it.
- [x] Nothing outside scope.
- [x] Tests added, none weakened.
- [x] Tenancy (`withTenant` in the failure hook), idempotency (guarded updates), no PII in logs (ids and error text only), en and es added.
- [x] No decisions needed.

## Optional notes (not blocking)
1. **The hook is at-most-once.** If the worker process dies between BullMQ's `moveToFailed` and `onJobFailed` finishing, the row still stays `running`. The B-17 stall alert should sweep `jobs` rows stuck `running` with no live BullMQ job.
2. **Concurrent batches on the same order.** The second batch records "This label is being bought right now" as `failed` (it comes from `rateOrder`'s BUSY conflict, before the batch's own in-flight wait). No money risk, but the web toast then says "1 failed" for an order that did get a label. Treating that conflict like `in_flight` in `buyOne` would report it as `skipped`.
3. **The render job** (`personalization.renderArtwork`) carries no job-row id and has no `onFinalFailure`. If it stalls out, its items stay artwork `pending`. Rare, but worth a hook that flags them `artwork_qa_failed`.
4. Round-1 notes 3–6 remain open, as the author states (B-17 or later).
