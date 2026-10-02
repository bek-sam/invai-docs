---
name: orbstack-hang-midwave
description: Local Docker/OrbStack can hang mid-wave (Valkey + Postgres stop answering); what to do without breaking other agents
metadata:
  type: project
---
2026-09-30 T-A4: Valkey stopped answering PING and Postgres accepted TCP but timed out queries; `docker` CLI hung too, so vitest froze at start and curls hung.
**Why:** `orb stop && orb start` restarts every agent's shared services.
**How to apply:** probe with `perl -e 'alarm 6; exec @ARGV' sh -c 'printf "PING\r\n" | nc -w 3 localhost 6379'`; if hung, stop only your own PIDs/background tasks and report to the tech lead; don't restart OrbStack yourself in a shared wave.
