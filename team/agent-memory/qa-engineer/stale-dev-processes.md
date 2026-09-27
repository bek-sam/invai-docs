---
name: stale-dev-processes
description: Long-lived local sessions accumulate orphaned tsx-watch api/worker processes; clean them up individually by PID before a golden-path gate, never touch 31xx ports.
metadata:
  type: project
---

Before a `run-golden-path` gate, `lsof -iTCP:3000-3199 -sTCP:LISTEN -P` and
`ps aux | grep -E '[t]sx (watch )?src/(api/server|worker/index)'` can show several stale,
multi-hour-old `tsx watch src/api/server.ts` and `tsx watch src/worker/index.ts` processes
accumulated from earlier sessions (a `pnpm dev` orchestrator plus orphaned worker watchers spawn
new child processes without the old ones dying). One 2026-09-27 gate found 6 live worker children
and 2 separate api-watch chains (one on :3000, one on :3142).

**Why:** these are genuinely stale/orphaned, not necessarily another agent's session — but a
process bound to a 31xx port matches the pattern for another agent's dedicated verification API
(`PORT=31xx pnpm dev:api`, `CLAUDE.md`), so it must never be killed without asking the tech lead,
even if it looks idle.

**How to apply:** kill only processes on the gate's own ports (3000, 5173, 5174, 8000) and any
plain worker watchers, by individual PID (never `pkill`/`killall`, which is also blocked by the
agent brief). Record every PID you stop. Leave any process on a 31xx port alone and note it in the
gate report for the tech lead to check ownership, even if it looks idle — see
[[respect-ownership-ports]].
