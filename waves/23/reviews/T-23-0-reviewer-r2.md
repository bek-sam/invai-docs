# Review of T-23-0 (round 2)

- Reviewer: reviewer on claude-opus-5-5
- Author: backend-foundation on claude-sonnet-5
- Verdict: approve

Commit reviewed: `invai-backend` `5630634` on top of `e22129c` (`git diff e22129c 5630634`: `.env.example` +3, `README.md` +7/-4, `src/env.ts` +42/-6, `src/test/redis-test-db.test.ts` +67/-0).

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` (invai-backend, Node v24.21.0) | `tsc --noEmit`: clean |
| `pnpm lint` | `Checked 418 files in 302ms. No fixes applied.` |
| `pnpm test src/test/redis-test-db.test.ts src/lib/queues.test.ts`: plain run, `REDIS_URL`/`TEST_REDIS_URL` unset (`env \| grep -c REDIS` = 0), own Postgres DB `invai_t23_0_rev2` via `TEST_DATABASE_URL`/`TEST_MIGRATION_DATABASE_URL` only. Waited first for another agent's plain vitest run (PID 2680, on DB 15) to finish, so the two runs did not share DB 15 | `Test Files 2 passed (2)`, `Tests 17 passed (17)`, 3.53s |
| `valkey-cli monitor` captured for the whole run above (read-only, container-side `timeout 40`) | 1,611 lines: 1,606 on `[15`, 4 on `[0`. The 4 on DB 0 are 3 ioredis `HELLO 3` handshakes (before `SELECT 15`) and one `ping` from another client. `test.*` commands: 120 on DB 15, 0 on DB 0 |
| `valkey-cli -n 0 --scan --pattern '*test.t*' \| wc -l`, before and after | 0 / 0 |
| Live probe (scratch `.mts`): boot `src/env.ts` with `NODE_ENV=test` and a given `REDIS_URL`, build an ioredis client, read `options.db` and `CLIENT INFO` | Redirected to `/15`, **live db=15**: no path, `/0`, **`/0/`**, **`/0.5`**, **`/0x1`**, `/00`, `/014`, `/1e1`, `/%31`, `/+1`, `/-0`, `/14/`, `?db=0`. Kept: `/14` → live db=14. The round-1 escapes are closed |
| Same probe with `REDIS_URL=redis://localhost:6379` and `TEST_REDIS_URL` set | `/0`, no path, `/0/`, `/0x1`: process exits 1 with `Error: TEST_REDIS_URL must point at a non-zero Redis DB (got "redis://localhost:6379/0"), never DB 0 — the dev/CI worker's DB (B-205). Use e.g. redis://localhost:6379/14.` `/13` → live db=13. `/14?db=0` → live db=14. Empty `TEST_REDIS_URL=` → falls through to the redirect, `/15` |
| `NODE_ENV=development REDIS_URL=redis://localhost:6379` boot | `redis://localhost:6379` unchanged (AC3) |
| New test file against the round-1 code (`git archive e22129c` into the scratchpad, r2 test copied in, `vitest run`) | `Tests 5 failed \| 6 passed (11)`: the 5 new cases (`/0/`, `/0.5`, `/0x1`, TEST_REDIS_URL `/0` and `/0/`) fail without the fix. The new tests prove the fix |
| `scan-test-weakening.sh invai-backend e22129c` | Only hit: "test-only branch" on `src/env.ts` `REDIS_URL: isTest`. This is the intended `NODE_ENV=test` redirect (same as r1, same pattern as `DATABASE_URL`). The test file diff is additions only (+67/-0); no assertion removed or loosened |
| `git show --stat 5630634`, backend-foundation role file line 34 | All 4 paths are backend-foundation's. `.env.example` is not on the card's list but is in the role's owned paths ("`.env.example` stays in sync with `env.ts`", line 51). It is a commented doc line and answers my r1 note, so it is not scope creep |

Cleanup: dropped `invai_t23_0_rev2`, deleted the scratch archive and the monitor capture, and my monitor client exited (container-side timeout). I left Valkey DB 15 unflushed: after the other agent's full run it held 232 keys (mostly `rt:company:*` streams) that were not mine, and it had 0 clients attached. DB 0, the dev DB, :3000, :3142 and :5183 were not touched. Nothing I started is still running.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | Every DB 0 spelling I tried (including the round-1 `/0/`, `/0.5` and `/0x1` escapes) redirects to live DB 15. MONITOR shows no test command on DB 0 during the plain run |
| 2 | Yes | `/14` is kept (test and live probe). `TEST_REDIS_URL=/13` wins (live db=13). The precedence and the pinned-DB rule are documented in `env.ts` and the README |
| 3 | Yes | The development boot leaves `REDIS_URL` unchanged. The test's `development`/`production` case passes |
| 4 | Yes | `redis-test-db.test.ts` has 11 cases. The 5 new ones fail on round-1 code and pass now |
| 5 | Yes (author's r1 full-suite evidence, plus my targeted run) | 0 test keys on DB 0 before and after. MONITOR shows 0 test commands on DB 0. The full suite was not re-run (tech lead's instruction; the r2 diff only touches the env redirect) |
| r1 finding 1 | Closed | Live `CLIENT INFO` shows db=15 for `/0/`, `/0.5` and `/0x1` |
| r1 note (TEST_REDIS_URL on DB 0) | Closed | Boot fails with a clear message (above) |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat e22129c 5630634`: 4 backend-foundation paths; `.env.example` is in the role's paths, see above)
- [x] Nothing outside scope (no queue, worker, realtime or CI edits)
- [x] Tests exercise the behavior, and none were weakened (additions only; the new tests fail on the base; the scan hit is the intended test-env branch)
- [x] Tenancy, idempotency, money, en/es: not applicable (test infrastructure only; no tables, jobs or UI text)
- [x] Decisions recorded where needed: throw vs redirect for `TEST_REDIS_URL` is a choice inside the card, and the author's report explains it. No decision file is needed

## Optional notes (not blocking)
- The `TEST_REDIS_URL` error echoes the full URL, so a password in it (`redis://:pw@host/0`) would reach stderr. This only happens under `NODE_ENV=test` on a misconfiguration, and local and CI Redis have no password, so it is harmless today. Printing only the path (`new URL(url).pathname`) would remove it.
- The default DB 15 is shared by every plain `pnpm test` on this machine. During this review, another agent's plain full run was using DB 15, and I had to wait for it to finish before starting mine. `invai-docs/team/agent-brief.md:23` still says "the test env doesn't redirect Redis yet". When the tech lead updates it, it should still tell parallel agents to pin their own `TEST_REDIS_URL=/<n>`.
- The `env.ts` doc comment says ioredis resolves `/0x1` to DB 0. That is correct (`parseInt("0x1", 10)` = 0), and the probe agrees.
