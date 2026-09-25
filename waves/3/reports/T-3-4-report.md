# Report: T-3-4 Heavy work leaves the request
Author: backend-foundation on Opus 5.5

Commits on `main` (not pushed):
- **invai-backend `97651a0`:** chunked CSV import job with the ≤300-row inline path, the personalization render job, the batch-label job (`shipping/batch.ts`), sheet-job retries, the scrap job id hash, the `lib/queues` helpers and tests.
- **invai-web `a6ea3a1`:** the `batch` mutation in `src/routes/_app/shipping.tsx` follows the job. **Needs a web-engineer co-review** (one hunk, lines 129-157).

Contract stubs used as committed by the architect in invai-contracts `06e62a3`. No contract edits.

## Intake
- **Card:** T-3-4. **Owner:** backend-foundation. **Scope:** owner's rule 9; always in scope: reliability.
- **Owned (edited):**
  - `channels/router.ts`
  - the CSV import section of `channels/sync.ts` (only my hunks are committed: imports plus the `importCsv` section; T-3-1's webhook hunks weren't touched)
  - `orders/mapping.ts`
  - `personalization/{service,jobs}.ts`
  - `shipping/router.ts` and the new `shipping/batch.ts`
  - `production/jobs.ts`
  - the job registry in `src/modules/jobs.ts`
  - `src/lib/queues.ts` (my own role path)
  - tests next to these files
  - the named grant on `invai-web/src/routes/_app/shipping.tsx`
- **Not touched:**
  - `shipping/service.ts`: the old `batchBuy` is still there, now unused by the router (see gaps)
  - `shipping/jobs.ts` (T-3-2)
  - `channels/service.ts`
  - `orders/import.ts`
  - `production/sheets.ts`
- **Risk flag and co-reviewers:** floor-correctness → reviewer, plus qa-engineer (golden path). Web-engineer co-reviews the one web hunk.

## Built
### 1. CSV import (`channels/sync.ts`, `channels/router.ts`)
**Request.** One short tenant transaction:
- checks the connection;
- reads and parses the file, so a wrong format still fails at once with `CSV_UNREADABLE`;
- checks the plan;
- inserts the `import_runs` row.

**At most `CSV_INLINE_MAX_ROWS` = 300 rows.** The import runs to completion in the request, in chunk transactions of `CSV_CHUNK_ORDERS` = 100 orders each. The reply is the finished report with `status: "completed"` and `jobId: null`. `settings/channels.tsx` needs no change.

**Over 300 rows.** The same transaction:
- inserts a `csv_import` job row whose id is the run's id, so `jobId === importId`;
- emits the outbox event `channels.import_requested`, which is durable, unlike an `afterCommit` enqueue.

It returns `status: "queued"` with zero counts. The job `channels.importCsv` (sync queue, priority 10, 5 attempts with backoff and jitter) then runs the chunks.

**The chunk transaction:**
- locks the run;
- checks that the job row's `cursor` equals the chunk start, so a stalled job picked up twice can't apply a chunk twice;
- imports the chunk and adds its counts, errors and order ids to the run;
- advances the cursor and progress;
- publishes `job.progress`.

**A crash or retry** resumes after the last committed chunk. Each order is counted once.

**The final transaction:**
- applies channel cancellations;
- sets the run to `completed`;
- writes `markConnection`, `markFileReady`, the audit, `import.completed` and the realtime events, the same as before.

**The last failed attempt** marks the run `failed` with the line "The import stopped before the end…". The chunks already committed stay imported and counted. The job row becomes `failed` with the error.

**`channels.imports`** now goes through `listCsvImports`. It maps `pending → queued` and `running → running`, and fills `jobId`. `toImportReport` in `channels/service.ts` isn't mine, so I wrapped it rather than editing it.

### 2. Personalization renders (`orders/mapping.ts`, `personalization/{service,jobs}.ts`)
**Mapping.** `mapItems` no longer calls imaging. `requestItemRender` sets `item_artwork` to `pending` with the values to render, and sets the item's `artworkStatus` to `pending` (batch preview skips it as `needs_artwork`). `mapItems` then emits `artwork.render_requested` in the same transaction. The import, SKU rules, manual map and bulk apply all go this way, so no render ever runs inside an import transaction.

**The job.** `personalization.renderArtwork` (render queue, 3 attempts, exponential backoff with jitter) calls `renderPendingItem` for each item:
1. It reads in one short transaction.
2. It calls imaging with no transaction open.
3. It saves under the item's row lock, but only if the artwork is still the same `pending` render. A staff edit or a second run wins, and the repeat is `skipped`.

**Failures:**
- A transient failure (network, 5xx, 429) is not saved, and the job throws to retry. Items already rendered are skipped on the retry.
- On the last attempt, the failure is saved. The item gets `artwork_qa_failed` with "Personalization render failed: <reason>" and moves `ready → needs_artwork`.
- A refused render (4xx) is saved at once.

**Unchanged:** the interactive single-item paths (`rerenderArtwork`, `updateArtworkValues`, preview) and `renderValues`, which the seed uses. `renderItemArtwork` was split into plan and save steps, with the same behaviour.

### 3. Batch labels (`shipping/batch.ts`, `shipping/router.ts`, web `shipping.tsx`)
**`startBatchBuy` (the request):**
- runs the paid-action gate;
- creates the `batch_labels` job row with `{ orderIds, strategy, packagePresetId, results: {} }`;
- emits `shipping.batch_requested`;
- returns `status: "queued"`, `results: []`, zero counts and `jobId`.

It never enqueues without the gate passing.

**`shipping.batchBuy` job** (ship queue, 3 attempts). Each order goes through the crash-safe `rateOrder` + `buyLabel` from T-2-5. After each order, the outcome is saved into the job row's `input.results`.

**Recognising its own labels after a restart:** the shipment id is written to the job row (`status: "buying"`) *before* `buyLabel`. So a run that restarts after a crash:
- skips orders it already finished;
- counts a label it bought before the crash as its own (`labeled`), and a label that existed before the batch as `skipped`;
- finishes a shipment left `buying`. It waits out `BUY_IN_FLIGHT_MS` from `buyAttemptedAt`, then calls `buyLabel` with the recorded rate, which reads the carrier back and never buys twice.

**Guarantees against a second label:** T-2-5's partial unique index on labels, `rateOrder` refusing an order with a live or in-flight label, and the carrier read-back.

**The finished job:**
- `resultIds` = the shipments this batch labeled;
- message "N labeled, M failed[, K skipped]; postage $X";
- progress events every 5 orders.

**Web.** The `batch` mutation polls `production.jobs.get` every 1.5 s until the job is done or failed, then prints `job.resultIds`. The toast is the same as before: labels bought, the rest counted as failed, and postage summed from `shipping.shipments.get` for each bought shipment. A failed job becomes the mutation's error. No new strings.

### 4. Production jobs (`production/jobs.ts`)
**Retries.** `buildSheets` and `regenerateSheet` now have 4 attempts with exponential backoff and jitter, and throw at the start when imaging is down, so that case retries.

**A retry of a finished run does nothing.** "Finished" means the batch or sheet is no longer `building`, or the job row is done or failed.

**Failure recording.** Only the last attempt marks the job row failed; a build's last failure also marks the batch failed. Earlier attempts only set the message "Retrying after an error: …". Imaging errors inside a run were already recorded on the sheet and still are.

**Scrap job id.** It is now `scrap-cancelled-${orderId}-${sha256(sorted transferIds)[:16]}`, so two partial cancels of one order no longer collide.

### 5. `lib/queues.ts`
- `isFinalAttempt(job)`;
- `RETRY_BACKOFF` (exponential, 5 s, jitter 0.5);
- `runJobInline(job, input, { attempt, attempts })`, so a test can play a retry. By default an inline run is the last attempt.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 CSV import returns at once, chunked job, progress, same report, no one long transaction | Yes | `import-csv.test.ts` (4 tests): inline ≤300 rows returns `completed` with `jobId: null`; 500 rows returns `queued` with `jobId === importId`, no import in the request, then the job runs 3 chunks of 100/100/50 with the final report in `channels.imports`; a crash in chunk 3 resumes at cursor 200 with each order counted once; the last attempt marks it failed and keeps committed chunks. Real run below: the 3,000-row file answered in 86 ms, and the longest open transaction was 1.22 s. |
| 2 Renders in a job after commit; retry 3× with backoff; then `needs_artwork` with the reason | Yes | `render-job.test.ts` (5 tests): mapping queues and doesn't render; the job renders once and a rerun does nothing; a 503 retries and nothing is saved until attempt 2 succeeds; 3 failures give `needs_artwork` + `artwork_qa_failed` with "Personalization render failed: imaging down"; a 422 fails at once; a staff edit wins. `orders/import.test.ts` updated: the import leaves both personalized units `pending`, then the job settles them. Real run: 75 personalized units rendered once each. |
| 3 `batchBuy` returns a batch id; one crash-safe `buyLabel` per order; progress; web keeps working | Yes | `batch.test.ts` (4 tests): answers `queued` with no carrier call; 4 labels bought; a rerun buys nothing; skipped, labeled and failed per order; a crash mid-buy is read back after the in-flight window with 1 extra buy (order 3 only); the paid gate refuses before any job row exists. Real kill test below. Browser: "Buy & print 3" bought 3 and printed (screenshots checked). |
| 4 Build and regenerate retry with backoff; scrap job id has a content hash | Yes | `production/jobs.test.ts` (4 tests): both jobs have attempts > 1 and jitter; with imaging down, attempt 1 throws and leaves the row "Retrying…" and the batch `building`, while attempt 4 of 4 marks both failed; a finished run is skipped; two partial cancels get different ids, and order doesn't matter. |
| 5 Golden path: API and browser suites pass | Yes | API 13/13 and browser 15/15, below. |

## Checks I ran
| Repo | Command | Result |
|---|---|---|
| invai-backend | `pnpm typecheck` | clean |
| invai-backend | `pnpm lint` | "Checked 238 files … No fixes applied." |
| invai-backend | `pnpm test` (`TEST_DATABASE_URL …/invai_test_t34`, `REDIS_URL …/4`) | 59 files, 414 tests passed (run again on the final tree after T-3-1's commits) |
| invai-backend | `pnpm build` | "Build success" |
| invai-web | `pnpm typecheck && pnpm lint && pnpm test && pnpm build` | clean; 117 files lint-clean; 9 files, 47 tests passed; "built in 1.28s" |
| invai-web | `E2E_API=1 E2E_API_URL=http://localhost:3140 pnpm exec playwright test e2e/api-golden-path.spec.ts` on a freshly seeded `invai_t34_copy` | **13 passed** (14.4 s); sheet utilization 0.8848 / 0.8651 |
| invai-web | reseed the copy, wait 65 s, `E2E_API_URL=…:3140 E2E_WEB_URL=…:5140 pnpm exec playwright test` | **15 passed** (50.9 s): golden path 1-13 and both screen smokes, "No screen issues." |

## Exercised for real
Setup:
- DB copy `invai_t34_copy` (`createdb -T invai`), migrated;
- API on :3140 and the worker (both plain `tsx`, not watch);
- imaging on :8140, web on :5140;
- `REDIS_URL=redis://localhost:6379/4`, `MOCK_CARRIER_TRANSIT_HOURS=0.001`.

### 3,000-row CSV
The generated file has 1,500 orders × 2 lines with real SKUs (`DB0xx-G64000-BLK-<size>`). Every 20th order has a personalized DB025 line.
- `importCsv` answered in **86 ms** with `{"status":"queued","jobId":"286ce887…","importId":"286ce887…","rowsTotal":3000,"ordersImported":0}`.
- Progress, polled through `production.jobs.get`: `1.1s running 0% Importing 1500 orders` → `2.1s 7% Imported 100 of 1500` → … → `19.2s 93% Imported 1400 of 1500` → `21.2s done 100% 1500 new, 0 updated, 0 unchanged, 0 row(s) failed`.
- `channels.imports`: `status "completed"`, `jobId` set, `ordersImported 1500`, `rowsFailed 0`, 1,500 order ids.
- **Transaction length.** `pg_stat_activity` was sampled every 0.5 s during the run. The longest non-idle transaction on the copy was **1.22 s**, which is one chunk; the import itself took 20 s.
- **Renders.** Items were 2,925 `none|ready` and 75 `rendered|ready`. There were 75 `artwork.rendered` audits for 75 distinct items: each personalized unit was rendered once, by the job, after its chunk committed.
- **Re-import** of the same file: queued, then done. There were still 1,500 orders (no duplicates), but it reported `ordersUpdated 1500`. The cause is an existing issue in `orders/import.ts`, not this card; see "Blocked by other owners".

### 20-label batch with the worker killed mid-batch (run twice)
- **Run 1.** `batchBuy` answered in 10 ms with `status "queued"`. I sent `kill -9` to the worker tree when 8 labels were bought and 1 shipment was `buying` with `buy_attempted_at` set, then restarted the worker. The job finished: `done 100% 20 labeled, 0 failed; postage $138.41`, with 20 results.
- **Run 2** (20 more orders). Killed at 6 labeled with 1 `buying` (attempted 23:22:47); restarted at 23:22:54. BullMQ state was logged every 10 s:
  - the job showed as stalled at 23:23:35;
  - it was re-run at about 23:23:56 ("Bought 10 of 20");
  - it bought the rest and then waited out the in-flight window of the interrupted buy (until 23:24:48);
  - it read that buy back and was done at 23:24:57: `20 labeled, 0 failed; postage $110.80`.
- **Duplicate check, each batch:**
  - 20 orders, 20 live shipments, 20 distinct shipments, 20 label rows, all 20 `purchased`;
  - **0 orders with more than one live label**;
  - 20 `label.purchased` audits.
- **At the carrier:** the mock carrier rendered exactly **40** labels (`POST /labels/mock` × 40 in the imaging log) for the 40 orders. No label was bought twice.
- Setup note: the copy had only 14 packed orders, so I set 26 of my imported `T34-` orders to `packed` with SQL on the copy. That was test setup only.

### Browser, batch button
A throwaway Playwright script (deleted afterwards) selected 3 rows on `/shipping` and clicked "Buy & print 3".
- The button showed a spinner while the job ran (screenshot).
- The `batchLabelPdf` request fired and the toast read "3 labels bought" after 1,634 ms.
- The queue went from "14 orders packed" to "11 orders packed" (screenshots checked).

### Refused cases
- `presser@` calling `shipping.batchBuy` → `FORBIDDEN`.
- `designer@` calling `channels.importCsv` → `FORBIDDEN`.

## Decisions
- **The job row id equals the import run id** for queued imports. This gives `jobId` for `channels.imports` and `production.jobs.get` without a migration on `import_runs` (a channels schema file, not mine). The resume cursor is kept in `jobs.input`.
- **Jobs start through the outbox** (`channels.import_requested`, `shipping.batch_requested`, `artwork.render_requested`), not through `afterCommit(enqueue)`. A crash between the commit and the enqueue can't lose the work. These are internal event names, not in the contracts `Events`; the same approach as `sheet.regenerate_requested`.
- **Personalized items stay `ready` while their render is pending.** They move to `needs_artwork` only if the render is flagged or fails, which is the order this happened in before. Batches already exclude them: `sheets.ts` needs `artworkKey` + rendered/approved.
- **The in-flight wait happens inside the batch job.** It sleeps up to about 2 min, and BullMQ keeps renewing the lock. The alternative, failing that order, would leave a paid label unrecorded in the batch.
- **The web toast counts "failed" as orders − labeled**, so "already labeled" skips count as failed. The job contract carries only `resultIds` and a message. The ship queue lists only unlabeled orders, so skips there are rare.

## Known gaps and follow-ups
- **Stall recovery was slow once.** In run 1, BullMQ took about 7.5 min after the worker restart to re-queue the stalled job. The job then finished in 1 s with no duplicates. In run 2 it took 56 s, as designed: two 30-second stall checks. The `ship`, `sync` and `reports` blocking connections in the restarted worker reconnected right before the job moved in run 1, so the delay looks like a BullMQ worker start-up issue. I couldn't reproduce it. Worth a look under B-17 (stall alerts and redrive).
- **Interactive single-item renders** (`rerenderArtwork`, `updateArtworkValues`, `previewTemplate`) still call imaging inside the request transaction. They are one item and user-initiated; they were out of this card's import scope.
- **`shipping/service.ts` still has the old synchronous `batchBuy`.** The router no longer calls it; `label-safety.test.ts` still tests its paid-action gate. The shipping owner can delete it and point that test at `startBatchBuy` (my `batch.test.ts` covers the same gate).
- **`channels/settings.tsx`** shows a queued large import as all zeros, as the architect accepted. Wiring a poll is B-85 (wave 5).
- **Web copy.** The progress text isn't shown on the button; it shows only the spinner. A progress toast needs new strings and i18n files outside this grant.
- **`src/modules/README.md`** could gain a line on `isFinalAttempt` / `RETRY_BACKOFF` and the "claim before side effect" batch pattern. It's my file, but I kept this commit to the card's code. I'll add the line with the review round if the reviewer wants it.

## Blocked by other owners
- **`orders/import.ts:144-147` vs `:335` (backend-engineer, orders).** `createOrder` stores the computed ship-by (`computeShipBy`), but `updateExisting` compares the CSV's raw `n.shipBy` with the stored value. So the first re-import of a CSV with a `ship_by` column reports every order as "updated: ship-by" and overwrites the computed date. Seen on the 3,000-row file: `Updated from CSV import: ship-by | 1500`. The Etsy fixture has no ship-by, so its idempotency test passes. Suggested fix: compare against what `computeShipBy` would store, or store and compare the raw channel ship-by separately.

## Processes and data
- **Stopped:** my API (:3140), both workers (all 5 starts), web (:5140) and imaging (:8140). I killed only PIDs I started; nothing listens on 3140, 5140 or 8140.
- **Dropped:** `invai_t34_copy` and `invai_test_t34`. **Flushed:** Redis DB 4.
- **`invai-backend/seed-output.json`:** restored from a backup after the copy seeds; `git status` shows it clean.
- **Deleted:** temp driver scripts (`invai-web/.t34-*.ts`, `e2e/t34-batch.tmp.spec.ts`). Logs and screenshots in `/tmp/t34` are removed after this report.
- **Shared dev DB `invai`:** untouched (used only as the template for the copy).
