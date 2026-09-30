# Review of T-23-0 (round 4, AC6 fix of r3; commit invai-backend 6510860 only)

- Reviewer: reviewer on claude-opus-5-5
- Author: backend-foundation on claude-sonnet-5
- Verdict: approve

## Evidence I re-ran (scratch DB `invai_rev_r4_t230_test` pinned via both TEST_* URLs, TEST_REDIS_URL DB 10, empty before; shell PID 47971)
| Command | Result |
|---|---|
| `pnpm typecheck`; `pnpm lint` | clean; `Checked 420 files … No fixes applied` |
| `pnpm test --reporter=dot src/test src/modules/shipping/jobs.test.ts src/modules/orders/state-machine.test.ts` | `Test Files 4 passed (4)`, `Tests 46 passed (46)` (then "close timed out", 2 Vite servers; exited) |
| tsx probe of `assertTestDatabase` (no DB touched, `.env` loaded) | REFUSED: dev unpinned, dev pinned via `TEST_DATABASE_URL`, via `TEST_MIGRATION_DATABASE_URL`, dev on `127.0.0.1?sslmode=disable` pinned, raw `DATABASE_URL` renamed `shopdev` and pinned, `invai_latest`. ALLOWED: default `invai_test`, pinned `invai_rev_r4_t230_test`, pinned `invai_t23_0_r2` |
| New `db-safety.test.ts` against base `db-safety.ts` (6510860~1) | 5 of 13 fail (the 4 dev-pin/raw-name tests + `invai_latest`): the tests prove the fix |
| `scan-test-weakening.sh invai-backend 6510860~1` | removed=2 added=10; the 2 removed lines are the same dev-URL assertion, now via `DEV_DB` |
| `git diff --stat 6510860~1 6510860` | README.md, src/test/db-safety.ts, src/test/db-safety.test.ts: all owned |
| CI check: `.github/workflows/ci.yml:44-45` raw URLs name `invai` | CI's `invai_test` isn't in the refused set, so CI still passes |
| Cleanup | scratch DB dropped, Redis DB 10 flushed (dbsize 0); no process left |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| AC6 clean invai_test each run | yes | unchanged from r3 (global-setup guard → migrate → truncateAll); 46 tests green |
| Truncate can never hit the dev DB (r3 finding 1) | yes | db-safety.ts:29-36 refuses `invai` and the raw env names before any pin; the probe and new tests above |
| README true | yes | README.md:59-66 now says what the code does; the false "can never reach" line is gone |

## Blocking findings
none

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope (the `(^|_)test(_|$)` tightening was an r3 optional note)
- [x] Tests exercise the behavior and fail on base; none weakened
- [x] Tenancy/idempotency/money/i18n: n/a (test harness)
- [x] Decisions recorded: none needed

## Optional notes (not blocking)
- `databaseName` compares the raw pathname, but pg decodes it (`pg-connection-string` index.js:67 `decodeURI`). So a pinned `…/%69nvai` passes the guard and connects to `invai`. That only happens if someone sets it up on purpose. Comparing `decodeURI(name)` would close it.
- db-safety.test.ts raw-env tests restore with `process.env.X = original`. If the value was unset, that writes the string "undefined". It's harmless today because `.env` sets both.
