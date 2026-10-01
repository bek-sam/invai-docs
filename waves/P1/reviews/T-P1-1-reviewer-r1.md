# Review of T-P1-1 (round 1)

- Reviewer: reviewer on Opus 5.5. Author: backend-foundation on Opus 5.5 (card said sonnet). Commit `invai-backend@5649c7c`.
- Verdict: **changes-required**

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` / `pnpm lint` | exit 0 / `Checked 453 files`, no fixes |
| Two unpinned `pnpm test --reporter=dot` at once (`/tmp/p1a.log`, `/tmp/p1b.log`) while a third agent's run (pid 83035) was live | both `171 passed, 2 skipped (173)` files, `1368 passed`; got `invai_test_83303`/`_83302`, Redis DB 2/3; both DBs dropped afterwards |
| Registry poll of DB 15 every 2 s (`/tmp/p1reg.log`) | `lock:1 2 3 5` held until 20:43:54; **empty from 20:43:56** while runs 83035, 83302 and 83303 were all still alive |
| Pinned `TEST_DATABASE_URL`/`TEST_MIGRATION_DATABASE_URL`=`invai_rvw_test`, `REDIS_URL=…/10`, http + db-safety tests | 24/24 pass; `invai_rvw_test` migrated (91 tables); clients seen on db=10; no new `invai_test_<pid>`, no registry claim |
| `vitest run src/integrations/market/http.test.ts --reporter=verbose` | 8/8; "gives up…" 2 ms |
| tsx: `assertTestDatabase` on `%69nvai` (also pinned), `invai` | both REFUSE; `invai_test_123` allowed |
| Fresh `runMigrations` on a scratch DB (first-creation cost vs 30 s `lock_timeout`) | 3.7 s under load |
| `pg_database like 'invai_test%'` after | `invai_test_tpl`, `invai_test`, `invai_test_t230`, `invai_test_85388` (another agent's live run) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | Per-run clone seen; one advisory lock around ensure, migrate, sweep and clone; `provide`/`inject` reaches the workers (runs isolated) |
| 2 | **No** | Claim logic is right, but the run's own test file deletes every live claim (finding 1), so a later run can take a DB that is in use |
| 3 | Yes | Pinned run above |
| 4 | Yes | Code plus `test-db.test.ts` sweep and lookalike tests (passed in both runs); the template and unmarked DBs are never matched |
| 5 | Yes | tsx refusals above; 3 new cases in `db-safety.test.ts` |
| 6 | Yes | 2 ms; the error assertion is kept and `toHaveBeenCalledTimes(3)` is added; `unstubAllGlobals` is in `afterEach` |
| 7 | Partly | Both runs passed with nothing left behind, but isolation fails once a third run starts after the wipe (finding 1) |
| 8 | Yes | The replacement text is in the report (fix finding 1 before the tech lead retires the rule) |

## Blocking findings
1. `src/test/test-redis.test.ts:20-30` (`clearRegistry`, `KEYS test-redis-db-lock:*` then `DEL`, in `afterEach`) deletes **every** claim in the real DB-15 registry, including its own run's and every other live run's. I saw this happen: the registry went empty at 20:43:56 with 3 runs still alive. Failure: agent X holds DB 1 and agent Y's suite reaches this file, which wipes X's lock; agent Z then starts `pnpm test`, `SET NX` on `lock:1` succeeds, and X and Z share DB 1. `queues.test.ts`/`fairness.test.ts`/`reset.test.ts` `obliterate` then wipe each other's queues, the exact collision B-228 fixes. The same file also asserts `held toEqual([])` (line 69), which fails whenever another run holds a claim, and line 79 fills all 14 slots for 60 s, so a run starting then fails setup. The gate (`invai-infra/scripts/gate/lib.sh:228`, TEST_REDIS_URL=/15) runs this file too. Fix: point the tests at their own registry (inject the registry DB or key prefix into `claimTestRedisDb`), or delete only the keys and tokens the test created, and never assert on global registry state.

## Checks
- [x] Only owned paths changed: 13 files, `.env.example` comment lines only (late grant); `package.json`/`env.ts` untouched
- [x] Nothing outside scope
- [ ] Tests not weakened (none were; scan clean, the retry test is stronger), but the new registry test is destructive to shared state (finding 1)
- [x] Tenancy/idempotency/money/i18n: n/a (test infra only)
- [x] Decisions: listed in the report; nothing cross-cutting

## Optional notes (not blocking)
- The DB-15 registry overlaps with the gate's `TEST_REDIS_URL=/15` and with `env.ts:170`'s fallback, so README's "DB 15 is never a test target" is false for the gate. Harmless once finding 1 is fixed; move the gate off /15 later (infra).
- A crashed run keeps its Redis slot for the 2 h TTL, and a claimed DB is not flushed, so it inherits the last run's BullMQ keys (DB 10 had 64 stale keys). If `globalSetup` throws after claiming, nothing releases the claim (the DB is swept after 1 h).
- The `test-db.test.ts` stale-sweep test uses a fixed `invai_test_999999998`, so two runs reaching it at once can race. `--pool=threads` would make the in-test `invai_test_<pid>` equal the run's own DB.
- Not this card's: other agents' uncommitted T-P1-4 files are in the tree; both full runs passed with them, and I saw no failures there.
- Processes: my runs (pnpm 83286/83288, vitest 83302/83303) exited on their own; my registry watcher 83514 was killed; `invai_rvw_test` was dropped; the dev DB was untouched; Redis DB 0 was never used.
