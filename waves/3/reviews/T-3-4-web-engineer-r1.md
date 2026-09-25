# Review of T-3-4 (round 1): web-engineer co-review of the `batch` mutation

- Reviewer: web-engineer (co-review) on Opus 5.5
- Author: backend-foundation on Opus 5.5
- Scope: invai-web `a6ea3a1`, one hunk in `src/routes/_app/shipping.tsx` (the named grant)
- Verdict: **changes-required**

## Evidence I re-ran
| Command | Result |
|---|---|
| `git show --stat a6ea3a1` | only `src/routes/_app/shipping.tsx`, +22/−4, inside the `batch` mutation: within the grant |
| `tsc --noEmit` | exit 0 |
| `biome check .` | 117 files, no fixes |
| `vitest run` | 9 files, 47 tests passed |
| `vite build` | built in 2.79 s |
| Backend side of the flow, live on :3194 | `shipping.batchBuy` answered `{"status":"queued","results":[],"labeled":0,…,"jobId":…}`. `production.jobs.get` went `running` → `done` with `resultIds` of 10 shipments (the reviewer file has the worker-kill run). |
| Browser "Buy & print" | **Not run.** Skipped under the tech lead's stall instruction, so the popup and toast behaviour below is from reading the code. |
| Permission check | Every role with `shipping.buy` (owner, admin, office, packer) also has `production.read`, so the poll can't return FORBIDDEN after the buy was accepted. |

## Acceptance criteria (this hunk's part of criterion 3)
| # | Met? | Evidence |
|---|---|---|
| 3 The web's batch flow keeps working with the async `BatchBuyResult` | Partly | Happy path: the loop ends on `done`/`failed` (`JOB_STATES` has only `queued`/`running`/`done`/`failed`, so there is no unhandled terminal state). It prints `job.resultIds`, keeps the old toast numbers, and a failed job throws into the global `MutationCache` error toast. The button is disabled with a spinner while the mutation is pending. Also handles `status !== "queued"` for an API one version behind. The failure and timeout paths are not safe; see below. |

## Blocking findings
1. **`src/routes/_app/shipping.tsx:141-144`: unbounded poll, no tolerance for transient errors.**
   - **No deadline.** If the job never leaves `queued`/`running`, the button spins forever with no message. That happens when:
     - the worker is down;
     - the outbox relay is behind;
     - the job failed in BullMQ outside its handler (stalled twice, or input parse), which leaves the job row `running` (reviewer note 1).
   - **The loop outlives the component.** The user navigates away, the loop keeps polling, and minutes later it may call `printLabels`/`window.open` on another page.
   - **Any single failed `production.jobs.get` rejects the whole mutation** (a `tsx watch` API restart, which the lessons call out, or a 429/503). The user gets an error toast although the labels are bought and paid. Nothing prints, `invalidate()` never runs, and the queue still lists the orders. A second click then reports them all as "failed" (the backend skips them; no double buy).
   - This breaks the web role's "handle 429/503 gracefully", and criterion 3's "keeps working".
   - **Fix:**
     - retry a failed poll a few times with backoff (honour `Retry-After`);
     - stop after a deadline (e.g. 3 min) with an info toast ("Labels are still being bought; check Shipments"), and `invalidate()` on every exit path;
     - stop on unmount (an `AbortController`/ref flag).
   - A new string needs en + es (`pnpm i18n`). That is still inside this one-file grant.

## Checks
- [x] Only the granted hunk changed.
- [x] Nothing outside scope.
- [x] No tests were weakened. No new unit test for the mutation; the golden-path browser suite covers the button.
- [x] Money: `totalPostage` is summed in cents and formatted `/100`, as before. No new user-facing strings. No PII.
- [x] No decisions needed.

## Optional notes (not blocking)
1. **Popup blocker (unverified, check in the browser).** `printLabels` → `window.open` now runs after the whole job plus 1.5 s polls. Chrome's user activation from the click lasts about 5 s, so for anything but tiny batches the label tab is likely blocked. It was sync before, and usually faster. Consider opening a blank tab synchronously on click and setting its `location` when the PDF URL arrives, or showing a "Print labels" action in the success toast.
2. **Postage requests.** `Promise.all(ids.map(shipments.get))` (line 147) fires up to 100 parallel requests for "Buy & print all". The job already records per-order postage in `jobs.input.results`, and its message carries the total. A small contract addition (e.g. `totalPostage` on the job, or reading `batchLabelPdf`'s shipments) would avoid the fan-out and the 429 risk.
3. **Counting.** `failed = orderIds.length − labeled` counts "already labeled" skips as failures (the author notes this too). This is fine while the queue only lists unlabeled orders.
4. **Progress.** The job publishes `job.progress` (SSE) and a "Bought n of N" message. Showing it on the button would help long batches (needs strings). That is the author's stated gap; a follow-up is fine.
5. **Confirmation.** "Buy a label batch" has no confirm dialog (web rule: confirm costly actions). This predates the change and is outside this hunk; flag it for a web card.
