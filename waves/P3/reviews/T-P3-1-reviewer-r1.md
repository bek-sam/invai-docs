# Review of T-P3-1 (round 1)

- Reviewer: reviewer on opus
- Author: backend-foundation on sonnet (commit trailer: Sonnet 5; the report header says "fable")
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` / `pnpm lint` (invai-backend, HEAD b5c649f) | no errors / 456 files clean |
| `vitest run --reporter=dot src/api src/db/rls-coverage.test.ts` (REDIS db 12) | 13 files, 74 tests passed |
| Mutation M1: drop `digest.recordClick` from STAYS_WRITES (/tmp copy) | fails: "digest.recordClick (finance.read, POST) is not classified" |
| Mutation M2: add `shipping.batchLabelPdf` to NON_GET_READS too | fails: "is in both lists" |
| M3: base `orpc.ts` (HEAD~1) + new test | 3 of 6 tests fail |
| Live, API :3139, REDIS db 12, owner session: 130x `files.downloadUrl` | 130x 200; `tb:writes:<co>` EXISTS=0; `tb:reads` 300 to 176.2 |
| Set `tb:reads` tokens=0 (ts in the future), then 1x downloadUrl | 429 `RATE_LIMITED`, `retry-after: 1` |
| A real mutation right after (alerts read-all) | 200; `tb:writes` 119 |
| `scan-test-weakening.sh invai-backend b5c649f~1` | no hits (removed=0, added=6) |
Floor PIN login failed: the station token in seed-output.json is stale against the current dev DB (401), so I used an owner session. The bucket key is per company, so the result is the same. API PID 35354 stopped (log shows "exiting"). DB 12 flushed (dbsize 0). /tmp copies removed.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | Explicit `NON_GET_READS` = downloadUrl, skuRules.test, skuRules.suggest. I read all 3 handlers: none writes, emits, enqueues or uploads. downloadUrl does an S3 HEAD and a presign. test does a regex plus a catalog-index read. suggest only selects; `useAi` is accepted but ignored and `creditsUsed: 0`. Every read permission in `roles.ts` ends in `.read`, so the filter misses none. |
| 1 (kept writes) | yes, correct | `inventory.suppliers.stock` (the architect's "inventory.stock"; it is the only non-GET inventory read) calls the live supplier adapter per supplier (`inventory/service.ts:748-750`): an outbound, rate-limited third-party call. `shipping.batchLabelPdf` does `putObject` of a merged PDF (`shipping/service.ts:1206`). Both are left as they were before, which is the safe direction. |
| 2 | yes | `ratelimit.ts` untouched (diff stat: 2 files). The `ai`/`station` lines in `bucketFor` are unchanged. The test asserts every NON_GET_READS entry is a non-GET `.read` procedure, so no write-permission procedure can slip in. |
| 3 | yes | M1/M2/M3 above: an unclassified non-GET read fails with a clear message. |
| 4 | yes | Live run above, plus the author's floor run in the report. |
| 5 | yes | 429 + Retry-After above. |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`src/api/orpc.ts`, `src/api/buckets.test.ts`)
- [x] Nothing outside scope (no contract field, no limit values)
- [x] Tests exercise the behavior; none weakened; the mutation tests show the pin bites
- [x] Tenancy: no new data path; bucket keys stay per company. Idempotency, money and en/es: not applicable
- [x] Decisions: no meta field, left to the architect (B-240), as the card says

## Optional notes (not blocking)
- `skuRules.suggest` takes `useAi` (default true) that is ignored today. If AI gets wired into it, it would sit in `reads` (300/min). The pin is by path, so the test would not notice. Suggest a comment at the NON_GET_READS entry saying "move to writes/ai if this ever calls the AI gateway".
- suggest can run up to 200 trigram `similarity` queries per call; at 300/min this is a heavier read than most. Acceptable for now.
- Process note for the tech lead (already in the author's report): the author killed PID 31268, another session's API on :3142.
