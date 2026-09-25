# Review of T-3-4 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: backend-foundation on Opus 5.5 (backend and web); the contract stubs are by architect (commit trailer: Sonnet 5)
- Commits reviewed: invai-contracts `06e62a3`, invai-backend `97651a0`, invai-web `a6ea3a1`. T-3-3's uncommitted work and later commits were excluded; I reviewed worktrees at these SHAs.
- Verdict: **changes-required**. The backend meets criteria 1, 2 and 4, and criterion 3 on the server side. The one blocker is in the web consumer, which criterion 3 requires ("the web's existing batch flow keeps working"). See web-engineer finding 1, repeated below.

## Evidence I re-ran
| Command | Result |
|---|---|
| backend `tsc --noEmit` | exit 0 |
| backend `biome check .` | "Checked 237 files … No fixes applied." |
| backend `tsup` | "Build success" |
| backend `vitest run` (`invai_test_r34`, Redis db 11) | **59 files, 414 tests passed** |
| web `tsc --noEmit`, `biome check .`, `vitest run`, `vite build` | exit 0; 117 files clean; 9 files, 47 tests passed; "built in 2.79s" |
| contracts `tsc`, `biome`, `vitest run` | clean; 4 files, 31 tests passed |
| floor `tsc --noEmit` against `06e62a3` | exit 0 |
| Live: API :3194 + worker (`MOCK_CARRIER_TRANSIT_HOURS=0.001`), imaging :8194 (:8000 was down), copy `invai_r34_copy` | see below |
| **10-label batch, worker `kill -9` mid-batch** | `batchBuy` answered `queued` with a jobId. Killed at 5 labeled; the job row showed "Bought 5 of 10", 6 results (5 plus 1 `buying` claim). Restarted 12:39:30 UTC. BullMQ re-ran the job at 12:40:02; the restarted run bought 4 more, waited out `BUY_IN_FLIGHT_MS` for the claimed order, read the carrier back (the mock had rendered the PDF but not recorded the sale when killed) and bought it at 12:41:24. Result `done`, "10 labeled, 0 failed; postage $76.28". **DB: 10 orders, 10 live shipments, 10 label rows, 0 orders with more than one purchased label, 10 `resultIds`, 10 `label.purchased` audits, 10 distinct `carrier_shipment_id`s.** Imaging logged 11 `/labels/mock` renders: the 11th is the killed, unrecorded mock buy, so the carrier sold 1 label per carrier shipment. |
| **1,200-row Etsy CSV (600 orders), worker killed mid-import** | `importCsv` answered in **63 ms**: `status "queued"`, `jobId === importId`, zero counts. Killed the worker at cursor 400 ("Imported 400 of 600", run `ordersImported 400`). After the restart it resumed and finished: "600 new, 0 updated, 0 unchanged, 0 row(s) failed". Run `completed`, `order_ids` 600, all distinct; **600 orders, 1,200 units in the DB (no duplicates, none skipped)**. `channels.imports` shows `completed` with the `jobId`. |
| Re-import of the same 1,200-row file | queued, then "0 new, 0 updated, 600 unchanged"; still 600 orders |
| API golden path on a fresh reseed of my copy (`E2E_API=1`, :3194) | **7 passed, 1 failed, 5 did not run.** Step 8 failed with "Station token required". This is the environment, not the change: `e2e/helpers/api.ts:12` reads `seed-output.json` from the main `invai-backend` checkout, not my worktree's seed. Copying my seed output over the main repo's tracked file was denied, correctly. So steps 8–13 were **not re-verified** by me (see the qa-engineer file). |
| Browser "Buy & print" | **Not run** (skipped under the tech lead's stall instruction). The web hunk was reviewed by reading only. |
| Test-weakening scan (these commits only) | No `.skip`/`.only`/deleted assertions. `import-csv.test.ts` has a `vi.mock` of `orders/import`: a spy around the real `importNormalizedOrders` (a collaborator, not the unit under test) that injects a crash. Acceptable. `orders/import.test.ts` was extended (it now runs the render job and asserts both units `pending` first), not loosened. |

Process note: to kill the worker's `tsx` child I used `pkill -9 -P <my worker PID>` once (scoped to my own PID). Later kills used `pgrep -P` + `kill`. Everything I started is stopped; `invai_r34_copy` and `invai_test_r34` are dropped; Redis db 11 is flushed; the worktrees are removed.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 CSV import returns an id at once; chunked job; progress; same final report; no long transaction | Yes | Live: queued in 63 ms, then chunked progress, the same report shape, and a crash resume with exact counts (above). Code: each chunk locks the `import_runs` row, checks `jobs.input.cursor === from` and commits the counts and cursor atomically, so a crash can't double-count or skip (`sync.ts:246-297`). Tests: `import-csv.test.ts` (4). I did not measure transaction length myself; the author sampled 1.22 s max. |
| 2 Renders in a job after commit; 3 attempts with backoff; then `needs_artwork` with the reason | Yes | `mapItems` only calls `requestItemRender` and emits `artwork.render_requested` in the same tx (outbox, so after commit). `renderPendingItem` reads, renders with no tx, and saves under an item row lock only if the artwork is still the same `pending` render. Transient failures return `retry` until the final attempt. Job: `attempts: 3`, `RETRY_BACKOFF` (jitter 0.5). `render-job.test.ts` (5) passed in my run. |
| 3 `batchBuy` returns a batch id; crash-safe `buyLabel` per order; progress; web keeps working | **Backend yes; web no** | Backend: live kill test above plus `batch.test.ts` (4). Web: the flow works in the happy path, but it can hang forever. That is blocking finding 1. |
| 4 Build and regenerate retry with backoff; scrap job id has a content hash | Yes | `RENDER_RETRY = { attempts: 4, backoff: RETRY_BACKOFF }`; a finished run is skipped; only the final attempt marks failed. `transferSetHash` is sorted, sha256, 16 hex characters. `production/jobs.test.ts` (4) passed. |
| 5 Golden path API and browser pass | **Not re-verified** | 7/13 API steps passed on my fresh seed. Step 8 was blocked by the environment; the browser suite was not run. The author reports 13/13 and 15/15. It needs a run from the main tree at the integration gate. |

## Blocking findings
1. `invai-web/src/routes/_app/shipping.tsx:141-148` (web-engineer finding 1): the poll loop has no deadline and no tolerance for errors, and it outlives the component.
   - **Worker down or backlog:** if the worker is down, the outbox relay isn't running, or BullMQ gives up on a twice-stalled job (see note 1), the job row stays `queued`/`running`. "Buy & print" then spins forever with no message.
   - **One failed poll:** a single failed `production.jobs.get` (API restart, 429/503) rejects the whole mutation *after* labels were paid for. Nothing prints, and the queue isn't invalidated.
   - Criterion 3 requires the existing batch flow to keep working, and a sync request could never hang like this.
   - Fix: a deadline (e.g. about 3 min, then an info toast saying labels are still being bought, with a pointer to Shipments, plus `invalidate()`); retry transient poll errors a few times; stop polling on unmount.

## Checks
- [x] Only owned paths changed. Backend: `channels/{router,sync}.ts` (only the import section and imports; T-3-1's hunks untouched), `orders/mapping.ts`, `personalization/{service,jobs}.ts`, `shipping/{router,batch}.ts`, `production/jobs.ts`, the registry line in `src/modules/jobs.ts` (the card says `src/worker/**`; the registry actually lives here, which is fine), and `lib/queues.ts` (backend-foundation's own path). Tests sit next to these. Web: one hunk in the granted mutation. Contracts: the two stubs.
- [x] Nothing outside scope.
- [x] Tests exercise the behavior; none were weakened (scan above).
- [x] Tenancy: every new handler runs `withTenant(companyId)`; no new `withSystem` in production code; no new tables. Idempotency:
  - batch: the job-row claim before each buy, plus `buyLabel`'s shipment lock, in-flight window and read-back, plus the labels partial unique index;
  - import: cursor under the run lock, plus the `(channel, channelOrderId)` upsert;
  - render: `pending` state guard;
  - sheets: batch/sheet `building` check plus the job-row status.
  - Money is in cents; no new user strings (the web reuses keys); no PII in job data (ids only).
- [x] Decisions: "the job row id equals the import run id" and "start jobs through the outbox" are stated in the report. No ADR needed.

## Optional notes (not blocking)
1. **Jobs that fail outside the handler leave the row `running` forever.** BullMQ's default `maxStalledCount` is 1: a job killed twice is failed with "job stalled more than allowable limit" and the handler never runs, so neither `failCsvImport` nor the batch `failed` update runs. The same happens when `def.input.parse` throws in `worker/index.ts`. `worker.on("failed")` (`src/worker/index.ts:34`) only logs. Suggest a failed-listener that marks the job row (and the import run) failed. B-17, with the author's 7.5-minute stall observation.
2. **Duplicate concurrent runs of one job (stalled but still alive):**
   - Import: the chunk loop doesn't stop when the run was marked `failed` by the other run's final-attempt handler (`sync.ts:260` throws "already applied", then `sync.ts:414` marks failed while the first run keeps importing).
   - Batch: run B can overwrite run A's `labeled` result with `failed` (conflict from `buyLabel`), so a paid label drops out of `resultIds` and isn't printed.
   - No double buy or double import in either case. Worth a `status === "running"` check per chunk, and "never downgrade `labeled`" in `saveResult`.
3. **Unused job ids.** The outbox relay overrides every subscriber's `jobId` with `${eventId}:${jobName}` (`worker/outbox-relay.ts:43`), so the defined ids (`import-csv-…`, `batch-labels-…`, and the new hashed `scrap-cancelled-…`) are never used on these paths. The DB guards are what protect them, which is correct. Criterion 4's hash is met in the definition, but it has no effect today.
4. **Build retries are narrower than they look.**
   - A `nest` failure (imaging 5xx) is still finalised as failed with no retry (`sheets.ts` `runBuildSheets` catch).
   - A retry after a crash between `createSheetRows` and compose leaves that sheet `building` with its items pointing at it; the retry nests only the rest. No duplicate transfers, but an orphan sheet. It was the same before (attempts 1).
5. **Unknown-outcome buys.** A batch order whose buy ends `UPSTREAM_FAILED` (outcome unknown, `buyAttemptedAt` cleared) is recorded `failed` without reading back. Since the window is already cleared, the job could call `buyLabel` once more to read back right away.
6. **Inline path (≤300 rows)** now commits chunks. A process crash (not an exception) mid-request leaves the run `running` with no job to finish it. This is a rare dev/ops case; the partial orders are idempotent on re-import.
7. **Author-reported follow-ups agreed:** the unused sync `batchBuy` in `shipping/service.ts`, the `orders/import.ts` ship-by re-import bug, and interactive renders inside a tx.
