# Review of T-12-2 (round 1)

- Reviewer: platform-sre (co-reviewer) on Sonnet 5
- Author: backend-foundation on Sonnet
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git diff 6bfd318^..6bfd318 -- src/api/app.ts src/api/events.ts src/api/server.ts src/api/shutdown.ts src/db/migrate.ts src/lib/shutdown-timeout.ts src/worker/index.ts drizzle/0025_role_level_timeouts.sql` | full read, see checklist below |
| `grep -rn "pg_advisory_lock" src` | only `db/migrate.ts`, one fixed key (`468_241`), no collision with any other lock use in the repo |
| grep of `invai-infra/local/*.sql` and `docker-compose.yml` for prior `statement_timeout` | none — the role previously had **no** statement/lock/idle timeout at all; this migration is a net-new constraint, not a tightening of an existing one |
| Same `tsc`/`biome`/scoped-vitest evidence as the reviewer's file (own DB, `tsx src/db/migrate.ts` against a fresh DB, `0025` snapshot present in `drizzle/meta`) | clean |
| Cross-checked `invai-docs/research/11-platform-scale-playbook.md` lines 96–101, 217, 230–232 (the numbers and pattern this card implements) | migration matches the prescribed 15s/30s/5s/5min values and the "long jobs use `SET LOCAL`" escape hatch; one prescribed item (see findings) isn't carried into `migrate.ts` |

## Acceptance criteria (platform/infra angle only — see reviewer file for full table)
| # | Met? | Evidence |
|---|---|---|
| `/livez`/`/readyz`/`/health` | Yes | `/livez` truly makes zero calls (confirmed by reading `app.ts`, not just the test); this is the correct ECS/ALB split — an orchestrator won't bounce a healthy process over a DB blip, and `/readyz` still pulls it from rotation. Deploy-time wiring (ALB health-check path, ECS `stopTimeout`) is correctly left out of scope per wave.md. |
| Role-level timeouts sane | Mostly — one real interaction gap, not blocking | See findings. |
| SIGTERM drains within cap, no new work | Yes | `server.close()` (Node stops accepting new connections immediately; existing ones keep serving) and BullMQ `worker.close()` (pauses dispatch immediately, waits only for already-active jobs) both give "no new work" for free — this is documented, standard behavior of the libraries used, not something this diff has to implement itself, and the report's real manual run confirms a queued second job never started in either case. |
| Migrate advisory lock | Yes | Correct pattern: single connection (`max:1`) holds the session-level lock across extension-creation + migrate + reference-data, released in `finally`. Matches the T-1-5 review's root cause exactly (the race was on `CREATE EXTENSION`, now serialized). |

## Blocking findings
none

## Findings (risk, not blocking this round)
1. **`db/migrate.ts` (whole file) and `drizzle/0025_role_level_timeouts.sql:14-18`** — interaction between the new advisory lock and the new `invai`-role `statement_timeout=5min` isn't accounted for. `runMigrations`'s lock acquisition (`pool.query("select pg_advisory_lock($1)", ...)`) runs on the `invai` role, which after 0025 lands carries a 5-minute `statement_timeout`. Postgres counts time spent blocked waiting for a lock (including an advisory lock) against `statement_timeout`. So: if migration/deploy A legitimately runs longer than 5 minutes while holding the lock (a big backfill, a non-`CONCURRENTLY` index build), a second concurrent `runMigrations` call (a second ECS task deploying at the same time) does not "simply wait then no-op cleanly" as AC5 describes — its lock-wait errors out with `57014 query_canceled` once the 5-minute mark passes. AC5's own test only proves the fast-path (both calls finish in well under 5 minutes), so it doesn't exercise this. Concretely: two ECS tasks starting during a slow deploy → the losing task's migrate step throws instead of waiting, and (depending on how the deploy script handles a non-zero exit) could fail a rollout that would otherwise have succeeded once the first task finished.
   - Mitigating factors: rare in practice (no current migration approaches 5 minutes), and the existing `SET LOCAL statement_timeout` escape hatch documented in the same migration file for reports/purge jobs is the same fix a future long migration would need — it's just not spelled out for `migrate.ts` specifically.
   - Suggested follow-up (not this card): either give the migration connection `SET LOCAL statement_timeout = 0` for the duration of `runMigrations`, or add a comment in `migrate.ts` next to the lock acquisition pointing at this exact interaction, so the next person adding a slow migration isn't surprised.
2. **`db/migrate.ts` doesn't set its own session `lock_timeout`, per research doc §"expand/contract" (11-platform-scale-playbook.md:217): "MUST set `lock_timeout = '5s'` at the start of the migration session and retry on timeout."** The shipped design instead relies on `invai`'s new 5-minute `statement_timeout` as an implicit backstop for any lock wait (DDL queued behind a long-running query), which is far looser than the "5s + retry" pattern the research doc calls MUST for exactly this scenario (a stuck DDL statement blocking every later query on that table). Not a regression (there was no timeout at all before), but a documented MUST isn't fully implemented and isn't flagged as a deviation anywhere in the report or commit message.
3. **Outbox relay** (`worker/outbox-relay.ts`, unchanged by this commit): runs under `withSystem`/`invai`, batch of 100 rows per transaction, normally sub-second — the new 5-minute cap gives it a large safety margin rather than a hazard. No issue found here; called out only because the card asked for it explicitly.

## Checks
- [x] Only owned/coordination paths changed
- [x] Nothing outside scope (ECS/ALB/CloudWatch items correctly deferred)
- [x] Tests exercise the behavior; no weakening found in this card's files (scan run, see reviewer file)
- [x] No tenancy/PII/money surface in this card
- [x] Decisions recorded (no-`invai_system`-role choice is documented in the migration file itself and the report)

## Optional notes (not blocking)
- Recommend logging finding #1 as a wave-12 follow-up (`wave.md` "Follow-ups") rather than reopening this card: add a code comment in `migrate.ts` and/or a `SET LOCAL statement_timeout = 0` around the lock+migrate block, and note in `12-security-quality-playbook.md`/`11-platform-scale-playbook.md` that migrations expected to run past 5 minutes need that override.
- Finding #2 is a documentation/rigor gap versus a MUST, not an observed failure; worth a one-line comment at minimum so a future reader doesn't assume `lock_timeout` protection exists on the migration session that isn't actually there.
