# Review of T-12-1 (round 1)

- Reviewer: qa-engineer on Sonnet 5
- Author: backend-foundation on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint` (invai-contracts, invai-backend, invai-web) | clean in all three |
| `pnpm vitest run` (invai-backend, own DB `invai_test_review121`, own Redis DB) | 87 files / 635 tests passed, matches the report's count |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend origin/main` | 9 lines flagged, all read, none blocking (below) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-contracts origin/main` | no hits |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web origin/main` | 1 hit, traced to an unrelated prior commit (`80fc945`, T-9-4), not this card |
| Targeted read of every new/changed test file for this card (`queues.test.ts`, `internal.test.ts`, `outbox-relay.test.ts`, `sweeps.test.ts`, `channels/stuck-webhooks.test.ts`, `shipping/jobs.test.ts` additions, `ai/breaker.test.ts`) | each asserts the behavior it claims, see below |

## Acceptance criteria — test quality read
| # | Met? | Evidence |
|---|---|---|
| 1. Jitter | yes | `queues.test.ts`: 20 real BullMQ enqueues of the same job type, real failures, asserts delays fall in the jitter range **and** aren't all equal (`new Set(delays).size > 1`) — this actually exercises randomness, not just that the option is accepted |
| 2. `UnrecoverableError` | yes | Asserts `attemptsMade === 1` at the terminal `failed` state for both Zod-invalid input and a mocked 422; a 503 case in the same test proves the permanent path doesn't accidentally swallow transient failures too (asserts `delayed`, `attemptsMade === 1`) |
| 3. DLQ/redrive | yes | `internal.test.ts` runs a real `Worker` against `queues.ship`, drives a job to `failed`, redrives it via the HTTP route, and asserts `completed` — not a mock of BullMQ. 404 matrix (`missing header`/`wrong token`/`unset token`) is one test with 4 branches, per the card |
| 4. Outbox purge/parked alert | yes | `purgeDispatchedOutbox({ batch: 2 })` on seeded rows of varying age proves batching *and* the exclusion rule (parked/pending/recent survive) in one assertion set; "two sweeps, one alert, resolved stays resolved" is a 3-step test, matching the card's literal ask |
| 5. Stuck sweeps | yes | Report claims a delayed-job-backed row is left alone "then failed once that job is removed" — I confirmed this branch exists in `sweeps.test.ts` (a live job protects the row regardless of its age; removing the job lets the sweep fail it next tick), which is exactly the "can't double-process a merely-slow job" property the card is checking for |
| 6. Buy/void/push | yes | New void/push tests mirror the existing buy test's shape (`["failed","failed","alerted"]` + dedupe-keyed alert row), so coverage is now symmetric across all three intent kinds |
| 7. Webhook deliveries | yes | Four cases in one file: alerted-with-company, untouched-when-fresh, flagged-without-company, and purge-flags-before-delete — the last one is the one most likely to be missed and it's present |
| 8. jobId fix | yes | Three tests cover: same-payload/two-events → one job; that job finishing → next event still runs (event-scoped id); a job with no own id still dedupes on re-relay. This also test-proves the author's deviation from the card's literal fallback rule (see the reviewer's r1 note) — a real behavior claim, not just an implementation label |
| 9. Breaker fail-open alert | yes | Forces `redis.mget` to reject 3 times, asserts exactly 1 alert row (the in-process throttle), and a control case (Valkey up → 0 alerts) |

## Blocking findings
None.

## Checks
- [x] Tests exercise real behavior: three of the new suites (`internal.test.ts`, `outbox-relay.test.ts`, `queues.test.ts`) run a real BullMQ `Worker` against the test Redis, not a stub — retries, delays and terminal states are observed for real, not asserted from a mock.
- [x] No weakened tests. Every scanner hit is either a legitimate dependency mock (`redis.mget`, `pushTrackingJob.enqueue` — neither is the unit under test), an assertion spy (`realtime.publish`), the codebase's standard `!env.isTest` scheduler guard (present identically in 6 other `modules/*/jobs.ts` files before this card), or belongs to a different commit entirely (the web hit is from `80fc945`, confirmed by `git log -- <file>`). Assertion count only went up (0 removed / 121 added in backend).
- [x] New-test-fails-on-old-code spot check: read `internal.test.ts`'s 404 test and `queues.test.ts`'s "Zod-invalid input fails after 1 attempt" test against pre-card code — `api/internal.ts` didn't exist and `parseJobInput`/`permanentFailure` didn't exist, so both would fail to even import on `origin/main`. Confirms these aren't tautological additions.
- [x] Full backend suite green on an isolated DB/Redis I created and tore down myself; no shared-state leakage into the shared dev DB.
- [x] Cleanup: my worker/API processes killed, `invai_test_review121`/`invai_test_review121b` dropped, Redis DBs 13/14 flushed.

## Optional notes (not blocking)
- The report's claim of "87 files, 635 tests passed" reproduced exactly on a from-scratch DB copy — good sign there's no hidden dependency on pre-seeded fixture state.
