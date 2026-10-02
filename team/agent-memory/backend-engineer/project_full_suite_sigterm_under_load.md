---
name: project-full-suite-sigterm-under-load
description: invai-backend's full pnpm test can get SIGTERM'd (exit 143) mid-run on a loaded shared machine, with no FAIL in the log — not a real test failure.
metadata:
  type: project
---

On a machine running several wave agents' test suites at once (seen: 15G/16G RAM used, swap
compressor active, another agent looping `pnpm vitest run src/modules/market` 4-5x), a
foreground-then-backgrounded `pnpm test --reporter=dot > log 2>&1` for the full invai-backend
suite was killed with exit 143 (SIGTERM) partway through — thousands of lines in, no test
failures printed, just transient `ECONNREFUSED`/`redis timeout` lines from the shared Valkey
under load (the rate-limiter and fairness-semaphore code already fail open on those, by design).
No "Test Files"/"Tests" summary line ever printed, which is the tell that it was killed, not that
the suite actually finished and failed.

**Why:** found during T-P3-4's DoD gate. A piped run (`| tail -n 40`) had earlier reported exit 0
even though the underlying pnpm process had failed/been killed — the Stop hook's warning about
pipes hiding exit codes is real; `set -o pipefail` plus a trailing `echo EXIT:$?` is what caught
it the second time.

**How to apply:** don't read "ELIFECYCLE Test failed" + no FAIL lines as a real red suite — check
whether a `Test Files .. passed/failed` summary line exists at all first. If it's missing, the
run was killed, not failed; retry (preferably `nohup ... & disown` to detach from the calling
shell) once other agents' heavy test runs have finished, rather than trying to "fix" a
nonexistent failure. If retrying still doesn't finish before you must hand off, say so honestly
in the report (don't claim "pass") and name the PID/log for whoever follows up to check.
