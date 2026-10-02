---
name: seed-worker-race-review
description: How to review "seed/bulk job safe beside a running worker" and "reset drains queues" cards (T-20-5): scheduled sweeps race, MONITOR proof, reset.ts env trap
metadata:
  type: feedback
---

2026-09-28 T-20-5 r1 (changes-required):
- A fix that holds the outbox only covers event-driven jobs. `upsertJobScheduler` sweeps also
  fan out over every company, and BullMQ 6 `every` schedulers fire right away and then each
  tick. Reproduce a race deterministically: enqueue the sweep job (e.g. `today.alertsSweep`)
  from a scratch `.mts` when the seed log shows the phase you want (poll `grep -c`). That caught
  a `stock_low` alerts unique violation in about 1 minute.
- `src/db/reset.ts` resets `MIGRATION_DATABASE_URL`, not `DATABASE_URL`. Override both when
  pointing it at a copy, or you wipe the shared dev DB.
- The strongest proof that nothing else in Redis was touched is a bounded
  `perl -e 'alarm 25; exec @ARGV' docker exec local-valkey-1 timeout 20 valkey-cli monitor >file`
  around the command, then group DEL/UNLINK lines by `[db addr]`. Comparing dbsize is noisy
  because other agents write to it.
- Check the assigned Redis DB before using it (`dbsize`, `client list | grep db=N`). DB 10 was
  busy with another agent, so I used an empty DB and said so in the review. The guard hook
  blocks `pkill` even inside a container (`docker exec ... pkill`).
- Before blocking on "the test obliterates the shared Redis DB", grep for existing
  `obliterate(` in tests. Several already did it, which made it a non-blocking note.

**Why:** these were the non-obvious traps and the finding the author missed on the first
seed/worker race card.
**How to apply:** any card about seed, bulk builders, reset, queues or "safe while the worker
runs". See also [[env-backend-worktree-review]].
