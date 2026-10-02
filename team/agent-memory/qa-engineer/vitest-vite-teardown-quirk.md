---
name: vitest-vite-teardown-quirk
description: A benign "close timed out ... Vite servers not exiting" message after invai-backend market suite runs, not a real test failure
metadata:
  type: project
---

Running `pnpm vitest run src/modules/market --reporter=dot` in `invai-backend` (observed 2026-10-01,
T-P4-5, 5 sequential foreground runs) ends every time with:

```
close timed out after 10000ms
Tests closed successfully but something prevents 2 Vite servers from exiting
```

Exit code was 0 and the test/file counts (5 files passed, 1 pre-existing conditional skip; 95
tests passed, 1 skipped) were identical and correct across all 5 runs.

**Why:** looks like a Vitest/Vite dev-server teardown quirk tied to this suite's dynamic
`import()` loader pattern (`load(JOBS)` in the acceptance files) or the per-run test DB/pool setup,
not a real hang — "Tests closed successfully" prints right before it.

**How to apply:** don't treat this message alone as a failure or chase it as a bug unless the exit
code is non-zero or a run actually hangs past the command's own timeout. Worth a look from
backend-foundation/platform-sre if it starts costing real wall-clock time, but it did not block or
flake this card's 5 runs.
