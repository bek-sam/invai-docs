---
name: gate-rootcause-trace-first
description: Root-cause E2E gate failures from the Playwright trace network log (status codes) before timing/load hypotheses; floor 429 looked like offline/timeout
metadata:
  type: feedback
---
Ask QA to read the failing test's trace network log (HTTP status codes) first, before forming any timing or contention hypothesis.

**Why:** In P1 and P2 the floor `press.spec.ts` failure was blamed first on a timeout and then on preview-job DB contention. The real cause was an HTTP 429 from the rate-limit middleware, which the floor shows as "offline". The middleware rejects the request before any handler runs, so handler duration logs never saw it (B-236, waves/P2/reports/gate-rootcause.md).

**How to apply:** When a gate step fails, the root-cause prompt asks for the trace's status codes. Separately: before starting a round 2 builder, stop the round 1 builder, because its leftover full-suite runs hold test Redis DB 15 and the gate refuses to start.
