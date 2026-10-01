# T-P6-1: `db:reset` refuses to wipe shared queues; the seed refuses to overwrite the shared `seed-output.json` (B-219)

| Field | Value |
|---|---|
| Wave | P6 |
| Scope ref | `always-in-scope: bug` (dev tooling wiped the shared dev Redis DB 0 queues twice: 2026-09-29 T-23-9, 2026-10-01 T-P5-1; a scratch seed overwrote the shared `seed-output.json` in P5) |
| Spec | backlog B-219; `waves/P5/wave.md` build log and retro; lessons 2026-10-01 P5 |
| Owner | backend-foundation |
| Reviewer | reviewer (opus) |
| Co-reviewers | none |
| Risk flags | none (dev tooling only; no product code, no schema) |
| Model | sonnet |
| Depends on | nothing |

## Owned paths (edit)
- `invai-backend/src/db/reset.ts`, `invai-backend/src/db/reset.test.ts`
- `invai-backend/src/db/seed/index.ts` (only the output-file guard; nothing else in the seed), plus a new small test file under `invai-backend/src/db/seed/` for the guard
- `invai-backend/README.md` (the db:reset / seed lines only, if they mention the env vars)

## Read-only paths
- everything else, including `src/db/seed/builder.ts` (T-P6-4 will own it later), `src/api/**` (T-P6-2), `src/env.ts`, `src/lib/**`, `invai-infra/**` (its `scripts/gate.sh` resets `invai` with the default `REDIS_URL` and must keep working unchanged)

## Acceptance criteria
1. `pnpm db:reset` against the shared dev DB `invai` (database name exactly `invai`) behaves as today with any `REDIS_URL`, including the default (no path = DB 0). The gate (`invai-infra/scripts/gate.sh:108`) and CI (`.github/workflows/ci.yml`, `e2e.yml`, both on `invai` and `redis://localhost:6379`) keep working with no change.
2. `pnpm db:reset` against any other database refuses **before touching Postgres or Redis** (exit code non-zero, nothing dropped, no queue obliterated) when `REDIS_URL` has no explicit DB index or its index is 0. The message says what to do, for example: `[reset] refusing: resetting invai_p6_reset would wipe the queues in the shared Redis DB 0. Set REDIS_URL=redis://localhost:6379/<n> (n = 1-15) for this database.`
3. With an explicit non-zero index (`redis://localhost:6379/13`) a reset of another database works and obliterates only that DB's queues, as today.
4. The seed refuses (exit non-zero, before any insert) when the target database is not `invai` and `SEED_OUTPUT_FILE` is unset, with a message naming the variable. With `SEED_OUTPUT_FILE` set, or on `invai`, it behaves as today. (Decide the cheapest safe check point; a refusal after a 15-minute seed is not acceptable.)
5. Architect R3 (added after start; the reviewer checks it, round 2 if missing): the reset guard runs only in reset.ts's main block (test setup and `migrate.test.ts` import `ensureDatabase` on `invai_test`); the seed guard refuses unless both `DATABASE_URL` and `MIGRATION_DATABASE_URL` point at `invai` or `SEED_OUTPUT_FILE` is set.
6. The checks are pure functions with unit tests (allowed and refused cases for both guards); each new test is red with the guard removed (say how you showed it).

## Verification
- Scratch DB `invai_p6_reset` only; `REDIS_URL=redis://localhost:6379/13` and `SEED_OUTPUT_FILE=/tmp/p6-1-seed-output.json` pinned before any command that resets or seeds. Never reset or seed the shared `invai` DB (other agents use it). Drop `invai_p6_reset` at the end.
- Exercise for real: (a) `MIGRATION_DATABASE_URL=…/invai_p6_reset REDIS_URL=redis://localhost:6379 pnpm db:reset` → refused, exit ≠ 0, `invai_p6_reset` tables still there and `valkey-cli -n 0 dbsize` unchanged before/after; (b) the same with `/13` → resets. (c) Seed guard: run the seed on `invai_p6_reset` with `SEED_OUTPUT_FILE` unset → refused at once, `invai-backend/seed-output.json` mtime unchanged.
- `pnpm typecheck && pnpm lint 2>&1 | tail -n 20` and `pnpm vitest run src/db/reset.test.ts src/db/seed --reporter=dot 2>&1 | tail -n 20` in `invai-backend`. The full suite runs at the gate.

## Out of scope
- B-249 and B-208 (T-P6-4), the gate script, any env schema change in `src/env.ts`, deriving the Redis DB automatically (refusing is the rule).

## Rules
- Role file `.claude/agents/backend-foundation.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/backend-foundation/`.
- Other agents at the same time: product-manager and architect (plan reviews, docs only); later backend-foundation on T-P6-2 (`src/api/events.ts`). Don't touch their files.
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** Foreground test runs only, with an explicit 600000 ms timeout on long calls; don't end your turn with a run or a process going. Record every PID you start and list it (stopped) in the report.
- Trim output (`2>&1 | tail -n 40`). Report (≤ 60 lines) to `invai-docs/waves/P6/reports/T-P6-1.md`, one line per milestone as you go.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
