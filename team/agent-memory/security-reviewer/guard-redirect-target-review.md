---
name: guard-redirect-target-review
description: How to review guard-bash.py parse changes from a committed snapshot — old-vs-new probe corpus via git archive, the settings.json archive artefact, and the redirect/stdin edge classes still open after T-P8-2.
metadata:
  type: project
---

Review guard-bash.py changes from `git archive <sha> team/hooks` and `<sha>^` into /private/tmp, then pipe one
probe corpus (JSON `{tool_name, tool_input.command, cwd, agent_type}`) into both and diff verdicts; only drift
rows need reading. Three tests (`test_fast_check`, `test_guard_paths`, `test_memory_path`) read `../settings.json`
beside the hooks dir, so copy `.claude/settings.json` to `<extract>/team/settings.json` or they error in both copies.
In zsh, `echo ====` fails (`=cmd` expansion); use `----` as a separator.

**Why:** T-P8-2 (2026-10-01, r3 of T-P7-4) fixed "word after a redirect is a script"; the stdin exception
(`bash < x.sh`, `sh -s < x.sh` read as a run, `-c` excluded) was accepted because dropping it would weaken
`bash < /abs/bad.sh` from deny to allow.

**How to apply:** still-open classes to re-probe on the next guard card (backlog, not regressions): leading
redirect hides the run (`> /dev/null ./bad.sh`, `2>/dev/null ./bad.sh`); fd digit lexed as script (`bash 2>&1 <
x`); r2 notes (`repositories/<id>`, npx writers, `$(...)` producers, realpath in `_tracked`, overwrite-then-run).
See also [[guard-hook-review-probes]].
