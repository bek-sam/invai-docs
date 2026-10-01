# Review of T-P2-2 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: backend-engineer (catalog) on Opus 5.5 (card says sonnet)
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` / `pnpm lint` (invai-backend, HEAD incl. f6002ff) | exit 0 / `Checked 455 files`, no errors |
| `pnpm test src/modules/{catalog,orders,production} src/integrations/imaging src/db/rls-coverage.test.ts src/api/authz.test.ts --reporter=dot` | 20 files, 138 tests passed |
| New tests on base `f6002ff^` (git archive in /tmp, removed after) | 5 red: client 5xx + 422, job no-tx, job 4xx, job mid-render. Still green on base: job "transient throws" and the orders mapping test (gap-closing, expected) |
| `scan-test-weakening.sh invai-backend origin/main` + manual read of f6002ff test diff | only call-signature edits in `service.test.ts`, assertions unchanged; no skip/only/snapshot/config changes |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 0 | Partial | Numbers reported, but `scan` was called directly on the read-only miss path (not over HTTP with a station token), imaging was a 250 ms stub (no CPU contention), and "OLD" was a copy script. That supports "not reproduced", not "refuted". |
| 1 | Yes | `service.ts:355-395`: short read tx, imaging with no tx, guarded write per file; `isCompanyKey` on both keys; same key and jobId. No-tx test red on base. |
| 2 | **No** | See finding 1: imaging down (connection refused, or a timeout where `/health` also fails) still writes a permanent placeholder. |
| 3 | Partial | No-tx, mid-render, mapping, tenant tests present. Missing "replace clears the preview (T-P1-4 AC2)" (finding 2). The job "transient" test mocks `imaging.preview` itself, so it passes on base and doesn't cover the client fallback. |
| 4 | Yes | `jobs.ts:52-65` (durationMs, imagingMs), `router.ts:116-125` (companyId, stationId, durationMs; no PII). |

## Blocking findings
1. `src/integrations/imaging/client.ts:317`: the placeholder runs whenever `/health` fails, not only for "imaging not configured". `IMAGING_URL` is a required `z.url()` (`env.ts:54`), so "down" and "not configured" look the same here. Scenario: imaging restarts during a deploy or is saturated so `/health` times out at 2 s; `/preview` fails with status 0, health fails, the gray PNG is written, `previewKey` is set, the job completes, and nothing re-renders until the design is edited again. The kept test `client.test.ts:117` ("falls back to a placeholder ... can't be reached") passes and proves this. The card lists connection refused and timeout as transient. Fix options: throw on every non-permanent failure and write the placeholder only in non-prod/mock mode (an explicit flag), or only on the job's final attempt. If the tech lead wants "down = placeholder", that changes AC2 and is the tech lead's call.
2. AC3 is missing a test: "replace clears the preview (T-P1-4 AC2)". No test updates a design's placements through `updateDesign` and then asserts `previewKey` is null on the new rows (`grep previewKey *.test.ts` finds none). The mid-render test updates `file_key` in place and doesn't use the real replace path (`service.ts:230` delete+insert).
3. AC0 label: change "refuted" to "not reproduced" and list the limits (direct call on the miss path, stub imaging, copied old path). Or re-measure the HTTP `production.scan` press/success path, which writes, locks and publishes, against real imaging. Scenario: the next card drops the render job as a suspect based on a test that never ran the path that timed out.

## Checks
- [x] Only owned paths changed: 8 files, all inside catalog/**, the imaging client and its test, the router log, and an orders test
- [x] Nothing outside scope
- [ ] Tests exercise the behavior: none weakened, but see findings 1 and 2
- [x] Tenancy: `withTenant` throughout, no `withSystem`, no new tables. Idempotency: same jobId and deterministic key. Guard (c): `UPDATE … WHERE id AND file_key` is correct under a concurrent replace. Replace is delete+insert, so the old id matches 0 rows. An in-flight in-place change makes READ COMMITTED re-check the WHERE after the lock and skip. No money or UI text.
- [x] Decisions: card-local only (reuses `isPermanentHttpStatus`)

## Optional notes (not blocking)
- A user-triggered `runDesignQa(cleanAlpha)` changes `fileKey` in place during a render. The guard then drops the preview write, and nothing re-renders. This is the intended behavior, but a new design can be left with no thumbnail. Worth a backlog line.
- `db/seed/builder.ts:535` now throws on a 5xx/422 while imaging is up (out of scope, B-233 rest).
- Not exercised live by me; the AC2 failure is proven by the passing client test above.
