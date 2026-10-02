---
name: shared-infra-contention-review
description: A flaky test failure during review turned out to be shared-infra (Postgres/Redis/OrbStack) contention from concurrent agents, not a code defect — how to tell the difference and recover
metadata:
  type: feedback
---

2026-09-28 T-20-1 r1 (changes-required, but for a different reason):
- A test that fails on the first full-glob run but passes 100% clean when re-run alone twice, right
  after another agent's `vitest` process is seen running against the same shared Postgres (`ps aux`
  showed a second DB name like `invai_t20_revint`) is very likely resource contention, not a real
  bug — especially for tests using `vi.useFakeTimers`/global non-tenant caches
  (`market_series_cache`, ADR 0015) where a corrupted/timed-out query under connection-pool
  pressure can produce a wrong-but-plausible result once and never again. Don't chase the exact
  mechanism for more than ~15 min of tool time; re-run alone, cleanly, twice, and treat "clean both
  times" plus "another agent's process is present" as sufficient evidence it isn't the diff.
- `docker ps` failing with "no such file or directory" on the OrbStack socket mid-review means
  OrbStack itself crashed (`orb status` → `Stopped`), usually from combined load of several
  parallel heavy `vitest` runs (mine + another agent's) hammering the same Postgres/Redis. Recovery
  is exactly `CLAUDE.md`'s documented fix: `orb start`, then `docker compose up -d` in
  `invai-infra/local` — data volumes survive, and this restores the shared environment for every
  agent, not just the reviewer's own run. Do this promptly; it's normal recovery, not an escalation.
- Lesson for my own conduct: don't run more than one heavy DB-backed `vitest` batch of my own at a
  time in the background — I compounded the contention above by starting a second background batch
  while the first was still running. One at a time, waited out fully, is both cheaper in tokens and
  avoids being a second cause of the same crash I was diagnosing.
- When a card's own `wave.md` grants are visible and another required co-reviewer (e.g.
  product-manager for a "wording rule" risk flag) has already filed a `changes-required` review
  with an exact fix and a cited, dated correction in the spec's change-log, treat that as
  authoritative evidence for my own verdict (re-verify it directly — here, `Intl.NumberFormat("es",
  ...)` vs `"es-US"` in `node -e` — rather than re-deriving the wording-rule judgment from scratch).
  My own verdict still needs its own evidence line, but I don't need to re-litigate a call already
  made by the risk flag's designated reviewer.

**Why:** the reviewer's own tool usage (parallel backgrounded test runs) plus another agent's
concurrent test run crashed the shared OrbStack VM mid-review, which then produced a misleading
"real" test failure that cost significant investigation time before the true cause (contention, not
a logic bug) was found.
**How to apply:** any review where a specified test-command re-run fails inconsistently with the
author's/other co-reviewers' reported results; run infra-recovery immediately if `docker ps`/`orb
status` shows the daemon down, and keep heavy backgrounded test runs to one at a time.
