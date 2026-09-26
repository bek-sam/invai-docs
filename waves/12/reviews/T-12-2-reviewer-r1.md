# Review of T-12-2 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: backend-foundation on Sonnet
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend diff 6bfd318^..6bfd318 --stat` | 14 files; all within owned/coordination paths (app.ts, events.ts, server.ts, shutdown.ts (new), migrate.ts, shutdown-timeout.ts (new), worker/index.ts `shutdown()` region, migration 0025 + meta) |
| `git archive 6bfd318` into `/tmp/review-T-12-2`, symlinked `node_modules` | clean snapshot, isolated from other agents' uncommitted wave-12 work in the live tree |
| `./node_modules/.bin/tsc --noEmit` | clean, no errors |
| `./node_modules/.bin/biome check src drizzle` | "Checked 276 files... No fixes applied" |
| Own DB `invai_test_review122r1` (created fresh, not templated), own Redis db 14; `tsx src/db/migrate.ts` against it | `[migrate] up to date` — advisory lock path exercised on a fresh DB |
| `perl -e 'alarm 120; exec @ARGV' vitest run src/api/health.test.ts src/db/migrate.test.ts src/db/timeouts.test.ts src/lib/shutdown-timeout.test.ts` | 4 files, 11 tests passed |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend origin/main` | hits are all outside T-12-2's files (T-12-1/T-12-3/T-12-4 in-progress work sharing the tree) or are legitimate failure-injection mocks in `health.test.ts` (db.execute rejected to prove `/livez` skips it) — no weakening in this card's files |
| Dropped `invai_test_review122r1`, removed `/tmp/review-T-12-2` | clean |

Note: local Postgres/Docker was under heavy contention from other concurrently-running wave-12 agents for part of this review (docker exec / createdb queued for ~39 min); I killed my own stuck `createdb -T invai` (never other agents' PIDs) and switched to an empty CREATE DATABASE instead of templating from the live `invai` DB. Contention cleared on its own; the shared DB was left usable.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. `/livez` vs `/health` vs `/readyz` | Yes | `app.ts`: `/livez` = `c.json({ok:true})`, no `checkDb`/`checkRedis` calls; `/readyz` shares `checkDb`/`checkRedis` with `/health`, 503 iff either down; `/health` unchanged. `health.test.ts` proves DB-down → `/health` and `/readyz` 503, `/livez` 200 in <50ms with the db spy never called. |
| 2. DB role-level timeouts | Partly — sane defaults, real interaction risk not covered by tests (see notes) | `drizzle/0025_role_level_timeouts.sql` sets `invai_app` 15s/30s/5s and `invai` (documented stand-in for "system" role, no separate role exists) 5min. `timeouts.test.ts` confirms both role defaults and that Postgres cancels a 150ms-capped query with `57014`. |
| 3. Graceful SIGTERM — API | Yes (manually verified, no committed integration test) | `server.ts` drains via `withShutdownCap`, `DRAIN_TIMEOUT_MS=10s`; `events.ts` wakes SSE loop on `shuttingDown` and sends `retry: 1000`. Report documents a real SIGTERM run showing the SSE client receiving the shutdown event before the stream closed. No committed test exercises the actual process-level drain (only the generic `shutdown-timeout.test.ts` unit test of the shared cap). |
| 4. Graceful SIGTERM — worker | Yes (manually verified, no committed integration test) | `worker/index.ts` `shutdown()` races `Promise.all(workers.map(w=>w.close()))` against `SHUTDOWN_CAP_MS=20s`; force-exits at the cap with the job still active. Same gap as #3 — no committed test proves the real worker+BullMQ wiring, only the shared helper's unit test and an uncommitted manual script (per report). |
| 5. Migrate advisory lock | Yes | `migrate.ts`: `pg_advisory_lock`/`unlock` in try/finally around extensions+migrate+reference data, single `Pool({max:1})`. `migrate.test.ts` runs two concurrent `runMigrations` against a scratch DB and checks for exactly one `pg_trgm` extension and one `companies` table. I additionally ran a single migrate against a fresh DB directly and confirmed the lock path executes cleanly. |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat`) — matches wave.md's T-12-2 row; `events.ts` is flagged out-of-owned-path in the report and the tech lead approved it after the fact (wave.md "Grants")
- [x] Nothing outside scope
- [x] Tests exercise the behavior; scan found no weakening in this card's files
- [x] Tenancy/idempotency/money/en-es N/A to this card (no tenant tables, no money, no user-facing text touched)
- [x] Decisions recorded where needed (report's "Decisions" section covers the no-`invai_system`-role and unwired-env-var calls)

## Optional notes (not blocking)
- **AC3/AC4 lack a committed automated test of the real drain wiring.** Both are only proven by `lib/shutdown-timeout.test.ts` (generic, matches the AC3/4 shape well) plus the report's manual, uncommitted verification. A real SIGTERM-to-subprocess test (spawn the built server/worker, send SIGTERM, assert on stdout/exit code) would close this gap and survive a future refactor of `server.ts`/`worker/index.ts` that a reviewer might not re-verify by hand. Suggest a follow-up card, not a block — process-level signal tests are awkward in this stack and the shared helper is solidly covered.
- See the platform-sre co-review for the migration-0025-interaction risk (advisory lock wait vs. `invai`'s new `statement_timeout`) — a real but narrow edge case, not a blocker for this round.
