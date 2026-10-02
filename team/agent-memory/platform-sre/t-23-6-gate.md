---
name: t-23-6-gate
description: Design of invai-infra's pnpm gate (scripts/gate.sh + scripts/gate/lib.sh) and a lesson about a concurrent-instance collision while building it
metadata:
  type: project
---

`pnpm gate [repo...]` (T-23-6) is one entry point `invai-infra/scripts/gate.sh` sourcing a single
`invai-infra/scripts/gate/lib.sh` (functions: `default_repos`, `check_preconditions`,
`check_golden_path_ports`, `run_suite`, `write_stamp`, `wait_healthy`/`wait_http_ok`, a
`cleanup`/EXIT trap over `STARTED_PIDS`). That's the adopted convention for this directory — not
several separate step scripts. T-23-7 (GitHub Actions) should call into these same functions rather
than re-splitting them into files.

`guard-bash.py`'s push-stamp check (`_gate_check_push`) reads `invai-infra/.gate/pass.json`
(`{"repos": {"invai-<kind>": {"sha", "at"}}}`, per-repo timestamps, not one global time) and takes a
test-only override `INVAI_GATE_STAMP_PATH` read from the guard's own process environment (never
from the checked command's text) so hook tests can point at a scratch stamp file without touching
the real one. Tests: `.claude/hooks/tests/test_push_stamp.py` (not the git-tracked
`invai-docs/team/hooks/` mirror, since `.claude` isn't a git repo).

**Round 2 (review changes-required, all 5 findings fixed):** `guard-bash.py`'s push check now
threads a tracked cwd through `simple_commands`'s existing flattening pass (starts at the
session's own `cwd`, updates on literal `cd`/`pushd`, `CWD_AMBIGUOUS` sentinel on `popd`/`cd -`/an
unresolved `$var`; a `bash -c`/`eval`/`$(...)` body gets its own copy and never leaks its `cd`s
back out - correct subshell isolation for free from the existing recursion structure). A push
whose directory resolves to `CWD_AMBIGUOUS` is denied outright, not left to "nothing of ours to
gate" -> allow. `_gate_check_push` also now resolves the refspec's actual source
(`git rev-parse <src>^{commit}`) instead of always comparing local HEAD. `scripts/gate.sh`'s
`mapfile` (bash4+) became a `while read` loop over process substitution (see
[[bash32-empty-arrays]]). The golden-path dev:all stack now starts under `set -m` (its own process
group, PGID = PID) and is stopped via `kill -TERM -- -$pgid` (see the port-simulation proof this
actually frees ports, in the T-23-6 round-2 report). `write_stamp` now compares against a
START_SHAS captured before any suite ran, and refuses the whole run on a dirty tracked tree.
**Why:** all 5 were real bypasses/bugs the reviewer proved with commands, not style nits. **How to
apply:** this "thread state through the existing flattening pass, add a sentinel for
can't-resolve, and deny on the sentinel" pattern is reusable for any future guard rule that needs
to reason about "where does this command actually run", not just "what does it say".

**Lesson:** partway through this card, a supposedly "stalled, uncommitted" earlier instance turned
out to still be live in the background, independently writing the same files under the same names
I'd chosen (`scripts/gate/{refuse,repo-check,stamp,golden-path}.sh`) and, minutes later, committed
a complete, working `gate.sh`/`lib.sh` design and correctly detected and flagged my orphaned files
in its own commit message. **Why:** the harness can genuinely run two turns of the "same" agent
concurrently against the same working tree; a clean `git status` at task start doesn't rule this
out if the other instance hasn't committed yet. **How to apply:** if told an earlier instance
stalled, don't assume it's dead — check file mtimes (`ls -la`) and re-check `git log`/`git status`
partway through your own work, not just once at the start. If files change under you mid-task with
a design that already satisfies the card, verify and finish it rather than re-diverging; delete your
own now-orphaned duplicates instead of trying to merge two designs.
