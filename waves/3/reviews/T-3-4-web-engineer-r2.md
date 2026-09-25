# Review of T-3-4 (round 2): web-engineer co-review

- Reviewer: web-engineer (co-review) on Opus 5.5
- Author: backend-foundation on Opus 5.5
- Scope: invai-web `6718293`:
  - `src/routes/_app/shipping.tsx`;
  - new `src/lib/poll-job.ts` and `src/lib/poll-job.test.ts`;
  - key `ship.batchStillBuying` in `src/i18n/en.ts`, `src/i18n/es.ts` and `scripts/i18n-es.json`.
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `tsc --noEmit` | exit 0 |
| `biome check .` | 119 files, no fixes |
| `vitest run` | **10 files, 55 tests passed** (`poll-job.test.ts`: 8) |
| `vite build` | built in 1.18 s (a missing Spanish key would have failed it) |
| **Browser, worker stopped.** Throwaway Playwright spec (since deleted) against web :5194 (Vite dev, `VITE_API_URL=http://localhost:3194`), API :3194, imaging :8194, DB copy. Owner login, 2 rows selected, "Buy & print 2". | `batchBuy` 200, then `production.jobs.get` every **1.5 s** (about 120 polls). The button stayed disabled with a spinner. The last poll was at 181.0 s. At **181.1 s** the toast read: "Still buying labels in the background. They'll show up under Shipments when they're done." Afterwards the button was idle, the selection cleared and the queue refreshed. No console errors before that point. (My first attempt missed the toast: the host suspended mid-run, showing `ERR_NETWORK_IO_SUSPENDED` and a 480 s gap in the log. The instrumented rerun above is the evidence.) |
| **Browser, worker running.** Same flow on 2 new rows. | The toast read "2 labels bought · Postage $24.75" with a "Print 2 labels" action, after 1.9 s. **0 tabs opened by themselves.** The toolbar showed "Print 2 labels". Clicking it gave `batchLabelPdf` 200 and exactly 1 tab. The queue went from 12 to 10 orders packed. No page errors. I looked at the screenshot: the toast, the toolbar button and the refreshed count were all correct. |
| Deadline shortening | Not needed; I waited out the real 3 min. The `pollJob` unit tests also cover the deadline with a fake clock. |

## Round-1 findings
| r1 | Status | Evidence |
|---|---|---|
| Blocker: unbounded poll, no transient tolerance, outlives the component | **Fixed** | `pollJob` has a deadline (180 s), retries 408/429/502/503/504 and network errors with capped exponential backoff until the deadline, and throws other errors. `AbortController` in a ref is aborted in the `useEffect` cleanup, and an aborted poll returns quietly (the abort also wakes the sleep). `onSettled` refreshes on every outcome. All verified by unit tests and the browser runs above. |
| Note 1: popup blocker | Fixed | Print happens from a click (toast action or toolbar button). |
| Note 2: postage fan-out | Softened | `allSettled`, and postage is dropped from the toast if any read fails. The fan-out remains (see note 2 below). |
| Note 3: skips counted as failed | Unchanged | Accepted; see reviewer r2 note 2. |

## Blocking findings
None.

## Checks
- [x] Paths. `poll-job.ts` and the i18n key are outside the literal "batch mutation" grant but serve only it; my r1 review asked for the string. Acceptable, and noted for the tech lead.
- [x] The en and es strings are real Spanish ("Seguimos comprando las etiquetas en segundo plano. Aparecerán en Envíos cuando terminen."). The reused `ship.printSelected` has `{{count}}` in both languages.
- [x] The author hand-added the key rather than running `pnpm i18n`, to avoid committing others' pending strings. That's correct under the shared-repo rule. The build passes, so no key is missing.
- [x] No weakened tests; one new test file.
- [x] Money in cents, formatted `/100`. No PII. No `dangerouslySetInnerHTML`.

## Optional notes (not blocking)
1. **`Retry-After` isn't read.** On 429/503 the backoff is fixed exponential. That's fine at a 15 s cap, but the web rule asks to honour `Retry-After`; wire it once `errorInfo` exposes headers.
2. **Postage still fans out** as up to 100 parallel `shipments.get` calls for "Buy & print all". A job-level postage total (architect r1 note 3) would remove it.
3. **Timed-out batches aren't followable.** After the deadline the "Print" affordance is lost; the user must find the labels under Shipments. A later card could resume following the job from Shipments or through the realtime `job.progress`.
4. **Pre-existing:** there's still no confirm dialog before buying a label batch (web rule: confirm costly actions). Needs a separate web card.
