---
name: mock-carrier-transit-hours
description: hand-starting API/worker outside invai-infra's dev.sh misses MOCK_CARRIER_TRANSIT_HOURS, so the shipping golden-path step times out at the default 60s poll
metadata:
  type: project
---

2026-10-01 T-P7-1: `invai-infra/scripts/dev.sh` sets `MOCK_CARRIER_TRANSIT_HOURS=0.001` so the mock carrier's
"in transit" scan happens almost immediately; `invai-backend/src/modules/shipping/service.ts:106` reads it
once at module load (`Number(process.env.MOCK_CARRIER_TRANSIT_HOURS ?? 2)`), so it must be set *before* the
API/worker process starts, not just before a request. Hand-starting the API/worker directly (`tsx
src/api/server.ts` / `src/worker/index.ts`) for a scratch stack, instead of `pnpm dev:all`, misses this var —
the golden-path suite's step 9 ("item shipped (carrier scan)") then times out waiting at the real 2h default.

**Why:** the var is read once at import time, not per-call, so setting it mid-run does nothing; only a fresh
process start picks it up.
**How to apply:** when hand-starting API/worker for a scratch stack (not via `invai-infra`'s `dev:all`),
always export `MOCK_CARRIER_TRANSIT_HOURS=0.001` first. If step 9 times out, check this before suspecting a
product bug.
