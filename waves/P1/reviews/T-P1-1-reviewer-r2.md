# Review of T-P1-1 (round 2)

- Reviewer: reviewer on Opus 5.5. Author: backend-foundation on Opus 5.5. Commit `invai-backend@f5c0a68` (2 files: `src/test/test-redis.ts`, `src/test/test-redis.test.ts`, both owned).
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm test src/test --reporter=dot` (unpinned) with a 1 s DB-15 sampler (`/tmp/r2reg.log`, 34 samples) | 4 files, 43/43 passed. Two other agents' live claims `lock:1` (pid 97002) and `lock:3` (pid 97202) are in **every** sample, and their tokens are unchanged after the run. My run's claim `lock:2` was present during the run and released at the end. Its DB was dropped. |
| `pnpm typecheck` / `pnpm lint` | exit 0 / `Checked 453 files`, no fixes |
| `scan-test-weakening.sh invai-backend f5c0a68~1` | 3 "removed" assertions are the same checks under a variable rename (`claim`→`result`, `claimTestRedisDb(...)`→`claim()`). Same 6 tests. The `mockImplementation` hit is in T-P1-3's uncommitted files, which I ignored. |

## Finding 1 (r1): fixed
- The test now uses its own per-run `KEY_PREFIX` (`test-redis-db-lock-ut-<pid>-<uuid>:`). `afterEach`, `held toEqual([])`, the fill-all-14 test and the CAS test all touch only `${KEY_PREFIX}*`. The test makes no assertion about global registry state.
- `global-setup.ts` passes neither `registryDb` nor `keyPrefix`, so the real path is unchanged (DB 15, `test-redis-db-lock:`).

## Stale sweep (`src/test/test-db.ts:84-109`): not a correctness bug
- A run's DB is dropped only when **both** hold: the `created_at` marker is more than 1 h old, **and** `kill(pid,0)` returns ESRCH. A live run's vitest main process is alive, so its DB is safe. EPERM or a reused pid counts as "alive", so these cases keep the DB rather than drop it.
- Create and sweep can't race. The sweep, `CREATE DATABASE` and `COMMENT` all run inside the same session-level advisory lock (`:145-167`, one-connection pool, on `/postgres`). A database with no marker is skipped anyway.
- The author's flake comes from the test, not the sweep. `test-db.test.ts:99-105` creates the fixed `invai_test_999999998` from `invai_test_tpl` outside the advisory lock. Two runs reaching that test at once can drop each other's fixture, or collide with another run's template migrate or clone ("being accessed by other users"). Only test runs are affected, not data. This is non-blocking (see notes).

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1, 3, 4, 5, 6, 8 | Yes | Unchanged since r1 (met there) |
| 2 | Yes | Live claims survived the registry-test run (sampler above) |
| 7 | Yes | Isolation holds with 3 concurrent runs; nothing of mine left in `pg_database` or the registry |

## Checks
- [x] Owned paths only · [x] in scope · [x] tests not weakened · [x] tenancy/idempotency/money/i18n n/a (test infra)

## Optional notes (not blocking)
- Take the advisory lock in the stale-sweep test, or use a per-run fake pid such as `999_9xx_<pid>`. Either removes the cross-run fixture race.
- My run printed `close timed out after 10000ms … 2 Vite servers`, but exited on its own. Check for an unclosed Redis or pg handle in the `src/test` files later.
- Processes: sampler PID 97284 was killed. My vitest exited by itself. PIDs 97002 and 97202 belong to other agents and were left alone. I did not touch the dev DB.
