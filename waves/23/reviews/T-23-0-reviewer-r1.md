# Review of T-23-0 (round 1)

- Reviewer: reviewer on claude-opus-5-5
- Author: backend-foundation on claude-sonnet-5
- Verdict: changes-required

Commit reviewed: `invai-backend` `e22129c` (README.md, src/env.ts, src/test/redis-test-db.test.ts).

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` (invai-backend) | `tsc --noEmit`: clean |
| `pnpm lint` | `Checked 418 files in 245ms. No fixes applied.` |
| `pnpm test src/test/redis-test-db.test.ts src/lib/queues.test.ts src/worker/stall.test.ts`: plain run, no `REDIS_URL`/`TEST_REDIS_URL` in the shell (checked with `env`), own Postgres DB `invai_t23_0_rev` | `Test Files 3 passed (3)`, `Tests 14 passed (14)`, 5.28s |
| `valkey-cli monitor` captured for the whole run above (read-only) | 1,997 lines: 1,962 on `[15`, 34 on `[0`. Every `test.t121.*`/`test.t222.*` job command (123) was on `[15`. The 5 test client connections sent only `HELLO 3` on DB 0 (ioredis handshake before `SELECT 15`). The rest of the DB 0 traffic is the dev worker (`bzpopmin bull:*:marker`, `evalsha`) and a ping, from other client ports |
| `valkey-cli -n 0 --scan --pattern '*test.t*' \| wc -l`, before and after | 0 / 0 |
| New test against the base code (`git archive e22129c~1`, new test copied in) | 3 failed (both redirect cases and the `TEST_REDIS_URL` case), 3 passed. The test fails without the change |
| Edge-case probe: scratch `.mts` boots `src/env.ts` under `NODE_ENV=test` with a given `REDIS_URL`, then builds an ioredis client and reads `options.db` (plus a live `CLIENT INFO` for 4 of them) | `redis://localhost:6379` → `/15`, db 15 live · `…/` → `/15` · `…/0` → `/15` · `?db=0` → `/15?db=0`, db 15 (path wins in ioredis) · `/0?family=4` → `/15?family=4` · `rediss://…` → `/15` · `redis://:pw@…/0` → `/15` · `/14` kept · **`/0/` kept, live `db=0`** · **`/0.5` kept, live `db=0`** · **`/0x1` kept, ioredis db 0** · `//`, `/%30`, `/ 0` kept, ioredis db NaN, and the connection fails with `ERR value is not an integer` (fails closed) |
| `scan-test-weakening.sh invai-backend e22129c~1` | Only hit: "test-only branch" on `src/env.ts:256`. That is the intended `NODE_ENV=test` redirect, the same pattern as `DATABASE_URL`. Not a weakening |
| `grep -rn "REDIS_URL\|new Redis" src scripts` | The only connections are `src/lib/queues.ts:17` (the shared `redis`, also passed to BullMQ as `connection`) and `src/lib/realtime.ts:136`. Both use `env.REDIS_URL`. `scripts/t12-3-fairness-loadtest.ts` reads `process.env` directly, but it is a manual script and not part of the suite |

Cleanup: dropped `invai_t23_0_rev`, ran `flushdb` on DB 15 (0 clients attached; it held only 4 `bull:*:meta` keys from my run). DB 0, the dev DB, :3000, :3142 and :5183 were not touched. No processes left running.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Partly | Redirect works for every realistic DB 0 spelling (no path, `/`, `/0`, `?db=0`, query strings, `rediss://`, auth), and for both connection sites (MONITOR above). It does not hold for a non-canonical DB 0 path such as `/0/` or `/0.5`: see blocking finding 1 |
| 2 | Yes | An explicit `/14` is kept (test + probe). `TEST_REDIS_URL` wins over both (test). Precedence is documented in `env.ts:250-255` and in the README |
| 3 | Yes | The test's `development` and `production` cases return `redis://localhost:6379` unchanged, and `env.ts:256` is `raw.REDIS_URL` when `!isTest` |
| 4 | Yes | `redis-test-db.test.ts`. It fails on the base code (3 of 6) and passes with the change |
| 5 | Yes (author's evidence, per the tech lead's instruction) | The author's full run: 1194 passed. My own BullMQ-file run with MONITOR shows zero test commands on DB 0 beyond the connection handshake |

## Blocking findings
1. `invai-backend/src/env.ts:175` and `:184`: `redisDbIndex` uses `Number(path)`, but ioredis 6.0.0 picks the DB with `parseInt(options.db, 10)` (`node_modules/ioredis/built/Redis.js:725-726`, path taken from `utils/index.js` `parseURL`). Any path where `Number` is NaN or non-zero but `parseInt` gives 0 is treated as "caller pinned a non-zero DB" and kept as-is, so the suite runs on DB 0.
   - **Failure scenario:** a dev `.env` (or CI) has `REDIS_URL=redis://localhost:6379/0/` (a trailing slash after the DB). The dev worker runs on DB 0. `pnpm test` keeps the URL and connects with live `db=0` (my `CLIENT INFO` probe). `queues.test.ts`/`fairness.test.ts`/`stall.test.ts` then `obliterate` the dev worker's `render` queue and add `test.*` jobs to it: this is exactly the B-205 bug. `/0.5` and `/0x1` behave the same way.
   - **Fix (small):** keep a URL unchanged only when its path is a canonical positive integer, for example `if (/^\/[1-9]\d*$/.test(new URL(url).pathname)) return url;`. Redirect everything else to `/15`. Alternatively, compute the index the way ioredis does (`Number.parseInt(path, 10)`, NaN → 0). Add a `/0/` case to `redis-test-db.test.ts`.

## Checks
- [x] Only owned paths changed (`git show --stat e22129c`: `README.md`, `src/env.ts`, `src/test/redis-test-db.test.ts`, all inside the card's owned paths)
- [x] Nothing outside scope (no queue, worker, realtime or CI edits)
- [x] Tests exercise the behavior and none were weakened: the scan hit is the intended test-env branch, and the new test fails on the base code
- [x] Tenancy, idempotency, money, en/es: not applicable (test infrastructure only; no tables, jobs or UI text)
- [x] Decisions recorded where needed: none needed. The precedence rule is documented in `env.ts` and the README

## Optional notes (not blocking)
- `TEST_REDIS_URL` is used verbatim, so `TEST_REDIS_URL=redis://localhost:6379/0` puts the suite on DB 0. It is an explicit opt-in, but applying the same guard to it, or rejecting DB 0 in the Zod schema under test, would make "never DB 0" hold with no exceptions.
- The default DB 15 is shared by every plain `pnpm test` on this machine. Two agents running the suite at once, or a gate plus a reviewer, still collide there (the `render` queue obliterates). The README already says to pin a DB per agent; the tech lead's `agent-brief.md` update (line 23 still says "the test env doesn't redirect Redis yet") should keep that instruction.
- `.env.example` has no `TEST_REDIS_URL` line (the author already lists this as a follow-up).
