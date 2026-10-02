---
name: gate-script-review-checks
description: Checks for reviewing shell tooling (pnpm gate, dev runners) and cwd-based guard checks — bash 3.2 on macOS, subshell PID kills, cd-before-push bypass
metadata:
  type: feedback
---

2026-09-29 T-23-6 r1 (changes-required):
- The only bash on this machine is /bin/bash 3.2.57: `mapfile`, empty-array expansion under `set -u` fail. Always run the no-args/default path of a new shell script once.
- `( cd x && pnpm dev:all ) & pid=$!` then `kill $pid` orphans pnpm and everything under it. Prove by simulation (scratch package.json with a `bash -c "sleep & wait"` script), not by running the real stack.
- A guard check that resolves the repo from the hook's `cwd` / literal `git -C` is bypassed by `cd <repo> && git push`, `pushd`, subshells, `GIT_DIR=`/`--git-dir`, and `git -C $r` loops. Probe these plus refspecs `<sha>:main`.
- Scratchpad Write is blocked by guard-paths for reviewer; create probe files via Bash heredoc and split "git"+"push" literals.

2026-09-29 T-23-6 r2 (escalate):
- New code that reads push args (refspecs) sees the fd digit of `2>&1` as a word (shlex punctuation split), so a gated push piped through `2>&1 | tail -3` was denied. Always probe legit forms WITH redirects and a valid stamp.
- Paths that don't exist as written (`~/...`, `{}` from xargs/find -exec) resolved to "outside any repo" and were allowed. Probe them with no stamp.
- Run the team suites (`invai-docs/team/hooks/tests`) against the live guard in scratch (`<x>/settings.json` + `<x>/hooks/`) and diff with the mirror; a changed row (B07) needs a judgment.
- Simulate `set -m` process groups with the real lib.sh sourced, including SIGINT/SIGTERM mid-run; check survivors with `lsof -ti` or `ps -axo | awk` (pgrep is blocked).

**Why:** all four were real blocking findings the author's tests missed.
**How to apply:** any review of infra scripts or guard-bash repo/cwd logic. See [[guard-hook-review-checks]].
