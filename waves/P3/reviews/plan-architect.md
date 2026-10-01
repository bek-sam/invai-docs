# Plan review: wave P3 (T-P3-1, T-P3-2)

Author: architect. Design review only, read-only on code (orpc.ts, _base.ts, outbox.ts, sync.ts,
errors.ts, invai-contracts/src/contract/*.ts), per gate-rootcause.md.

## Verdict: approve-with-changes

## 1. Explicit backend reads set vs `rateBucket` in ProcedureMeta
Approve the explicit set for this card. It matches the accepted precedent already in `orpc.ts`
(`AI_CHEAP_READS`, same shape: a `ReadonlySet<string>` of full paths), needs no contract change
(the card is right to keep `rateBucket` out of scope for a gated bug-fix wave), and AC3's
walk-every-procedure test is the forcing function that keeps it correct as procedures are added.
Backlog line (not this card): a future wave should add an optional `rateBucket` to `ProcedureMeta`
so a procedure's read/write rate-limit intent is declared where the procedure is authored
(contracts), not maintained as a second list in a file (`orpc.ts`) that only backend-foundation
owns — today, any other role adding a POST-shaped read must wait on a one-line edit from
backend-foundation instead of declaring it themselves.

## 2. Procedures that must never move to reads
Walked every non-GET `*.read`-permission procedure in the contract. These read by permission name
but write or spend, and AC1's test must list them as "stays writes", not reads:
- `alerts.markRead`, `alerts.markAllRead` (POST, marks state)
- `orders.addNote` (POST, writes a timeline entry)
- `digest.feedback`, `digest.recordClick` (POST, write rows)
- `market.recommendations.vote` (POST, writes a vote)
- `tenancy` `org.set`, `today.start`/`reset`/`leave`, `today.dismissChecklist`,
  `today.recordActionClick` (all POST/PUT, all mutate despite `*.read` permission)
- `analytics.export`, `finance.exportCsv` (POST; `finance.exportCsv` returns `JobRef` — enqueues;
  `analytics.export` returns a storage `key` — writes a CSV to storage synchronously)
- `personalization.preview` (POST, calls the imaging render — an outbound/costly call, same reason
  `ai.*` stays off `reads`)
`ai.*` is already routed separately in `bucketFor` and unaffected.
Good candidates for `reads` beyond `files.downloadUrl`: `inventory.stock` (POST only because the
body carries up to 200 ids; no write) and `shipping.batchLabelPdf` (POST only for the `shipmentIds`
array; reads already-purchased label PDFs, no carrier call, no write).

## 3. T-P3-2 floor-correctness rule — gap
AC3 ("replace the busy state with the server's result") is right but incomplete: it doesn't say
what happens if the presser has already scanned the *next* item while the delayed result for the
*previous* `clientScanId` arrives. **Ruling (round 2):** the replace must be keyed to
`clientScanId` and apply only if that id still matches the panel currently on screen; a result that
arrives after the user moved on must go to the existing alert/problem path, never overwrite the
active panel with another scan's result. Without this, a stale BLOCKED (or PRESS) for item A could
flash over item B's in-progress check — a floor-correctness violation.

## 4. Missing from ACs
- T-P3-1: none beyond §1/§2 above; AC3's full-contract walk already guards `ai.*`/`auth:"station"`
  regressions.
- T-P3-2: add the clientScanId-match guard from §3 to AC3 explicitly.

## Rulings for the tech lead to queue (round 2)
1. T-P3-1 report must list `alerts.markRead/markAllRead`, `orders.addNote`, `digest.feedback`,
   `digest.recordClick`, `market.recommendations.vote`, `tenancy.org.set`,
   `tenancy.today.start/reset/leave`, `today.dismissChecklist`, `today.recordActionClick`,
   `analytics.export`, `finance.exportCsv`, `personalization.preview` under "stays writes" with
   the one-line reason each; and decide `inventory.stock` / `shipping.batchLabelPdf` for `reads`.
2. T-P3-2 AC3 gets the clientScanId-match guard above before review round 1 closes.
3. Backlog (not a card): `rateBucket` on `ProcedureMeta`, owned by architect, for a later wave.
