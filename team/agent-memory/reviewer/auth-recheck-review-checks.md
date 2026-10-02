---
name: auth-recheck-review-checks
description: How to review a periodic re-check-and-revoke SSE/stream auth card (T-P6-2 style) - two-step mutation proof plus a live sign-out probe
metadata:
  type: feedback
---

2026-10-01 T-P6-2 r1 (approve): reviewing a long-lived-connection re-auth feature (SSE `/events`
dropping `?token=` and closing streams on revoke every ping).

- Red-on-base alone (new test file against the pre-change export) often just crashes on a missing
  export (`createEvents is not a function`, 0 tests run). That proves nothing about whether the
  tests discriminate real behavior. Do a second, stronger proof: hand-write a minimal shim in the
  base-commit worktree that adds *only* the new export's shape (e.g. an injectable `pingMs`
  param) with none of the new auth logic, and run the test file against that. Here it produced
  8 failed / 3 passed, and the 3 passes were exactly the behaviors the card says are unchanged
  (Bearer still 200, still-valid session keeps pinging, shutdown path unchanged) — that is the
  real discriminating proof, not the crash.
- For a "fail-open vs fail-closed on an ambiguous signal" ruling (here: architect ruling C1, a DB
  probe gates whether a failed recheck means "revoked" or "unknown/DB down"), mutation-test it
  directly in the head-commit worktree: change the one line that reads the probe result to always
  return the "revoked" branch, rerun the suite, and check exactly one test fails (the one that
  exists to catch this). If more or fewer than one test fails, the guard isn't tested the way the
  card claims.
- A live probe is cheap and convincing for this class of card: sign in for a cookie, open the
  SSE stream in the background with `curl -N ... > out & `, call the real sign-out endpoint, then
  poll the output file in a loop (not a flat `sleep N`) until `unauthorized` appears or a deadline
  passes. Confirms the real ping interval and the no-`retry:` claim without needing the floor PIN
  flow.
- The `Write` tool is blocked outside reviewer-owned paths even under `/tmp` (guard-paths.py
  matches the literal path, not just paths inside a repo) — use the `Bash` tool with a heredoc
  (`cat > /tmp/... << 'EOF' ... EOF`) to create scratch files for worktree mutation tests instead.
- `pnpm test` can show 1-2 unrelated failures on one run and be fully green on an immediate rerun
  with no code change — shared dev-infra contention (see [[shared-infra-contention-review]]), not
  a regression; rerun once before treating a full-suite red as real, especially when the touched
  test file itself was green in both runs.

**Why:** a crash-based red-on-base proof and an untested "fail open" ruling are both easy to miss
from the report alone; they need their own quick reproductions.
**How to apply:** any card that re-validates a long-lived connection/session on a timer, or that
has an explicit fail-open/fail-closed ruling from the architect baked into one branch of a
condition.
