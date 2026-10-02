---
name: wave-p6-t1-round2-dual-url-guard
description: T-P6-1 round 2 fix (B-219) — seed guard must check both DATABASE_URL and MIGRATION_DATABASE_URL, and a live-check gotcha with importing src/db/seed/index.ts
metadata:
  type: project
---

T-P6-1 round 1's `assertSafeToSeed` checked only `MIGRATION_DATABASE_URL`. Reviewer (r1) found a
mixed env (DATABASE_URL scratch, MIGRATION_DATABASE_URL pinned to `invai`, or the reverse) passed
the guard, because the seed writes through two pools: `systemDb` (MIGRATION_DATABASE_URL) and
`auth`/`signUp` (DATABASE_URL, `src/db/client.ts`). Fixed by taking both URLs and requiring both
to name `invai` (or `SEED_OUTPUT_FILE` set).

**Why relevant later:** any guard or check that gates a multi-pool script (seed, a future
migration helper) must check every pool the script actually writes through, not just the one
most visible at the top of `main()`. Grep for every `systemDb`/`db`/`auth.api` usage in the script
before trusting a single env var names the whole blast radius.

**Live-check gotcha:** calling `tsx` on a one-off script that `import()`s `src/db/seed/index.ts`
(even just to reach the exported pure function) runs all of that file's top-level imports,
including `market-demand.ts`'s scheduler registration against Redis. On a shared dev box with
several agents running concurrent seeds/worktrees, that import can stall with zero output for
minutes — looks like a hang, not an error. Give any such probe script an internal hard deadline
(`setTimeout(() => process.exit(2), 15000)`) so it always self-terminates; don't rely on the Bash
tool's command timeout alone, since a backgrounded hang still leaves a live node process you then
have to find and stop with `TaskStop`/`kill` by exact PID.

Related: [[wave-p6-t1-safe-reset-seed]] (round 1, B-219).
