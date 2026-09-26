# T-12-2 report: health, timeouts and graceful shutdown

Status: **done, not pushed.** Built on T-12-1's `319027a`. Ran in parallel with T-12-3 (rate
limits/fairness) and T-12-4 editing the same shared files at the same time; every hunk below was
staged with `git apply --cached` against a hand-cut patch, not `git add`, and verified against
`git diff --cached` to make sure only my lines went in (details in "Concurrent edits" below).

## Acceptance criteria and their tests

1. **`/livez` vs `/health` vs `/readyz`.** `app.ts`: `/livez` returns `{ ok: true }` with zero
   DB/Redis/imaging/S3 calls. `/readyz` reuses the same `checkDb`/`checkRedis` helpers `/health`
   now shares, without imaging/S3 (those degrade a feature, not whether the instance should take
   traffic): 503 when either is down, 200 otherwise. `/health` is unchanged (checked by the
   existing test). `health.test.ts`: with `db.execute` mocked to reject, `/livez` still 200 in
   under 50ms and never calls the mock; `/health` and `/readyz` both 503; a healthy `/readyz` is
   `{ ok: true, db: true, redis: true }`.
2. **DB role-level timeouts.** New migration `drizzle/0025_role_level_timeouts.sql`:
   `invai_app` gets `statement_timeout = '15s'`, `idle_in_transaction_session_timeout = '30s'`,
   `lock_timeout = '5s'`. There's no separate `invai_system` login role in this setup (checked
   `invai-infra/local/init.sql` and `db/client.ts`) — `invai`, the owner role used by
   `systemPool`/`withSystem`/migrations/the outbox relay/reports jobs, **is** the "system/reports
   role" the card means; it gets `statement_timeout = '5min'`. `db/timeouts.test.ts`: two tests
   read `current_setting(...)` as each role and assert the exact values; a third opens a
   transaction, sets `SET LOCAL statement_timeout = '150ms'` (standing in for the role default so
   the test doesn't wait 15 real seconds) and runs `select pg_sleep(2)` — Postgres cancels it in
   ~150ms (`cause.code === "57014"`, `query_canceled`), the error surfaces through drizzle as a
   normal `DrizzleQueryError` well before 1s, not a hang. I did not write a `lock_timeout`-specific
   test: proving Postgres enforces `lock_timeout` on its own lock manager isn't code this task
   ships, and the two easy ways to test it (advisory locks held on a *different* pooled
   connection than the one that releases them, or `LOCK TABLE` on a revoked-privilege global
   table) were both fragile enough to skip; the role-default check already confirms the value (5s)
   is actually set.
3. **Graceful SIGTERM — API.** `server.ts`: on SIGTERM/SIGINT, `beginShutdown()` (new
   `api/shutdown.ts`) fires first, then `server.closeIdleConnections()`, then `server.close()`
   raced against `DRAIN_TIMEOUT_MS = 10s` via the new shared `lib/shutdown-timeout.ts`
   (`withShutdownCap`). Below the cap: clean exit 0. At the cap: `closeAllConnections()` then
   exit 1.
4. **Graceful SIGTERM — worker.** `worker/index.ts`'s `shutdown()` (my region only, per
   `wave.md`; T-12-3 owns the `Worker` processor line in the same file — see "Concurrent edits").
   `Promise.all(workers.map(w => w.close()))` (force=false, waits for each active job) raced
   against `SHUTDOWN_CAP_MS = 20s` via the same `withShutdownCap`. Below cap: normal
   `closeQueues`/`closeDb`, exit 0. At cap: exit 1 immediately, skipping further cleanup, with
   the job still running.
5. **Migrate advisory lock.** `db/migrate.ts`: `runMigrations` takes `pg_advisory_lock` on a
   fixed key before `CREATE EXTENSION`/`migrate`/`ensureReferenceData`, releases it in a `finally`
   (survives a thrown error), all on the same connection (`Pool({ max: 1 })`).
   `db/migrate.test.ts`: creates a scratch fresh database, runs `runMigrations` twice
   concurrently against it, asserts both resolve without error and `pg_extension`/`pg_tables`
   show one clean copy each (not partial/duplicate), then drops the scratch database.

## Shared logic: `lib/shutdown-timeout.ts`

Both AC3 and AC4 are "wait for X to finish, but not past N seconds, and don't touch X if it's
still running when the cap hits." Factored that once as `withShutdownCap(work, capMs)`
(resolves `true` if `work` settles first, `false` at the cap without cancelling `work`), used by
both `server.ts` and `worker/index.ts`. Unit-tested directly with fake short timers
(`lib/shutdown-timeout.test.ts`, 20ms/200ms) — fast and exact, and it's the literal shipped
function, not a re-implementation.

## Real verification (not just unit tests)

- **API + SSE, for real.** Started the real `api/server.ts` against `invai_test_t122`/Valkey
  db 13 on :3122. Minted a floor session directly via `createFloorSessionToken` (skipping full
  PIN login) against a seeded company/station, opened `/events?token=...` with `curl -N`, then
  sent a real `SIGTERM` to the process. Result: `[api] draining` → `[api] exiting
  {"forced":false}` within ~1s (not the 25s ping cycle), and the curl output shows the client
  actually received `event: shutdown` / `retry: 1000` before the stream closed. `/livez` and
  `/readyz` also hit for real (200s) beforehand.
- **Worker, for real, mid-job.** A throwaway script (not committed) built one real BullMQ
  `Worker` against real Redis db 13, using the actual shipped `withShutdownCap`, self-sending
  `SIGTERM` ~1s after a job started so timing didn't depend on manual multi-second tool-call
  latency. Two runs:
  - `capMs=15000, jobMs=4000`: SIGTERM at +1003ms, job **kept running** and finished normally at
    +4004ms, `closedInTime=true`, exit 0. The second, already-queued job never started (no log
    line for it at all) — closing stops new dispatch immediately even though it waits for the
    active job.
  - `capMs=1500, jobMs=8000`: SIGTERM at +1006ms, `closedInTime=false` at +2509ms (~cap), exit 1,
    with the 8s job still active (never printed "finished") and, again, no third job ever
    started.
  First attempt at this hit real flakiness worth recording: `kill -9` on the `tsx` wrapper PID
  left its actual child process (a second PID, the real script) running and still holding a
  BullMQ lock, so a later run's job stalled for ~2 minutes waiting for BullMQ's stalled-check to
  reassign it — a process-management mistake on my end (this machine runs several other agents'
  dev servers too), not a bug in the shipped code. Killed both PIDs, flushed the scratch queue's
  keys from Redis db 13, reran clean.

## Concurrent edits (T-12-3 landed at the same time)

`app.ts` and `worker/index.ts` are wave.md's named coordination files, and both had a second
agent's uncommitted changes sitting in the working tree while I worked (T-12-3: `orpc.ts`,
`auth.ts`, `queues.ts`, `ratelimit.ts`, new `fairness.ts`, plus a `ResponseHeadersPlugin` import
and constructor change in `app.ts`, and a `withFairness`-wrapped processor in `worker/index.ts`).
Neither file's hunks overlapped mine at the line level. I never ran `git add <file>` on either —
I diffed, hand-cut a patch containing only my hunks, `git apply --cached --check`'d it, applied
it, then re-diffed both staged and unstaged to confirm the split before committing. `git diff
--cached` for both files shows only my lines; `git diff` (unstaged) shows only theirs, untouched.

## Out-of-owned-path edit (needs the tech lead's OK)

- **`src/api/events.ts`** (not listed as an owned or coordination file for this card): the SSE
  ping loop now races its 25s sleep against a new `shuttingDown` promise
  (`api/shutdown.ts`) so a connection wakes immediately on SIGTERM instead of at the next ping,
  sends `event: shutdown` with `retry: 1000`, unsubscribes, and lets the stream close normally.
  Without this, AC3's "close SSE streams with a retry hint" would either not exist or make
  `server.close()`'s drain wait the full un-bounded SSE lifetime every time. Small, isolated,
  same pattern T-12-1 used for its `worker/index.ts` grant (own commit, flagged here). Verified
  for real above.

## Decisions (and why)
- **No `invai_system` role.** The research doc's suggested role name doesn't exist in this repo;
  creating one is an infra change (`invai-infra/local/init.sql` + a real deploy-time role in AWS,
  out of this card's scope per wave.md's AWS-deferred list) I didn't make. `invai` already plays
  that part for every system/cross-tenant path that exists today.
- **`DRAIN_TIMEOUT_MS = 10s`, `SHUTDOWN_CAP_MS = 20s`.** Not wired to an env var: `env.ts` isn't
  an owned or coordination file for this card, and every existing production knob for these
  numbers is deploy-time AWS config (ECS `stopTimeout`) that's explicitly out of scope this wave.
  Plain constants in the owned files, easy to promote to env vars later.
- **`process.exit(1)` on a forced/timed-out shutdown, `0` on graceful.** Not required by the AC,
  but free and useful for anyone watching exit codes in a deploy.

## Verification
- `tsc --noEmit`: clean. `biome check` on my files only (`pnpm lint` fails repo-wide on an
  unrelated uncommitted formatting issue in `src/db/seed/index.ts`, not mine and not staged).
- Full backend `vitest run` on `invai_test_t122`, `REDIS_URL=.../13`: **90 files, 645 tests
  passed** (tree also had other agents' uncommitted wave-12 work, per above).
- Real runs: see "Real verification" above. Cleanup: all my processes stopped (checked `ps`
  after each), the scratch shutdown-verify script and its Redis keys removed, `invai_test_t122`
  left in place per the card's own instruction (tests re-migrate it idempotently; I did not
  drop it since T-12-1/3/4 may still be relying on their own DBs existing independently — mine
  is `invai_test_t122` specifically and isn't shared, so I'll leave dropping it to whoever runs
  the final gate unless told otherwise).

## Cross-card notes
- **T-12-3:** confirmed no overlap in `worker/index.ts` — you own the `Worker(...)` processor
  line (now wrapping `processJob` in `fairProcessJob`), I own `shutdown()`. Same for `app.ts`:
  your `ResponseHeadersPlugin` wiring and my `/livez`/`/readyz` sit in different hunks.
- **T-12-4:** no interaction seen in the files I touched.
- **Follow-up (not built):** `DRAIN_TIMEOUT_MS`/`SHUTDOWN_CAP_MS` should eventually match the
  real ECS `stopTimeout` once that's set (wave 10/11); until then they're just sane local
  defaults.
