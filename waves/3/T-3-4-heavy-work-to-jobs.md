# T-3-4: Heavy work leaves the request

| Field | Value |
|---|---|
| Wave | 3 |
| Scope ref | owner's rule 9; always-in-scope: reliability |
| Backlog | B-61 (without `rateOrder`, done in T-2-5), B-12 personalization retry (from B-61), B-100 (build/regenerate retries, scrap job id) |
| Owner | backend-foundation (with the named functions in orders, personalization, shipping and production granted) |
| Reviewer | reviewer |
| Co-reviewers | qa-engineer (golden path) |
| Risk flags | floor-correctness |
| Model | opus |

## Owned paths (edit)
- `invai-backend/src/modules/channels/router.ts` and the CSV import entry in `modules/channels/sync.ts`. T-3-1 also edits `sync.ts`: touch only the import-CSV function, and commit only your hunks.
- `invai-backend/src/modules/orders/mapping.ts`, `modules/personalization/{service,jobs}.ts`
- `invai-backend/src/modules/shipping/router.ts`, plus a new `modules/shipping/batch.ts` for the batch-buy job. T-3-2 owns `shipping/jobs.ts`; register your job in the worker registry, not in `jobs.ts`.
- `invai-backend/src/modules/production/jobs.ts`
- `invai-backend/src/worker/**` (job registry)
- Contract changes needed for async results. Coordinate with the architect: a stub commit in invai-contracts, reviewed.
- One narrow, named grant in `invai-web/src/routes/_app/shipping.tsx` (just the `batch` mutation, ~lines 127-145): required same-day, because `BatchBuyResult` becomes async-first for this card (see below) — get a web-engineer co-review on that one file's diff.
- tests next to these files

## r1 review note (architect): exact contract stub shapes
See wave.md "Contract stubs for async results" for the full reasoning; summary:
- **`ImportReport`**: add `status: "queued"|"running"` (append to the enum) and `jobId: Id.nullable().optional()`. Keep imports at or under **300 rows** running to completion inline (short chunked sub-transactions), returning `status: "completed"|"failed"`, `jobId: null` — this is your sync-compatible wrapper, and `settings/channels.tsx` needs no change for it. Only larger files return `"queued"` immediately.
- **`BatchBuyResult`**: add `status: "completed"|"queued"` (default `"completed"`). **No size-based sync wrapper here** — your own verification step (kill the worker mid-20-label batch, restart, check no dupes) only tests anything if 20 labels genuinely go through the async job, so `batchBuy` should always enqueue and return `status: "queued"`, empty `results`, zeros, `jobId` set. That's why `shipping.tsx`'s `batch` mutation is in your owned paths this time: update it to poll instead of trusting the immediate response.

## Acceptance criteria
1. **CSV import** returns an import id at once. The work runs in a job in chunks (short transactions), reports progress, and gives the same final report as today (`channels.imports` shows it). A 5,000-row file doesn't hold one transaction.
2. **Personalization renders** run in a job after the import commits, never inside the import transaction. Failed renders retry with backoff (3 attempts), then flag `needs_artwork` with the reason.
3. **`batchBuy`** returns a batch id. Labels are bought in a job, one crash-safe `buyLabel` each (T-2-5), with progress events. The web's existing batch flow keeps working: if the contract shape changes, update the web consumer the same day, or keep a sync-compatible wrapper for small batches.
4. **Production jobs:**
   - `buildSheetsJob` and `regenerateSheetJob` retry with backoff.
   - The scrap job id includes a content hash, so two partial cancels don't collide.
5. **Golden path:** the API and browser suites still pass.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build`.
- For real on a DB copy:
  - import a 3,000-row CSV (generate it) and watch the progress;
  - batch-buy 20 labels;
  - kill the worker mid-batch, restart it, and check there are no duplicate labels.
- Run both golden-path suites on your copy.

## Out of scope
- Queue fairness per tenant (B-20).
